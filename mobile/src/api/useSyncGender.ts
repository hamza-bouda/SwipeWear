import { useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiPatch, apiPost } from './client';
import type { Gender } from '../context/PreferencesContext';

/**
 * Push the chosen gender to the server profile.
 *
 * Picking a gender only wrote to AsyncStorage, and the value reached the
 * backend solely as a field of the styles onboarding payload. Anyone who
 * tapped "Passer", or changed the setting later, kept a profile with
 * `gender = null` — and the retrieval filter, having nothing to filter on,
 * served a mixed men's and women's feed.
 *
 * PATCH /profile merges, so sending this one field leaves sizes and budget
 * untouched.
 *
 * KAN-89
 */
export function useSyncGender() {
  const { token, userId } = useAuth();

  return useCallback(
    async (gender: Gender): Promise<void> => {
      let authToken = token;
      if (!authToken) {
        const resp = await apiPost<{ access_token: string }>('/auth/token', {
          user_id: userId,
        });
        authToken = resp.access_token;
      }
      await apiPatch('/profile', { hard_constraints: { gender } }, { token: authToken });
    },
    [token, userId],
  );
}
