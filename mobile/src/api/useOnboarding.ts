import { useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiPost, apiPostForm } from './client';
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
    async (
      payload: OnboardingPayload,
      imageUris: string[] = [],
      sessionToken?: string,
    ): Promise<void> => {
      const activeToken = sessionToken ?? token;
      if (!activeToken) throw new Error('Session anonyme indisponible');
      await apiPost('/onboarding/styles', payload, { token: activeToken });
      if (imageUris.length === 0) return;

      const form = new FormData();
      imageUris.forEach((uri, index) => {
        form.append('files', {
          uri,
          name: `inspiration-${index}.jpg`,
          type: 'image/jpeg',
        } as unknown as Blob);
      });
      await apiPostForm('/onboarding/images/upload', form, { token: activeToken });
    },
    [token],
  );
}
