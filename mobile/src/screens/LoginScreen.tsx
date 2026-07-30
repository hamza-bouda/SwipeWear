import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { Button } from '../components';
import { useAuth, type OAuthProvider } from '../context/AuthContext';
import { colors, typography, spacing, borderRadius } from '../theme';
import type { RootStackParamList } from '../navigation/types';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Login'>;

/** Errors come from Supabase in English; these are the ones users actually hit. */
function frenchMessage(error: unknown): string {
  const raw = error instanceof Error ? error.message : String(error);
  const lower = raw.toLowerCase();
  if (lower.includes('invalid login credentials')) {
    return 'Email ou mot de passe incorrect.';
  }
  if (lower.includes('already registered') || lower.includes('already been registered')) {
    return 'Un compte existe déjà avec cet email. Connecte-toi.';
  }
  if (lower.includes('email not confirmed')) {
    return "Confirme d'abord ton email : regarde ta boîte de réception.";
  }
  if (lower.includes('password') && lower.includes('at least')) {
    return 'Le mot de passe doit faire au moins 8 caractères.';
  }
  if (lower.includes('rate limit') || lower.includes('too many')) {
    return 'Trop de tentatives. Réessaie dans quelques minutes.';
  }
  if (lower.includes('failed to fetch') || lower.includes('network')) {
    return 'Serveur injoignable. Vérifie ta connexion.';
  }
  // Les deux erreurs de mise en service : le fournisseur n'a jamais été activé
  // dans le tableau de bord, ou l'URL de redirection n'y est pas déclarée.
  // Sans ces deux cas, l'utilisateur voyait le message anglais brut de
  // Supabase — « Unsupported provider: provider is not enabled ».
  if (lower.includes('provider is not enabled') || lower.includes('unsupported provider')) {
    return "Ce mode de connexion n'est pas encore disponible. Utilise ton email pour l'instant.";
  }
  if (lower.includes('redirect') && (lower.includes('not allowed') || lower.includes('invalid'))) {
    return "La redirection après connexion a été refusée. C'est un réglage à corriger côté SwipeWear.";
  }
  return raw;
}

export function LoginScreen() {
  const navigation = useNavigation<Nav>();
  const { signIn, signUp, signInWithProvider, canSignIn } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [pending, setPending] = useState<'email' | OAuthProvider | null>(null);

  const handleSubmit = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Erreur', 'Remplis tous les champs.');
      return;
    }
    if (mode === 'register' && password.length < 8) {
      Alert.alert('Erreur', 'Le mot de passe doit faire au moins 8 caractères.');
      return;
    }

    setPending('email');
    try {
      const address = email.trim().toLowerCase();
      if (mode === 'register') {
        const needsConfirmation = await signUp(address, password);
        if (needsConfirmation) {
          // No session was created. Navigating to the feed here would show a
          // signed-out user everything as if they had signed up.
          Alert.alert(
            'Confirme ton email',
            `On vient d'envoyer un lien à ${address}. Ouvre-le pour activer ton compte.`,
          );
          return;
        }
      } else {
        await signIn(address, password);
      }
      navigation.replace('Main');
    } catch (e) {
      Alert.alert('Connexion impossible', frenchMessage(e));
    } finally {
      setPending(null);
    }
  };

  const handleProvider = async (provider: OAuthProvider) => {
    setPending(provider);
    try {
      await signInWithProvider(provider);
      // On the web the page navigates away and comes back signed in; on native
      // the session lands before this resolves.
      if (Platform.OS !== 'web') navigation.replace('Main');
    } catch (e) {
      Alert.alert('Connexion impossible', frenchMessage(e));
    } finally {
      setPending(null);
    }
  };

  const busy = pending !== null;

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.content}>
        <Text style={styles.logo}>Swipe<Text style={styles.logoAccent}>Wear</Text></Text>
        <Text style={styles.subtitle}>
          {mode === 'login' ? 'Content de te revoir' : 'Crée ton compte'}
        </Text>

        {!canSignIn && (
          <View style={styles.notice}>
            <Ionicons name="warning-outline" size={18} color={colors.textPrimary} />
            <Text style={styles.noticeText}>
              La connexion n'est pas configurée sur cet appareil. Tu peux
              continuer sans compte.
            </Text>
          </View>
        )}

        <View style={styles.form}>
          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor={colors.disabled}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            editable={canSignIn && !busy}
            accessibilityLabel="Email"
            textContentType="emailAddress"
          />
          <TextInput
            style={styles.input}
            placeholder="Mot de passe"
            placeholderTextColor={colors.disabled}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            editable={canSignIn && !busy}
            accessibilityLabel="Mot de passe"
            textContentType="password"
          />

          <Button
            title={mode === 'login' ? 'Se connecter' : 'Créer mon compte'}
            onPress={handleSubmit}
            loading={pending === 'email'}
            disabled={!canSignIn || busy}
          />
        </View>

        <View style={styles.divider}>
          <View style={styles.dividerLine} />
          <Text style={styles.dividerText}>ou</Text>
          <View style={styles.dividerLine} />
        </View>

        <Button
          title="Continuer avec Google"
          onPress={() => handleProvider('google')}
          variant="outline"
          loading={pending === 'google'}
          disabled={!canSignIn || busy}
          style={styles.socialButton}
        />
        <Button
          title="Continuer avec Apple"
          onPress={() => handleProvider('apple')}
          variant="outline"
          loading={pending === 'apple'}
          disabled={!canSignIn || busy}
          style={styles.socialButton}
        />

        <TouchableOpacity
          style={styles.switchMode}
          onPress={() => setMode(mode === 'login' ? 'register' : 'login')}
          disabled={busy}
          accessibilityRole="button"
          accessibilityLabel={
            mode === 'login' ? 'Passer à la création de compte' : 'Passer à la connexion'
          }
        >
          <Text style={styles.switchText}>
            {mode === 'login'
              ? "Pas encore de compte ? Inscris-toi"
              : 'Déjà un compte ? Connecte-toi'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.skipButton}
          onPress={() => navigation.replace('Main')}
          disabled={busy}
          accessibilityRole="button"
          accessibilityLabel="Passer la connexion"
        >
          <Text style={styles.skipText}>Passer pour l'instant</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
  },
  logo: {
    ...typography.h1,
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: spacing.xs,
  },
  logoAccent: {
    color: colors.accentDark,
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.xl,
  },
  notice: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.accentLight,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.lg,
  },
  noticeText: {
    ...typography.caption,
    color: colors.textPrimary,
    flex: 1,
    lineHeight: 18,
  },
  form: {
    gap: spacing.md,
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    paddingHorizontal: spacing.md,
    ...typography.body,
    color: colors.textPrimary,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: spacing.lg,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: colors.border,
  },
  dividerText: {
    ...typography.caption,
    color: colors.textSecondary,
    marginHorizontal: spacing.md,
  },
  socialButton: {
    marginBottom: spacing.sm,
  },
  switchMode: {
    alignItems: 'center',
    marginTop: spacing.lg,
  },
  switchText: {
    ...typography.body,
    color: colors.textSecondary,
  },
  skipButton: {
    alignItems: 'center',
    marginTop: spacing.md,
  },
  skipText: {
    ...typography.body,
    color: colors.disabled,
    textDecorationLine: 'underline',
  },
});
