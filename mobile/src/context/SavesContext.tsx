import React, { createContext, useCallback, useContext, useState } from 'react';
import { Product } from '../types';

interface SavesContextType {
  savedProducts: Product[];
  isSaved: (productId: string) => boolean;
  toggleSave: (product: Product) => void;
}

const SavesContext = createContext<SavesContextType>({
  savedProducts: [],
  isSaved: () => false,
  toggleSave: () => {},
});

export function SavesProvider({ children }: { children: React.ReactNode }) {
  const [savedProducts, setSavedProducts] = useState<Product[]>([]);

  const isSaved = useCallback(
    (productId: string) => savedProducts.some((p) => p.id === productId),
    [savedProducts],
  );

  const toggleSave = useCallback((product: Product) => {
    setSavedProducts((prev) => {
      const exists = prev.some((p) => p.id === product.id);
      if (exists) {
        return prev.filter((p) => p.id !== product.id);
      }
      return [...prev, product];
    });
  }, []);

  return (
    <SavesContext.Provider value={{ savedProducts, isSaved, toggleSave }}>
      {children}
    </SavesContext.Provider>
  );
}

export function useSaves() {
  return useContext(SavesContext);
}
