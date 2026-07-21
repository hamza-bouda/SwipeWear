export type AnalyticsEvent =
  | { name: 'session_started' }
  | { name: 'onboarding_started' }
  | { name: 'onboarding_completed'; properties: { route: 'styles' | 'images' | 'skip' } }
  | { name: 'swipe'; properties: { type: 'swipe_right' | 'swipe_left_style' | 'swipe_left_price'; product_id: string } }
  | { name: 'save'; properties: { product_id: string } }
  | { name: 'product_opened'; properties: { product_id: string } }
  | { name: 'offer_clicked'; properties: { product_id: string; url: string } };

export type EventName = AnalyticsEvent['name'];
