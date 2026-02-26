import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

export type PreferenceKind = 'liked_brand' | 'excluded_brand' | 'color' | 'style' | 'budget' | 'size';
export type PreferenceSource = 'learned' | 'manual';

export interface AlgorithmPreference {
  id: string;
  kind: PreferenceKind;
  label: string;
  source: PreferenceSource;
  locked: boolean;
}

interface AlgorithmContextValue {
  preferences: AlgorithmPreference[];
  revision: number;
  addPreference: (kind: PreferenceKind, label: string) => void;
  removePreference: (id: string) => void;
  toggleLock: (id: string) => void;
}

const initialPreferences: AlgorithmPreference[] = [
  { id: 'brand-carhartt', kind: 'liked_brand', label: 'Carhartt WIP', source: 'learned', locked: false },
  { id: 'brand-nike', kind: 'liked_brand', label: 'Nike', source: 'manual', locked: true },
  { id: 'exclude-the-north-face', kind: 'excluded_brand', label: 'The North Face', source: 'manual', locked: true },
  { id: 'color-black', kind: 'color', label: 'Noir', source: 'learned', locked: false },
  { id: 'style-streetwear', kind: 'style', label: 'Streetwear', source: 'learned', locked: false },
  { id: 'budget-80', kind: 'budget', label: 'Moins de 80 €', source: 'manual', locked: true },
  { id: 'size-m', kind: 'size', label: 'M', source: 'manual', locked: true },
];

const AlgorithmContext = createContext<AlgorithmContextValue | null>(null);

export function AlgorithmProvider({ children }: { children: React.ReactNode }) {
  const [preferences, setPreferences] = useState<AlgorithmPreference[]>(initialPreferences);
  const [revision, setRevision] = useState(0);

  const addPreference = useCallback((kind: PreferenceKind, label: string) => {
    const normalized = label.trim();
    if (!normalized) return;
    setRevision((value) => value + 1);
    setPreferences((current) => {
      if (current.some((item) => item.kind === kind && item.label.toLowerCase() === normalized.toLowerCase())) {
        return current;
      }
      return [...current, { id: `${kind}-${normalized.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`, kind, label: normalized, source: 'manual', locked: false }];
    });
  }, []);

  const removePreference = useCallback((id: string) => {
    setRevision((value) => value + 1);
    setPreferences((current) => {
      const next = current.filter((item) => item.id !== id);
      return next;
    });
  }, []);

  const toggleLock = useCallback((id: string) => {
    setPreferences((current) => current.map((item) => (
      item.id === id ? { ...item, locked: !item.locked } : item
    )));
  }, []);

  const value = useMemo(() => ({ preferences, revision, addPreference, removePreference, toggleLock }), [preferences, revision, addPreference, removePreference, toggleLock]);
  return <AlgorithmContext.Provider value={value}>{children}</AlgorithmContext.Provider>;
}

export function useAlgorithm() {
  const context = useContext(AlgorithmContext);
  if (!context) throw new Error('useAlgorithm must be used within AlgorithmProvider');
  return context;
}
