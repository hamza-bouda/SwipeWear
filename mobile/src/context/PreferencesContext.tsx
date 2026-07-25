import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type Gender = 'men' | 'women' | 'unisex';
export type Language = 'fr' | 'en';

const GENDER_KEY = '@swipewear/gender';
const LANGUAGE_KEY = '@swipewear/language';

interface PreferencesValue {
  gender: Gender | null;
  language: Language;
  /** False until storage has been read, so we do not flash the wrong screen. */
  ready: boolean;
  setGender: (gender: Gender) => Promise<void>;
  setLanguage: (language: Language) => Promise<void>;
}

const PreferencesContext = createContext<PreferencesValue | undefined>(undefined);

export function PreferencesProvider({ children }: { children: React.ReactNode }) {
  const [gender, setGenderState] = useState<Gender | null>(null);
  const [language, setLanguageState] = useState<Language>('fr');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Read once at startup. Until this resolves `ready` stays false, otherwise
    // a returning user is shown the gender question again for a frame.
    (async () => {
      try {
        const [storedGender, storedLanguage] = await Promise.all([
          AsyncStorage.getItem(GENDER_KEY),
          AsyncStorage.getItem(LANGUAGE_KEY),
        ]);
        if (storedGender === 'men' || storedGender === 'women' || storedGender === 'unisex') {
          setGenderState(storedGender);
        }
        if (storedLanguage === 'fr' || storedLanguage === 'en') {
          setLanguageState(storedLanguage);
        }
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

  return (
    <PreferencesContext.Provider
      value={{ gender, language, ready, setGender, setLanguage }}
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
