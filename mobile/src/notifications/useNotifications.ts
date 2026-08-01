import { useEffect, useRef, useCallback } from 'react';
import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { useAuth } from '../context/AuthContext';
import { apiPost } from '../api/client';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
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
      if (data?.type === 'drop') {
        onNavigate('MainTabs', { screen: 'Drop' });
      } else if (data?.product_id) {
        onNavigate('ProductDetail', { productId: data.product_id as string });
      }
    });
    return () => sub.remove();
  }, [onNavigate]);

  if (Platform.OS === 'android') {
    Notifications.setNotificationChannelAsync('default', {
      name: 'SwipeWear',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
    });
  }
}
