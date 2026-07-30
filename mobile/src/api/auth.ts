import { apiDelete, apiPost } from './client';

/**
 * Account endpoints that remain on our side.
 *
 * Registration and sign-in moved to Supabase in KAN-90 — the backend never
 * sees a password. What is left is provisioning the local account behind a
 * Supabase session, handing a browsing identity to visitors, and erasing an
 * account for good.
 */

export interface AnonymousSession {
  user_id: string;
  access_token: string;
}

export interface SyncedAccount {
  user_id: string;
  email: string | null;
  provider: string;
  /** True when the profile built while browsing anonymously was carried over. */
  profile_migrated: boolean;
}

/**
 * Ask the server for a throwaway browsing identity.
 *
 * The id comes from the server. The endpoint this replaced signed whatever
 * user_id the caller sent, with no credential at all — knowing an id was
 * enough to read, change and delete that person's account.
 */
export function startAnonymousSession(): Promise<AnonymousSession> {
  return apiPost<AnonymousSession>('/auth/anonymous', {});
}

/**
 * Provision the local account behind a freshly signed-in Supabase session.
 *
 * `anonymousUserId` carries the swipes and the style profile built before
 * signing up; omitting it throws that work away.
 */
export function syncAccount(
  token: string,
  anonymousUserId?: string | null,
): Promise<SyncedAccount> {
  return apiPost<SyncedAccount>(
    '/auth/sync',
    { anonymous_user_id: anonymousUserId ?? null },
    { token },
  );
}

export function deleteAccount(token: string): Promise<void> {
  return apiDelete('/auth/account', { token });
}
