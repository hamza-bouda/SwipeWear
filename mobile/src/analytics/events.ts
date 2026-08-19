export type AnalyticsEvent =
  | { name: 'session_started' }
  | { name: 'onboarding_started' }
  | { name: 'onboarding_completed'; properties: { route: 'styles' | 'images' | 'skip' } }
  | { name: 'swipe'; properties: { type: 'swipe_right' | 'swipe_left_style' | 'swipe_left_price'; product_id: string } }
  | { name: 'save'; properties: { product_id: string } }
  | { name: 'product_opened'; properties: { product_id: string } }
  | { name: 'alert_created'; properties: { alert_type: 'style' | 'specific_item'; product_id?: string } }
  | { name: 'alert_deleted'; properties: { alert_id: string } }
  | { name: 'ladder_viewed'; properties: { product_id: string } }
  | { name: 'drop_opened'; properties: { available_count: number } }
  | { name: 'drop_completed' }
  | { name: 'push_opened'; properties: { product_id?: string; notification_type: 'drop' | 'alert' } }
  | { name: 'paywall_viewed'; properties: { trigger: 'alert_limit' | 'profile' | 'drop_completed' } }
  | { name: 'subscribe'; properties: { trigger: 'alert_limit' | 'profile' | 'drop_completed' } }
  | {
      name: 'outbound_click';
      properties: {
        product_id: string;
        source: string;
        price: number;
        position: 'detail' | number;
      };
    }
  | { name: 'share_card_generated'; properties: { product_id: string } };

export type EventName = AnalyticsEvent['name'];
