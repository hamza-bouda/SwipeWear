import { useCallback, useEffect, useState } from 'react';
import { Product } from '../types';
import { useAuth } from '../context/AuthContext';
import { apiGet, apiPost } from './client';

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
 * Load one product by id, for screens reached without one in hand.
 *
 * ProductDetailScreen used to fall back to a hardcoded MOCK_PRODUCTS list in
 * that case — opening an item from the wardrobe or an alert showed an invented
 * product under a real id, at a price nobody could pay.
 *
 * Skipped entirely when the caller already passed the product, which is the
 * common path from the feed: no request, no spinner.
 */
export function useProduct(productId: string, skip = false) {
  const { token, userId } = useAuth();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(!skip);
  const [error, setError] = useState<string | null>(null);

  const getToken = useCallback(async (): Promise<string> => {
    if (token) return token;
    const resp = await apiPost<{ access_token: string }>('/auth/token', {
      user_id: userId,
    });
    return resp.access_token;
  }, [token, userId]);

  const load = useCallback(async () => {
    if (skip) return;
    setLoading(true);
    setError(null);
    try {
      const authToken = await getToken();
      const data = await apiGet<ApiProduct>(
        `/products/${encodeURIComponent(productId)}`,
        { token: authToken },
      );
      setProduct(mapProduct(data));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Produit indisponible');
      setProduct(null);
    } finally {
      setLoading(false);
    }
  }, [getToken, productId, skip]);

  useEffect(() => { load(); }, [load]);

  return { product, loading, error, reload: load };
}
