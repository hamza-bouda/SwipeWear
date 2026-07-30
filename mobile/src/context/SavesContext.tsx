import React, {
  createContext, useCallback, useContext, useEffect, useState,
} from 'react';
import { Product } from '../types';
import { useAuth } from './AuthContext';
import { apiGet, apiPost } from '../api/client';

interface SavesContextType {
  savedProducts: Product[];
  isSaved: (productId: string) => boolean;
  toggleSave: (product: Product) => void;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

const SavesContext = createContext<SavesContextType>({
  savedProducts: [],
  isSaved: () => false,
  toggleSave: () => {},
  loading: false,
  error: null,
  reload: () => {},
});

interface ApiProduct {
  id: string;
  source: string;
  title: string;
  brand: string | null;
  price: number;
  currency: string;
  condition: string;
  category: string;
  size_raw: string | null;
  image_urls: string[];
  affiliate_url: string | null;
}

function mapProduct(p: ApiProduct): Product {
  return {
    id: p.id,
    title: p.title,
    brand: p.brand ?? '',
    price: p.price,
    currency: p.currency || 'EUR',
    condition: p.condition,
    category: p.category,
    size: p.size_raw,
    imageUrls: p.image_urls,
    source: p.source,
    url: p.affiliate_url ?? undefined,
  };
}

/**
 * The wardrobe.
 *
 * This was a bare useState, so "Mon dressing" emptied on every app restart and
 * the heart toggle never reached the server — even though each save was
 * already being recorded as an event elsewhere in the app, where nothing ever
 * read it back. It now loads from GET /saves and records both directions.
 */
export function SavesProvider({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  const [savedProducts, setSavedProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getToken = useCallback(async (): Promise<string> => {
    // AuthContext always holds a token — an account's, or the browsing
    // identity it obtained at startup. This used to mint one from
    // POST /auth/token, which signed any user_id without a credential.
    if (!token) throw new Error('Session indisponible');
    return token;
  }, [token]);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const authToken = await getToken();
      const data = await apiGet<{ products: ApiProduct[] }>('/saves', {
        token: authToken,
      });
      setSavedProducts(data.products.map(mapProduct));
    } catch (e) {
      // An empty wardrobe and a failed request must not look alike: the user
      // would think their saves were lost.
      setError(e instanceof Error ? e.message : 'Dressing indisponible');
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => { reload(); }, [reload]);

  const isSaved = useCallback(
    (productId: string) => savedProducts.some((p) => p.id === productId),
    [savedProducts],
  );

  const toggleSave = useCallback(async (product: Product) => {
    const wasSaved = savedProducts.some((p) => p.id === product.id);
    // Move the heart first so it responds instantly, then persist; on failure
    // put it back rather than leaving the screen disagreeing with the server.
    setSavedProducts((prev) =>
      wasSaved ? prev.filter((p) => p.id !== product.id) : [product, ...prev],
    );
    try {
      const authToken = await getToken();
      await apiPost(
        '/events',
        {
          product_id: product.id,
          event_type: wasSaved ? 'unsave' : 'save',
          payload: {},
        },
        { token: authToken },
      );
    } catch {
      setSavedProducts((prev) =>
        wasSaved ? [product, ...prev] : prev.filter((p) => p.id !== product.id),
      );
      setError("Le dressing n'a pas pu être mis à jour");
    }
  }, [savedProducts, getToken]);

  return (
    <SavesContext.Provider
      value={{ savedProducts, isSaved, toggleSave, loading, error, reload }}
    >
      {children}
    </SavesContext.Provider>
  );
}

export function useSaves() {
  return useContext(SavesContext);
}
