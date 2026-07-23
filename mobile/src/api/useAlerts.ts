import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiGet, apiPost, apiPatch, apiDelete } from './client';

export interface AlertConstraints {
  max_price?: number | null;
  size?: string[] | null;
  sources?: string[] | null;
}

export interface AlertItem {
  alert_id: string;
  alert_type: 'style' | 'specific_item';
  label: string;
  status: 'active' | 'paused';
  constraints: AlertConstraints;
  reference_product_id?: string | null;
}

interface AlertsListResponse {
  alerts: AlertItem[];
  active_count: number;
  free_limit: number;
  missed_deals_count: number;
}

interface CreateAlertPayload {
  alert_type: 'style' | 'specific_item';
  label: string;
  constraints?: AlertConstraints;
  reference_product_id?: string;
}

export function useAlerts() {
  const { userId, token } = useAuth();
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [missedDeals, setMissedDeals] = useState(0);
  const [freeLimit, setFreeLimit] = useState(3);
  const [loading, setLoading] = useState(true);

  const getToken = useCallback(async (): Promise<string> => {
    if (token) return token;
    const resp = await apiPost<{ access_token: string }>('/auth/token', { user_id: userId });
    return resp.access_token;
  }, [token, userId]);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const t = await getToken();
      const data = await apiGet<AlertsListResponse>('/alerts', { token: t });
      setAlerts(data.alerts);
      setMissedDeals(data.missed_deals_count);
      setFreeLimit(data.free_limit);
    } catch {
      // silent — keep current state
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => { reload(); }, [reload]);

  const create = useCallback(async (payload: CreateAlertPayload) => {
    const t = await getToken();
    const created = await apiPost<AlertItem>('/alerts', payload, { token: t });
    setAlerts(prev => [...prev, created]);
    return created;
  }, [getToken]);

  const remove = useCallback(async (alertId: string) => {
    const t = await getToken();
    await apiDelete(`/alerts/${alertId}`, { token: t });
    setAlerts(prev => prev.filter(a => a.alert_id !== alertId));
  }, [getToken]);

  const toggle = useCallback(async (alertId: string, currentStatus: 'active' | 'paused') => {
    const newStatus = currentStatus === 'active' ? 'paused' : 'active';
    const t = await getToken();
    await apiPatch(`/alerts/${alertId}/status`, { status: newStatus }, { token: t });
    setAlerts(prev => prev.map(a => a.alert_id === alertId ? { ...a, status: newStatus } : a));
  }, [getToken]);

  return { alerts, missedDeals, freeLimit, loading, reload, create, remove, toggle };
}
