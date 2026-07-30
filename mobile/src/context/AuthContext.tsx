import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as WebBrowser from 'expo-web-browser';
import { makeRedirectUri } from 'expo-auth-session';
import type { Session } from '@supabase/supabase-js';
import { isSupabaseConfigured, requireSupabase, supabase } from '../lib/supabase';
import * as accountApi from '../api/auth';

/**
 * Identity for the whole app.
 *
 * Two kinds of identity exist, and every request carries one of them:
 *
 *  - a *browsing* identity, minted by the server for a visitor with no
 *    account, so the feed can be personalised before signing up;
 *  - an *account*, owned by Supabase, which also owns the passwords and the
 *    Google and Apple handshakes.
 *
 * Seven call sites used to each re-implement "if I have no token, ask
 * /auth/token for one for this user_id". That endpoint signed any id handed to
 * it without a credential, so it is gone; this provider is now the single
 * place a token comes from, and it always has one.
 *
 * KAN-90
 */

/** Persisted whole: the server no longer re-issues a token for a known id. */
const ANONYMOUS_SESSION_KEY = '@swipewear/anonymous-session';

export type OAuthProvider = 'google' | 'apple';

interface AuthState {
  userId: string | null;
  token: string | null;
  email: string | null;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  /** False until storage and Supabase have been read. */
  ready: boolean;
  /** False when the project is unconfigured — screens say so instead of failing. */
  canSignIn: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  /**
   * Resolves to true when Supabase created no session because it is waiting
   * for the address to be confirmed. Treating that as a success would send the
   * user to a feed they are not signed in to.
   */
  signUp: (email: string, password: string) => Promise<boolean>;
  signInWithProvider: (provider: OAuthProvider) => Promise<void>;
  signOut: () => Promise<void>;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function loadAnonymousSession(): Promise<accountApi.AnonymousSession> {
  const stored = await AsyncStorage.getItem(ANONYMOUS_SESSION_KEY);
  if (stored) {
    try {
      const parsed = JSON.parse(stored) as accountApi.AnonymousSession;
      if (parsed.user_id && parsed.access_token) return parsed;
    } catch {
      // Corrupt entry: fall through and ask for a fresh one.
    }
  }
  const created = await accountApi.startAnonymousSession();
  await AsyncStorage.setItem(ANONYMOUS_SESSION_KEY, JSON.stringify(created));
  return created;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    userId: null, token: null, email: null, isAuthenticated: false,
  });
  const [ready, setReady] = useState(false);
  const anonymousRef = useRef<accountApi.AnonymousSession | null>(null);
  // Which account we have already provisioned server-side, so a token refresh
  // does not re-post /auth/sync every hour.
  const syncedUserRef = useRef<string | null>(null);

  const applyAnonymous = useCallback(async () => {
    try {
      const session = await loadAnonymousSession();
      anonymousRef.current = session;
      setState({
        userId: session.user_id,
        token: session.access_token,
        email: null,
        isAuthenticated: false,
      });
    } catch {
      // The API is unreachable. Staying token-less is the honest state: the
      // screens already show their own errors rather than inventing data.
      setState({ userId: null, token: null, email: null, isAuthenticated: false });
    }
  }, []);

  const applySession = useCallback(async (session: Session) => {
    setState({
      userId: session.user.id,
      token: session.access_token,
      email: session.user.email ?? null,
      isAuthenticated: true,
    });

    if (syncedUserRef.current === session.user.id) return;
    syncedUserRef.current = session.user.id;
    try {
      // Provisions the local row and carries over whatever was built while
      // browsing without an account.
      await accountApi.syncAccount(
        session.access_token, anonymousRef.current?.user_id ?? null,
      );
      // The anonymous profile now belongs to the account; keeping the old
      // token would let the same person come back as two different people.
      await AsyncStorage.removeItem(ANONYMOUS_SESSION_KEY);
      anonymousRef.current = null;
    } catch {
      // Sync is retried on the next launch: syncedUserRef is per-process.
      syncedUserRef.current = null;
    }
  }, []);

  useEffect(() => {
    let active = true;

    (async () => {
      if (!supabase) {
        await applyAnonymous();
        if (active) setReady(true);
        return;
      }

      const { data } = await supabase.auth.getSession();
      if (!active) return;
      if (data.session) {
        await applySession(data.session);
      } else {
        await applyAnonymous();
      }
      if (active) setReady(true);
    })();

    const subscription = supabase?.auth.onAuthStateChange((_event, session) => {
      if (!active) return;
      if (session) {
        applySession(session);
      } else {
        syncedUserRef.current = null;
        applyAnonymous();
      }
    });

    return () => {
      active = false;
      subscription?.data.subscription.unsubscribe();
    };
  }, [applyAnonymous, applySession]);

  const signIn = useCallback(async (email: string, password: string) => {
    const { error } = await requireSupabase().auth.signInWithPassword({
      email, password,
    });
    if (error) throw error;
  }, []);

  const signUp = useCallback(async (email: string, password: string) => {
    const { data, error } = await requireSupabase().auth.signUp({ email, password });
    if (error) throw error;
    return data.session === null;
  }, []);

  const signInWithProvider = useCallback(async (provider: OAuthProvider) => {
    const client = requireSupabase();
    const redirectTo = makeRedirectUri({ scheme: 'swipewear', path: 'auth' });

    const { data, error } = await client.auth.signInWithOAuth({
      provider,
      options: { redirectTo, skipBrowserRedirect: Platform.OS !== 'web' },
    });
    if (error) throw error;
    // On the web the browser has already navigated away; the session is read
    // back from the URL when the page reloads.
    if (Platform.OS === 'web' || !data?.url) return;

    const result = await WebBrowser.openAuthSessionAsync(data.url, redirectTo);
    if (result.type !== 'success') {
      // Closing the sheet is a choice, not a failure worth an error dialog.
      return;
    }
    const code = new URL(result.url).searchParams.get('code');
    if (!code) throw new Error("La réponse du fournisseur d'identité est incomplète.");
    const exchange = await client.auth.exchangeCodeForSession(code);
    if (exchange.error) throw exchange.error;
  }, []);

  const signOut = useCallback(async () => {
    if (supabase) await supabase.auth.signOut();
    syncedUserRef.current = null;
    await applyAnonymous();
  }, [applyAnonymous]);

  const deleteAccount = useCallback(async () => {
    if (!state.token || !state.isAuthenticated) return;
    // Server-side first: it erases the identity at Supabase too. Clearing the
    // local session alone would leave the account intact and let the same
    // person sign straight back in.
    await accountApi.deleteAccount(state.token);
    if (supabase) await supabase.auth.signOut();
    syncedUserRef.current = null;
    await AsyncStorage.removeItem(ANONYMOUS_SESSION_KEY);
    anonymousRef.current = null;
    await applyAnonymous();
  }, [state.token, state.isAuthenticated, applyAnonymous]);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        ready,
        canSignIn: isSupabaseConfigured,
        signIn,
        signUp,
        signInWithProvider,
        signOut,
        deleteAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
