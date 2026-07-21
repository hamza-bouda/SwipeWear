import React, { createContext, useCallback, useContext, useState } from 'react';

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
  login: (userId: string, token: string, email: string) => void;
  logout: () => void;
  getAnonymousId: () => string;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function createAnonymousState(): AuthState {
  return {
    userId: generateUUID(),
    token: null,
    email: null,
    isAuthenticated: false,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>(createAnonymousState);

  const login = useCallback((userId: string, token: string, email: string) => {
    setState({ userId, token, email, isAuthenticated: true });
  }, []);

  const logout = useCallback(() => {
    setState(createAnonymousState());
  }, []);

  const getAnonymousId = useCallback(() => {
    return state.userId;
  }, [state.userId]);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, getAnonymousId }}>
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
