import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type Gender = 'men' | 'women' | 'unisex';
export type Language = 'fr' | 'en';

const GENDER_KEY = '@swipewear/gender';
const LANGUAGE_KEY = '@swipewear/language';
const ONBOARDING_KEY = '@swipewear/onboarding-completed';

interface PreferencesValue {
  gender: Gender | null;
  language: Language;
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
  completeOnboarding: () => Promise<void>;
}

const PreferencesContext = createContext<PreferencesValue | undefined>(undefined);

export function PreferencesProvider({ children }: { children: React.ReactNode }) {
  const [gender, setGenderState] = useState<Gender | null>(null);
  const [language, setLanguageState] = useState<Language>('fr');
  const [onboardingCompleted, setOnboardingCompleted] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Read once at startup. Until this resolves `ready` stays false, otherwise
    // a returning user is shown the gender question again for a frame.
    (async () => {
      try {
        const [storedGender, storedLanguage, storedOnboarding] = await Promise.all([
          AsyncStorage.getItem(GENDER_KEY),
          AsyncStorage.getItem(LANGUAGE_KEY),
          AsyncStorage.getItem(ONBOARDING_KEY),
        ]);
        if (storedGender === 'men' || storedGender === 'women' || storedGender === 'unisex') {
          setGenderState(storedGender);
        }
        if (storedLanguage === 'fr' || storedLanguage === 'en') {
          setLanguageState(storedLanguage);
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

  const completeOnboarding = useCallback(async () => {
    setOnboardingCompleted(true);
    await AsyncStorage.setItem(ONBOARDING_KEY, 'true');
  }, []);

  return (
    <PreferencesContext.Provider
      value={{
        gender, language, onboardingCompleted, ready,
        setGender, setLanguage, completeOnboarding,
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
