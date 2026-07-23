/**
 * Hook: premium subscription state + purchase/restore actions.
 *
 * Usage:
 *   const { isPremium, isTrialing, purchase, restore, loading } = usePremium();
 *
 * KAN-73
 */

import { useCallback, useEffect, useState } from 'react';
import {
  PurchaseResult,
  SubscriptionInfo,
  getSubscriptionInfo,
  purchasePremium,
  restorePurchases,
} from './revenuecat';

interface PremiumState extends SubscriptionInfo {
  loading: boolean;
  error: string | null;
}

interface PremiumActions {
  purchase: () => Promise<PurchaseResult>;
  restore: () => Promise<PurchaseResult>;
  refresh: () => Promise<void>;
}

export function usePremium(): PremiumState & PremiumActions {
  const [state, setState] = useState<PremiumState>({
    isActive: false,
    isTrialing: false,
    expiresAt: null,
    loading: true,
    error: null,
  });

  const refresh = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const info = await getSubscriptionInfo();
      setState({ ...info, loading: false, error: null });
    } catch (err: any) {
      setState((s) => ({ ...s, loading: false, error: err.message }));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const purchase = useCallback(async (): Promise<PurchaseResult> => {
    const result = await purchasePremium();
    if (result.success && result.isActive) {
      await refresh();
    }
    return result;
  }, [refresh]);

  const restore = useCallback(async (): Promise<PurchaseResult> => {
    const result = await restorePurchases();
    if (result.success) {
      await refresh();
    }
    return result;
  }, [refresh]);

  return {
    ...state,
    isPremium: state.isActive,
    purchase,
    restore,
    refresh,
  } as PremiumState & PremiumActions & { isPremium: boolean };
}
