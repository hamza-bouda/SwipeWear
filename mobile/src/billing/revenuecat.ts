/**
 * Thin wrapper around react-native-purchases (RevenueCat SDK).
 *
 * Falls back to a no-op mock in development / Expo Go (the native SDK
 * requires a custom dev build and cannot run in Expo Go).
 *
 * Configuration:
 *   EXPO_PUBLIC_REVENUECAT_API_KEY_IOS   — RevenueCat iOS app key
 *   EXPO_PUBLIC_REVENUECAT_API_KEY_ANDROID — RevenueCat Android app key
 *
 * KAN-73
 */

import { Platform } from 'react-native';

// RevenueCat product identifier as configured in App Store / Play Store.
export const PREMIUM_OFFERING_ID = 'swipewear_premium_monthly';

export interface PurchaseResult {
  success: boolean;
  isActive: boolean;
  error?: string;
}

export interface SubscriptionInfo {
  isActive: boolean;
  isTrialing: boolean;
  expiresAt: Date | null;
}

// --------------------------------------------------------------------------
// Try to load the native SDK. In Expo Go it will not be available.
// --------------------------------------------------------------------------
let Purchases: any = null;
let nativeAvailable = false;

try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  Purchases = require('react-native-purchases').default;
  nativeAvailable = true;
} catch {
  // Expo Go or native module not linked yet — fall back to mock
}

// --------------------------------------------------------------------------
// Initialisation (call once at app start, after the user is known)
// --------------------------------------------------------------------------
export async function configure(userId: string): Promise<void> {
  if (!nativeAvailable || !Purchases) return;

  const apiKey =
    Platform.OS === 'ios'
      ? process.env.EXPO_PUBLIC_REVENUECAT_API_KEY_IOS ?? ''
      : process.env.EXPO_PUBLIC_REVENUECAT_API_KEY_ANDROID ?? '';

  if (!apiKey) return; // not configured in this env

  await Purchases.configure({ apiKey, appUserID: userId });
}

// --------------------------------------------------------------------------
// Purchase
// --------------------------------------------------------------------------
export async function purchasePremium(): Promise<PurchaseResult> {
  if (!nativeAvailable || !Purchases) {
    // Dev mock: simulate a successful purchase
    return { success: true, isActive: true };
  }

  try {
    const offerings = await Purchases.getOfferings();
    const pkg = offerings.current?.availablePackages?.[0];
    if (!pkg) {
      return { success: false, isActive: false, error: 'Aucun abonnement disponible.' };
    }
    const { customerInfo } = await Purchases.purchasePackage(pkg);
    const isActive = !!customerInfo.entitlements.active[PREMIUM_OFFERING_ID];
    return { success: true, isActive };
  } catch (err: any) {
    if (err.userCancelled) {
      return { success: false, isActive: false };
    }
    return { success: false, isActive: false, error: err.message };
  }
}

// --------------------------------------------------------------------------
// Restore
// --------------------------------------------------------------------------
export async function restorePurchases(): Promise<PurchaseResult> {
  if (!nativeAvailable || !Purchases) {
    return { success: true, isActive: false };
  }

  try {
    const customerInfo = await Purchases.restorePurchases();
    const isActive = !!customerInfo.entitlements.active[PREMIUM_OFFERING_ID];
    return { success: true, isActive };
  } catch (err: any) {
    return { success: false, isActive: false, error: err.message };
  }
}

// --------------------------------------------------------------------------
// Current status (for hook initialisation)
// --------------------------------------------------------------------------
export async function getSubscriptionInfo(): Promise<SubscriptionInfo> {
  if (!nativeAvailable || !Purchases) {
    return { isActive: false, isTrialing: false, expiresAt: null };
  }

  try {
    const customerInfo = await Purchases.getCustomerInfo();
    const entitlement = customerInfo.entitlements.active[PREMIUM_OFFERING_ID];
    if (!entitlement) {
      return { isActive: false, isTrialing: false, expiresAt: null };
    }
    return {
      isActive: true,
      isTrialing: entitlement.periodType === 'trial',
      expiresAt: entitlement.expirationDate ? new Date(entitlement.expirationDate) : null,
    };
  } catch {
    return { isActive: false, isTrialing: false, expiresAt: null };
  }
}
