import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as authApi from '../api/auth';
import { setAnalyticsSession } from '../analytics';

const SESSION_KEY = '@swipewear/session';
const ANONYMOUS_SESSION_KEY = '@swipewear/anonymous-session';

interface AuthState {
  userId: string;
  token: string | null;
  email: string | null;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  /** False until storage has been read, so we never sign a returning user out. */
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  retryAnonymousSession: () => Promise<string>;
  logout: () => Promise<void>;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    userId: '',
    token: null,
    email: null,
    isAuthenticated: false,
  });
  const [anonymousSession, setAnonymousSession] = useState<authApi.AnonymousSession | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setAnalyticsSession(state.userId || 'anonymous', state.token);
  }, [state.userId, state.token]);

  const restoreOrCreateAnonymousSession = useCallback(async () => {
    const stored = await AsyncStorage.getItem(ANONYMOUS_SESSION_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as authApi.AnonymousSession;
        if (parsed.user_id && parsed.access_token) return parsed;
      } catch {
        // A corrupted cache is replaced by a new server-issued identity.
      }
    }
    const created = await authApi.createAnonymousSession();
    await AsyncStorage.setItem(ANONYMOUS_SESSION_KEY, JSON.stringify(created));
    return created;
  }, []);

  useEffect(() => {
    // Everything was previously held in useState alone, so closing the app
    // minted a brand new user id: the profile, the swipes, the saved items and
    // the alerts were all orphaned on every launch.
    (async () => {
      try {
        const [storedSession, anonymous] = await Promise.all([
          AsyncStorage.getItem(SESSION_KEY),
          restoreOrCreateAnonymousSession(),
        ]);
        setAnonymousSession(anonymous);

        if (storedSession) {
          const session = JSON.parse(storedSession) as AuthState;
          if (session.userId && session.token) {
            setState({ ...session, isAuthenticated: true });
            return;
          }
        }
        setState({
          userId: anonymous.user_id,
          token: anonymous.access_token,
          email: null,
          isAuthenticated: false,
        });
      } catch {
        // Do not manufacture an identity locally: a network failure is safer
        // than reintroducing the client-controlled token vulnerability.
        setState({ userId: '', token: null, email: null, isAuthenticated: false });
      } finally {
        setReady(true);
      }
    })();
  }, [restoreOrCreateAnonymousSession]);

  const persist = useCallback(async (user: authApi.AuthUser) => {
    const next: AuthState = {
      userId: user.user_id,
      token: user.access_token,
      email: user.email,
      isAuthenticated: true,
    };
    setState(next);
    await AsyncStorage.setItem(SESSION_KEY, JSON.stringify(next));
  }, []);

  const retryAnonymousSession = useCallback(async (): Promise<string> => {
    // A web preview may load before its local API has started. Retrying here
    // lets onboarding recover without asking the user to restart the app.
    await AsyncStorage.removeItem(ANONYMOUS_SESSION_KEY);
    const fresh = await restoreOrCreateAnonymousSession();
    await AsyncStorage.setItem(ANONYMOUS_SESSION_KEY, JSON.stringify(fresh));
    setAnonymousSession(fresh);
    setState((current) => current.isAuthenticated ? current : {
      userId: fresh.user_id,
      token: fresh.access_token,
      email: null,
      isAuthenticated: false,
    });
    return fresh.access_token;
  }, [restoreOrCreateAnonymousSession]);

  const login = useCallback(async (email: string, password: string) => {
    const user = await authApi.login(email, password);
    await persist(user);
  }, [persist]);

  const loginWithGoogle = useCallback(async (idToken: string) => {
    const user = await authApi.loginWithGoogle(idToken);
    await persist(user);
  }, [persist]);

  const register = useCallback(async (email: string, password: string) => {
    const user = await authApi.register(email, password, anonymousSession?.access_token);
    await persist(user);
  }, [persist, anonymousSession]);

  const logout = useCallback(async () => {
    await AsyncStorage.removeItem(SESSION_KEY);
    if (!anonymousSession) throw new Error('Session anonyme indisponible');
    setState({
      userId: anonymousSession.user_id,
      token: anonymousSession.access_token,
      email: null,
      isAuthenticated: false,
    });
  }, [anonymousSession]);

  const deleteAccount = useCallback(async () => {
    if (state.token) {
      // Deleting server-side first: clearing local state on its own left the
      // account, the profile and the event log intact on the server, which the
      // screen still called "supprimer définitivement".
      await authApi.deleteAccount(state.token);
    }
    await AsyncStorage.removeItem(SESSION_KEY);
    const fresh = await authApi.createAnonymousSession();
    await AsyncStorage.setItem(ANONYMOUS_SESSION_KEY, JSON.stringify(fresh));
    setAnonymousSession(fresh);
    setState({
      userId: fresh.user_id,
      token: fresh.access_token,
      email: null,
      isAuthenticated: false,
    });
  }, [state.token]);

  return (
    <AuthContext.Provider
      value={{ ...state, ready, login, loginWithGoogle, register, retryAnonymousSession, logout, deleteAccount }}
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
