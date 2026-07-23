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
  const { userId, token } = useAuth();

  return useCallback(
    (productId: string, eventType: EventType) => {
      const doPost = async () => {
        try {
          let authToken = token;
          if (!authToken) {
            const resp = await apiPost<{ access_token: string }>('/auth/token', {
              user_id: userId,
            });
            authToken = resp.access_token;
          }
          await apiPost(
            '/events',
            { product_id: productId, event_type: eventType },
            { token: authToken },
          );
        } catch {
          // fire-and-forget: log failures silently
        }
      };
      doPost();
    },
    [userId, token],
  );
}
