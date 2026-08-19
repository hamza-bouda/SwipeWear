import { useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiPost } from './client';

type EventType =
  | 'swipe_right'
  | 'swipe_left_style'
  | 'swipe_left_price'
  | 'save'
  | 'open';

export function usePostEvent() {
  const { token } = useAuth();

  return useCallback(
    (productId: string, eventType: EventType) => {
      const doPost = async () => {
        try {
          if (!token) return;
          await apiPost(
            '/events',
            { product_id: productId, event_type: eventType },
            { token },
          );
        } catch {
          // fire-and-forget: log failures silently
        }
      };
      doPost();
    },
    [token],
  );
}
