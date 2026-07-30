import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { initializeApp, getApps, type FirebaseApp } from 'firebase/app';
import { getAuth, initializeAuth, type Auth } from 'firebase/auth';

/**
 * Firebase client — the app's only source of credentials.
 *
 * The backend stores no password and never performs an OAuth handshake:
 * Firebase owns sign-in, Google, phone verification and password resets, and
 * the API only verifies the ID token it issues.
 *
 * Every value below is public by design. They identify the project and are
 * compiled into the bundle; they grant nothing on their own. The service
 * account key is a different thing entirely and lives only on the server.
 *
 * KAN-91
 */

const config = {
  apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY?.trim() ?? '',
  authDomain: process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN?.trim() ?? '',
  projectId: process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID?.trim() ?? '',
  storageBucket: process.env.EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET?.trim() ?? '',
  messagingSenderId: process.env.EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID?.trim() ?? '',
  appId: process.env.EXPO_PUBLIC_FIREBASE_APP_ID?.trim() ?? '',
};

/** False when the project is not configured, so screens can say so plainly. */
export const isFirebaseConfigured = Boolean(config.apiKey && config.projectId);

/**
 * Web OAuth client id, created automatically by Firebase when the Google
 * provider is switched on. Empty means Google sign-in is not available yet.
 */
export const googleWebClientId =
  process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID?.trim() ?? '';

let app: FirebaseApp | null = null;
let authInstance: Auth | null = null;

if (isFirebaseConfigured) {
  app = getApps().length ? getApps()[0] : initializeApp(config);

  if (Platform.OS === 'web') {
    // The browser build keeps the session in IndexedDB on its own.
    authInstance = getAuth(app);
  } else {
    // On React Native there is no default persistence: without this the user
    // is signed out every time the app is closed. `getReactNativePersistence`
    // only exists in the React Native build, so it is required lazily rather
    // than imported — importing it would break the web bundle.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { getReactNativePersistence } = require('firebase/auth');
    authInstance = initializeAuth(app, {
      persistence: getReactNativePersistence(AsyncStorage),
    });
  }
}

export const auth = authInstance;

export function requireAuth(): Auth {
  if (!auth) {
    throw new Error(
      "La connexion n'est pas configurée : les variables "
      + 'EXPO_PUBLIC_FIREBASE_* sont absentes du .env.',
    );
  }
  return auth;
}
