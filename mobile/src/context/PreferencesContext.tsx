import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type Gender = 'men' | 'women' | 'unisex';
export type Language = 'fr' | 'en';

const GENDER_KEY = '@swipewear/gender';
const LANGUAGE_KEY = '@swipewear/language';
const ONBOARDING_KEY = '@swipewear/onboarding-completed';
const SIZES_KEY = '@swipewear/sizes';
const NOTIF_FREQ_KEY = '@swipewear/notification-frequency';

export type NotificationFrequency = 'instant' | 'daily_digest' | 'disabled';

interface PreferencesValue {
  gender: Gender | null;
  language: Language;
  sizes: string[];
  notificationFrequency: NotificationFrequency;
  /**
   * True once the user has reached the feed at least once. Without it the
   * navigator has no way to tell a returning user from a new install, and
   * sent everyone back through onboarding on every launch.
   */
  onboardingCompleted: boolean;
  /** False until storage has been read, so we do not flash the wrong screen. */
  ready: boolean;
  setGender: (gender: Gender) => Promise<void>;
  setLanguage: (language: Language) => Promise<void>;
  setSizes: (sizes: string[]) => Promise<void>;
  setNotificationFrequency: (freq: NotificationFrequency) => Promise<void>;
  completeOnboarding: () => Promise<void>;
}

const PreferencesContext = createContext<PreferencesValue | undefined>(undefined);

export function PreferencesProvider({ children }: { children: React.ReactNode }) {
  const [gender, setGenderState] = useState<Gender | null>(null);
  const [language, setLanguageState] = useState<Language>('fr');
  const [sizes, setSizesState] = useState<string[]>([]);
  const [notificationFrequency, setNotifFreqState] = useState<NotificationFrequency>('instant');
  const [onboardingCompleted, setOnboardingCompleted] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Read once at startup. Until this resolves `ready` stays false, otherwise
    // a returning user is shown the gender question again for a frame.
    (async () => {
      try {
        const [storedGender, storedLanguage, storedOnboarding, storedSizes, storedNotifFreq] = await Promise.all([
          AsyncStorage.getItem(GENDER_KEY),
          AsyncStorage.getItem(LANGUAGE_KEY),
          AsyncStorage.getItem(ONBOARDING_KEY),
          AsyncStorage.getItem(SIZES_KEY),
          AsyncStorage.getItem(NOTIF_FREQ_KEY),
        ]);
        if (storedGender === 'men' || storedGender === 'women' || storedGender === 'unisex') {
          setGenderState(storedGender);
        }
        if (storedLanguage === 'fr' || storedLanguage === 'en') {
          setLanguageState(storedLanguage);
        }
        if (storedSizes) {
          try { setSizesState(JSON.parse(storedSizes)); } catch { /* corrupted */ }
        }
        if (storedNotifFreq === 'instant' || storedNotifFreq === 'daily_digest' || storedNotifFreq === 'disabled') {
          setNotifFreqState(storedNotifFreq);
        }
        setOnboardingCompleted(storedOnboarding === 'true');
      } finally {
        setReady(true);
      }
    })();
  }, []);

  const setGender = useCallback(async (next: Gender) => {
    setGenderState(next);
    await AsyncStorage.setItem(GENDER_KEY, next);
  }, []);

  const setLanguage = useCallback(async (next: Language) => {
    setLanguageState(next);
    await AsyncStorage.setItem(LANGUAGE_KEY, next);
  }, []);

  const setSizes = useCallback(async (next: string[]) => {
    setSizesState(next);
    await AsyncStorage.setItem(SIZES_KEY, JSON.stringify(next));
  }, []);

  const setNotificationFrequency = useCallback(async (next: NotificationFrequency) => {
    setNotifFreqState(next);
    await AsyncStorage.setItem(NOTIF_FREQ_KEY, next);
  }, []);

  const completeOnboarding = useCallback(async () => {
    setOnboardingCompleted(true);
    await AsyncStorage.setItem(ONBOARDING_KEY, 'true');
  }, []);

  return (
    <PreferencesContext.Provider
      value={{
        gender, language, sizes, notificationFrequency, onboardingCompleted, ready,
        setGender, setLanguage, setSizes, setNotificationFrequency, completeOnboarding,
      }}
    >
      {children}
    </PreferencesContext.Provider>
  );
}

export function usePreferences(): PreferencesValue {
  const context = useContext(PreferencesContext);
  if (!context) {
    throw new Error('usePreferences must be used inside a PreferencesProvider');
  }
  return context;
}
