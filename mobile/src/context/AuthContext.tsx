import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as authApi from '../api/auth';

const SESSION_KEY = '@swipewear/session';
/**
 * The anonymous id is stored separately from the session: it must survive a
 * logout, otherwise signing out and back in would strand the profile built
 * while browsing without an account.
 */
const ANONYMOUS_ID_KEY = '@swipewear/anonymous-id';

function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

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
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // The id is replaced by the persisted one as soon as storage resolves; the
  // generated value only covers a genuinely first launch.
  const [state, setState] = useState<AuthState>(() => ({
    userId: generateUUID(),
    token: null,
    email: null,
    isAuthenticated: false,
  }));
  const [anonymousId, setAnonymousId] = useState<string>(state.userId);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Everything was previously held in useState alone, so closing the app
    // minted a brand new user id: the profile, the swipes, the saved items and
    // the alerts were all orphaned on every launch.
    (async () => {
      try {
        const [storedSession, storedAnonymousId] = await Promise.all([
          AsyncStorage.getItem(SESSION_KEY),
          AsyncStorage.getItem(ANONYMOUS_ID_KEY),
        ]);

        let anonymous = storedAnonymousId;
        if (!anonymous) {
          anonymous = generateUUID();
          await AsyncStorage.setItem(ANONYMOUS_ID_KEY, anonymous);
        }
        setAnonymousId(anonymous);

        if (storedSession) {
          const session = JSON.parse(storedSession) as AuthState;
          if (session.userId && session.token) {
            setState({ ...session, isAuthenticated: true });
            return;
          }
        }
        setState({
          userId: anonymous, token: null, email: null, isAuthenticated: false,
        });
      } catch {
        // A corrupt entry must not brick the app: fall back to anonymous.
        setState((prev) => ({ ...prev, token: null, isAuthenticated: false }));
      } finally {
        setReady(true);
      }
    })();
  }, []);

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

  const login = useCallback(async (email: string, password: string) => {
    const user = await authApi.login(email, password);
    await persist(user);
  }, [persist]);

  const register = useCallback(async (email: string, password: string) => {
    const user = await authApi.register(email, password, anonymousId);
    await persist(user);
  }, [persist, anonymousId]);

  const logout = useCallback(async () => {
    await AsyncStorage.removeItem(SESSION_KEY);
    setState({
      userId: anonymousId, token: null, email: null, isAuthenticated: false,
    });
  }, [anonymousId]);

  const deleteAccount = useCallback(async () => {
    if (state.token) {
      // Deleting server-side first: clearing local state on its own left the
      // account, the profile and the event log intact on the server, which the
      // screen still called "supprimer définitivement".
      await authApi.deleteAccount(state.token);
    }
    await AsyncStorage.removeItem(SESSION_KEY);
    const fresh = generateUUID();
    await AsyncStorage.setItem(ANONYMOUS_ID_KEY, fresh);
    setAnonymousId(fresh);
    setState({ userId: fresh, token: null, email: null, isAuthenticated: false });
  }, [state.token]);

  return (
    <AuthContext.Provider
      value={{ ...state, ready, login, register, logout, deleteAccount }}
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
