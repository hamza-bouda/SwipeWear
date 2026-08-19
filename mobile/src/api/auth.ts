import { apiDelete, apiPost } from './client';

/**
 * Real account endpoints.
 *
 * The login screen used to fabricate a random UUID and the literal string
 * "stub-jwt-token" instead of calling anything. Nothing was stored, the
 * password was discarded, and the backend rejected that token on every
 * authenticated call — so an account could never survive a restart.
 *
 * KAN-89
 */

export interface AuthUser {
  user_id: string;
  email: string;
  access_token: string;
  /** True when the anonymous profile was carried over into the new account. */
  profile_migrated?: boolean;
}

export interface AnonymousSession {
  user_id: string;
  access_token: string;
}

export function createAnonymousSession(): Promise<AnonymousSession> {
  return apiPost<AnonymousSession>('/auth/anonymous', {});
}

export function register(
  email: string,
  password: string,
  anonymousToken?: string | null,
): Promise<AuthUser> {
  return apiPost<AuthUser>('/auth/register', {
    email,
    password,
  }, { token: anonymousToken });
}

export function login(email: string, password: string): Promise<AuthUser> {
  return apiPost<AuthUser>('/auth/login', { email, password });
}

export function deleteAccount(token: string): Promise<void> {
  return apiDelete('/auth/account', { token });
}
