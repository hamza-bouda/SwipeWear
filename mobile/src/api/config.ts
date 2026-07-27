import { Platform } from 'react-native';

/**
 * Backend base URL.
 *
 * Configuration:
 *   EXPO_PUBLIC_API_URL — full base URL of the deployed backend
 *                         (e.g. https://swipewear-api.up.railway.app).
 *
 * When unset (or empty), falls back to the local dev backend, matching the
 * emulator networking rules: the Android emulator cannot resolve
 * `localhost` to the host machine and needs the special alias `10.0.2.2`.
 *
 * KAN-83
 */

const DEV_HOST = Platform.select({
  android: '10.0.2.2',
  default: 'localhost',
});

const DEV_API_BASE_URL = `http://${DEV_HOST}:8000`;

const configuredApiUrl = process.env.EXPO_PUBLIC_API_URL?.trim() ?? '';

export const API_BASE_URL = configuredApiUrl.length > 0 ? configuredApiUrl : DEV_API_BASE_URL;
