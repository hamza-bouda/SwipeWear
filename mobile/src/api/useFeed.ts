import { useCallback, useEffect, useState } from 'react';
import { Product } from '../types';
import { useAuth } from '../context/AuthContext';
import { apiGet } from './client';

interface ApiFeedItem {
  product: {
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
  };
  final_score: number;
  rank: number;
  explanation?: {
    editable_tags?: string[];
    sentence?: string;
  };
}

interface ApiFeedResponse {
  items: ApiFeedItem[];
  next_cursor: string | null;
  fallback_used: boolean;
}

function mapApiProduct(item: ApiFeedItem): Product {
  const p = item.product;
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
    // Dropped before, which is why the detail screen had to invent a URL from
    // the product id and always landed on a 404.
    url: p.affiliate_url ?? undefined,
    recommendationReason: item.explanation?.sentence ?? undefined,
  };
}

export function useFeed() {
  const { token } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchToken = useCallback(async (): Promise<string> => {
    // AuthContext always holds a token — an account's, or the browsing
    // identity it obtained at startup. This used to mint one from
    // POST /auth/token, which signed any user_id without a credential.
    if (!token) throw new Error('Session indisponible');
    return token;
  }, [token]);

  const loadFeed = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const authToken = await fetchToken();
      const data = await apiGet<ApiFeedResponse>('/feed', {
        token: authToken,
        params: { n_results: '30' },
      });
      // No mock substitution. Falling back to fabricated products made a
      // failed request indistinguishable from a working feed: the user browses
      // items that do not exist, cannot buy any of them, and nothing reports a
      // problem. An empty deck and a visible error are the honest answers.
      setProducts(data.items.map(mapApiProduct));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Feed indisponible');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [fetchToken]);

  useEffect(() => {
    loadFeed();
  }, [loadFeed]);

  return { products, loading, error, reload: loadFeed };
}
