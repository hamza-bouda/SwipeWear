import { Platform } from 'react-native';
import { apiPost } from '../api/client';
import type { AnalyticsEvent } from './events';

const APP_VERSION = '1.0.0';

interface CommonProperties {
  user_id: string;
  app_version: string;
  platform: string;
  timestamp: string;
}

let _userId = 'anonymous';
let _token: string | null = null;

export function setAnalyticsSession(userId: string, token: string | null) {
  _userId = userId;
  _token = token;
}

function getCommonProperties(): CommonProperties {
  return {
    user_id: _userId,
    app_version: APP_VERSION,
    platform: Platform.OS,
    timestamp: new Date().toISOString(),
  };
}

export function trackEvent(event: AnalyticsEvent) {
  const common = getCommonProperties();
  const properties = 'properties' in event ? event.properties : {};
  const payload = { event: event.name, ...common, ...properties };

  if (__DEV__) {
    console.log('[Analytics]', event.name, JSON.stringify(payload, null, 2));
  }

  // Metrics are best-effort by design: analytics must never block the user
  // journey or turn a temporary network failure into a product failure.
  if (_token) {
    void apiPost('/analytics/events', {
      name: event.name,
      properties: payload,
      occurred_at: common.timestamp,
    }, { token: _token }).catch(() => undefined);
  }
}
