import { useCallback, useEffect, useState } from 'react';
import { Product } from '../types';
import { useAuth } from '../context/AuthContext';
import { apiGet, apiPost } from './client';

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
    url: p.affiliate_url ?? undefined,
    recommendationReason: item.explanation?.sentence ?? undefined,
  };
}

export function useDrop() {
  const { userId, token } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchToken = useCallback(async (): Promise<string> => {
    if (token) return token;
    const resp = await apiPost<{ access_token: string }>('/auth/token', {
      user_id: userId,
    });
    return resp.access_token;
  }, [token, userId]);

  const loadDrop = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const authToken = await fetchToken();
      const data = await apiGet<ApiFeedResponse>('/drop', {
        token: authToken,
      });
      setProducts(data.items.map(mapApiProduct));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Drop indisponible');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [fetchToken]);

  useEffect(() => {
    loadDrop();
  }, [loadDrop]);

  return { products, loading, error, reload: loadDrop };
}
