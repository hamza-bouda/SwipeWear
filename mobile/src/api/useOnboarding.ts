import { useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiPost } from './client';
import type { Gender } from '../context/PreferencesContext';

export interface OnboardingPayload {
  style_ids: string[];
  sizes: string[];
  max_price_eur: number | null;
  gender: Gender | null;
}

/**
 * Persist the onboarding answers.
 *
 * ConstraintsScreen used to `await new Promise(r => setTimeout(r, 1500))` and
 * navigate on, so the styles, sizes and budget a new user had just chosen were
 * dropped and their first feed was built from an empty profile.
 */
export function useSubmitOnboarding() {
  const { token, userId } = useAuth();

  return useCallback(
    async (payload: OnboardingPayload): Promise<void> => {
      let authToken = token;
      if (!authToken) {
        const resp = await apiPost<{ access_token: string }>('/auth/token', {
          user_id: userId,
        });
        authToken = resp.access_token;
      }
      await apiPost('/onboarding/styles', payload, { token: authToken });
    },
    [token, userId],
  );
}
