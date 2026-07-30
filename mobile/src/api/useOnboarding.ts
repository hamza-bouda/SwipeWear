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
  const { token } = useAuth();

  return useCallback(
    async (payload: OnboardingPayload): Promise<void> => {
      // AuthContext always holds a token; POST /auth/token, which signed
      // any user_id with no credential, no longer exists.
      if (!token) throw new Error('Session indisponible');
      await apiPost('/onboarding/styles', payload, { token });
    },
    [token],
  );
}
