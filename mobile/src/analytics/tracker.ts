import { Platform } from 'react-native';
import type { AnalyticsEvent } from './events';

const APP_VERSION = '1.0.0';

interface CommonProperties {
  user_id: string;
  app_version: string;
  platform: string;
  timestamp: string;
}

let _userId = 'anonymous';

export function setAnalyticsUserId(userId: string) {
  _userId = userId;
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

  // PostHog integration point:
  // posthog.capture(event.name, { ...common, ...properties });
}
