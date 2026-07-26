import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiGet, apiPost } from './client';

export interface LadderEntry {
  productId: string;
  title: string;
  price: number;
  currency: string;
  source: string;
  condition: string;
  isNew: boolean;
  confidence: 'exact' | 'similar';
  imageUrl: string | null;
  affiliateUrl: string;
  similarityScore: number;
}

interface ApiLadderEntry {
  product_id: string;
  url: string;
  price_eur: number;
  source: string;
  condition: string;
  is_new: boolean;
  affiliate_url: string | null;
  confidence: 'exact' | 'similar';
  similarity_score: number;
  image_url: string | null;
  title: string | null;
}

interface ApiLadder {
  source_product_id: string;
  entries: ApiLadderEntry[];
  min_price_eur: number | null;
  max_price_eur: number | null;
  savings_pct: number | null;
  latency_ms: number;
}

function mapEntry(e: ApiLadderEntry): LadderEntry {
  return {
    productId: e.product_id,
    title: e.title ?? '',
    price: e.price_eur,
    currency: 'EUR',
    source: e.source,
    condition: e.condition,
    isNew: e.is_new,
    confidence: e.confidence,
    imageUrl: e.image_url,
    affiliateUrl: e.affiliate_url ?? e.url,
    similarityScore: e.similarity_score,
  };
}

/**
 * Every offer found for one item, cheapest first.
 *
 * PriceLadderScreen built this list from MOCK_PRODUCTS: it invented two fake
 * offers around a hardcoded product and showed a saving that was arithmetic on
 * fiction. The real comparison — the point of the whole feature — is what the
 * /ladder endpoint computes from the catalogue.
 */
export function useLadder(productId: string) {
  const { token, userId } = useAuth();
  const [entries, setEntries] = useState<LadderEntry[]>([]);
  const [savingsPct, setSavingsPct] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getToken = useCallback(async (): Promise<string> => {
    if (token) return token;
    const resp = await apiPost<{ access_token: string }>('/auth/token', {
      user_id: userId,
    });
    return resp.access_token;
  }, [token, userId]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const authToken = await getToken();
      const data = await apiGet<ApiLadder>(
        `/ladder/${encodeURIComponent(productId)}`,
        { token: authToken },
      );
      setEntries(data.entries.map(mapEntry));
      setSavingsPct(data.savings_pct);
    } catch (e) {
      // "No comparable offer" and "the request failed" mean different things
      // to someone deciding whether to buy, so they must not look alike.
      setError(e instanceof Error ? e.message : 'Comparaison indisponible');
      setEntries([]);
      setSavingsPct(null);
    } finally {
      setLoading(false);
    }
  }, [getToken, productId]);

  useEffect(() => { load(); }, [load]);

  return { entries, savingsPct, loading, error, reload: load };
}
