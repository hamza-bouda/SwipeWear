import 'react-native-url-polyfill/auto';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient, type SupabaseClient } from '@supabase/supabase-js';

/**
 * Supabase client — the app's only source of credentials.
 *
 * The backend no longer stores passwords, and never did OAuth. Supabase owns
 * sign-in, Google and Apple, password resets and email confirmation; the API
 * only verifies the access token it issues.
 *
 * The anon key is meant to be public — it identifies the project, it does not
 * grant anything on its own. The service role key is a different thing
 * entirely and must never appear in this bundle.
 *
 * KAN-90
 */

const url = process.env.EXPO_PUBLIC_SUPABASE_URL?.trim() ?? '';
const anonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY?.trim() ?? '';

/** False when the project is not configured, so screens can say so plainly. */
export const isSupabaseConfigured = Boolean(url && anonKey);

export const supabase: SupabaseClient | null = isSupabaseConfigured
  ? createClient(url, anonKey, {
      auth: {
        storage: AsyncStorage,
        persistSession: true,
        autoRefreshToken: true,
        // PKCE rather than the implicit flow: the redirect carries a
        // single-use code instead of the access token itself, so the token
        // never travels through a URL another app on the device could observe.
        flowType: 'pkce',
        // On native there is no URL bar to read the OAuth fragment from; the
        // redirect is handled explicitly after the browser closes. Leaving
        // this on would make Supabase look for a session in a URL that never
        // exists and log a warning on every launch.
        detectSessionInUrl: Platform.OS === 'web',
      },
    })
  : null;

export function requireSupabase(): SupabaseClient {
  if (!supabase) {
    throw new Error(
      "La connexion n'est pas configurée : EXPO_PUBLIC_SUPABASE_URL et "
      + 'EXPO_PUBLIC_SUPABASE_ANON_KEY sont absents du .env.',
    );
  }
  return supabase;
}
