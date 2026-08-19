import { useEffect, useRef, useCallback } from 'react';
import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { useAuth } from '../context/AuthContext';
import { apiPost } from '../api/client';
import { trackEvent } from '../analytics';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

async function getExpoPushToken(): Promise<string | null> {
  if (!Device.isDevice) return null;

  const { status: existing } = await Notifications.getPermissionsAsync();
  let finalStatus = existing;
  if (existing !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== 'granted') return null;

  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const tokenData = await Notifications.getExpoPushTokenAsync(
    projectId ? { projectId } : undefined,
  );
  return tokenData.data;
}

export function useNotifications(onNavigate?: (screen: string, params?: Record<string, string>) => void) {
  const { token: authToken } = useAuth();
  const registered = useRef(false);

  const registerToken = useCallback(async () => {
    if (registered.current || !authToken) return;
    const expoPushToken = await getExpoPushToken();
    if (!expoPushToken) return;

    try {
      await apiPost('/notifications/register', {
        expo_token: expoPushToken,
        platform: Platform.OS,
      }, { token: authToken });
      registered.current = true;
    } catch {
      // Will retry on next mount
    }
  }, [authToken]);

  useEffect(() => {
    registerToken();
  }, [registerToken]);

  useEffect(() => {
    if (!onNavigate) return;

    const sub = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data;
      const productId = typeof data?.product_id === 'string' ? data.product_id : undefined;
      const queueId = typeof data?.queue_id === 'string' ? data.queue_id : undefined;
      const isDrop = data?.type === 'drop';
      trackEvent({
        name: 'push_opened',
        properties: { product_id: productId, notification_type: isDrop ? 'drop' : 'alert' },
      });
      if (queueId && authToken) {
        void apiPost('/notifications/opened', { queue_id: queueId }, { token: authToken })
          .catch(() => undefined);
      }
      if (isDrop) {
        onNavigate('Main', { screen: 'Drop' });
      } else if (productId) {
        onNavigate('ProductDetail', { productId });
      }
    });
    return () => sub.remove();
  }, [authToken, onNavigate]);

  if (Platform.OS === 'android') {
    Notifications.setNotificationChannelAsync('default', {
      name: 'SwipeWear',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
    });
  }
}
