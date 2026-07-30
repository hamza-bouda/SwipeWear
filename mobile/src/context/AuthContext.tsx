import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Google from 'expo-auth-session/providers/google';
import {
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
  onIdTokenChanged,
  signInWithCredential,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut as firebaseSignOut,
  type User,
} from 'firebase/auth';
import { auth, googleWebClientId, isFirebaseConfigured, requireAuth } from '../lib/firebase';
import * as accountApi from '../api/auth';

/**
 * Identity for the whole app.
 *
 * Two kinds of identity exist, and every request carries one of them:
 *
 *  - a *browsing* identity, minted by the server for a visitor with no
 *    account, so the feed can be personalised before signing up;
 *  - an *account*, owned by Firebase, which also owns the passwords, the
 *    Google handshake and phone verification.
 *
 * Seven call sites used to each re-implement "if I have no token, ask
 * /auth/token for one for this user_id". That endpoint signed any id handed to
 * it without a credential, so it is gone; this provider is now the single
 * place a token comes from, and it always has one.
 *
 * KAN-91
 */

/** Persisted whole: the server no longer re-issues a token for a known id. */
const ANONYMOUS_SESSION_KEY = '@swipewear/anonymous-session';

interface AuthState {
  userId: string | null;
  token: string | null;
  email: string | null;
  phoneNumber: string | null;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  /** False until storage and Firebase have been read. */
  ready: boolean;
  /** False when the project is unconfigured — screens say so instead of failing. */
  canSignIn: boolean;
  /** False until the Google provider is switched on in the Firebase console. */
  canUseGoogle: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Isolates the Google OAuth hook so it is only ever mounted with a real client
 * id.
 *
 * `Google.useAuthRequest` throws during render when the id is missing
 * ("Client Id property must be defined to use Google auth on this platform").
 * Called unconditionally from the provider, that exception took down
 * AuthProvider and left the whole app on a blank screen — not just the Google
 * button. Hooks cannot be called conditionally, so the conditional part is the
 * component itself.
 */
function GoogleAuthBridge({
  onIdToken,
  registerPrompt,
}: {
  onIdToken: (idToken: string) => void;
  registerPrompt: (prompt: (() => Promise<unknown>) | null) => void;
}) {
  const [, response, promptAsync] = Google.useAuthRequest({
    clientId: googleWebClientId,
    webClientId: googleWebClientId,
  });

  useEffect(() => {
    registerPrompt(promptAsync);
    return () => registerPrompt(null);
  }, [promptAsync, registerPrompt]);

  useEffect(() => {
    // The browser flow resolves asynchronously, outside the call that started it.
    if (response?.type === 'success' && response.params?.id_token) {
      onIdToken(response.params.id_token);
    }
  }, [response, onIdToken]);

  return null;
}

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
    userId: null, token: null, email: null, phoneNumber: null, isAuthenticated: false,
  });
  const [ready, setReady] = useState(false);
  const anonymousRef = useRef<accountApi.AnonymousSession | null>(null);
  // Which account we have already provisioned server-side, so an hourly token
  // refresh does not re-post /auth/sync every time.
  const syncedUserRef = useRef<string | null>(null);

  // Set by GoogleAuthBridge, which only mounts when a client id exists.
  const googlePromptRef = useRef<(() => Promise<unknown>) | null>(null);

  const applyAnonymous = useCallback(async () => {
    try {
      const session = await loadAnonymousSession();
      anonymousRef.current = session;
      setState({
        userId: session.user_id,
        token: session.access_token,
        email: null,
        phoneNumber: null,
        isAuthenticated: false,
      });
    } catch {
      // The API is unreachable. Staying token-less is the honest state: the
      // screens already show their own errors rather than inventing data.
      setState({
        userId: null, token: null, email: null,
        phoneNumber: null, isAuthenticated: false,
      });
    }
  }, []);

  const applyUser = useCallback(async (user: User) => {
    const token = await user.getIdToken();
    setState({
      userId: user.uid,
      token,
      email: user.email,
      phoneNumber: user.phoneNumber,
      isAuthenticated: true,
    });

    if (syncedUserRef.current === user.uid) return;
    syncedUserRef.current = user.uid;
    try {
      // Provisions the local row and carries over whatever was built while
      // browsing without an account.
      await accountApi.syncAccount(token, anonymousRef.current?.user_id ?? null);
      // The anonymous profile now belongs to the account; keeping the old
      // token would let the same person come back as two different people.
      await AsyncStorage.removeItem(ANONYMOUS_SESSION_KEY);
      anonymousRef.current = null;
    } catch {
      // Retried on the next launch: syncedUserRef is per-process.
      syncedUserRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!auth) {
      applyAnonymous().finally(() => setReady(true));
      return;
    }
    // onIdTokenChanged rather than onAuthStateChanged: it also fires when
    // Firebase silently refreshes the token every hour, so the token held here
    // never goes stale and requests do not start failing after an hour.
    const unsubscribe = onIdTokenChanged(auth, (user) => {
      const run = user
        ? applyUser(user)
        : (() => { syncedUserRef.current = null; return applyAnonymous(); })();
      run.finally(() => setReady(true));
    });
    return unsubscribe;
  }, [applyAnonymous, applyUser]);

  const handleGoogleIdToken = useCallback((idToken: string) => {
    signInWithCredential(requireAuth(), GoogleAuthProvider.credential(idToken))
      .catch(() => {
        // onIdTokenChanged stays on the anonymous identity; the screen that
        // started the flow shows the error.
      });
  }, []);

  const registerGooglePrompt = useCallback(
    (prompt: (() => Promise<unknown>) | null) => {
      googlePromptRef.current = prompt;
    },
    [],
  );

  const signIn = useCallback(async (email: string, password: string) => {
    await signInWithEmailAndPassword(requireAuth(), email, password);
  }, []);

  const signUp = useCallback(async (email: string, password: string) => {
    await createUserWithEmailAndPassword(requireAuth(), email, password);
  }, []);

  const signInWithGoogle = useCallback(async () => {
    if (Platform.OS === 'web') {
      // Firebase redirects through its own handler at
      // <project>.firebaseapp.com/__/auth/handler, which is the only address
      // the OAuth client Firebase created authorises. Going through
      // expo-auth-session here sends http://localhost:8081 instead, and
      // Google answers `redirect_uri_mismatch`.
      await signInWithPopup(requireAuth(), new GoogleAuthProvider());
      return;
    }
    // On native there is no popup: the OAuth browser flow is the only way, and
    // it resolves through GoogleAuthBridge.
    const prompt = googlePromptRef.current;
    if (!googleWebClientId || !prompt) {
      throw new Error('provider is not enabled');
    }
    await prompt();
  }, []);

  const signOut = useCallback(async () => {
    if (auth) await firebaseSignOut(auth);
    syncedUserRef.current = null;
    await applyAnonymous();
  }, [applyAnonymous]);

  const deleteAccount = useCallback(async () => {
    if (!state.token || !state.isAuthenticated) return;
    // Server-side first: it erases the identity at Firebase too. Clearing the
    // local session alone would leave the account intact and let the same
    // person sign straight back in.
    await accountApi.deleteAccount(state.token);
    if (auth) await firebaseSignOut(auth);
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
        canSignIn: isFirebaseConfigured,
        // On web, signInWithPopup goes through Firebase's own handler and
        // needs no client id of ours; on native the OAuth flow does.
        canUseGoogle: Platform.OS === 'web'
          ? isFirebaseConfigured
          : Boolean(googleWebClientId),
        signIn,
        signUp,
        signInWithGoogle,
        signOut,
        deleteAccount,
      }}
    >
      {googleWebClientId ? (
        <GoogleAuthBridge
          onIdToken={handleGoogleIdToken}
          registerPrompt={registerGooglePrompt}
        />
      ) : null}
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
