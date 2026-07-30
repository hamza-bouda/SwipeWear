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
import { useAuth } from '../context/AuthContext';
import { colors, typography, spacing, borderRadius } from '../theme';
import type { RootStackParamList } from '../navigation/types';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Login'>;

/**
 * Firebase reports failures as codes such as `auth/invalid-credential`.
 * Matching on codes rather than on message text means the wording can change
 * upstream without silently turning every error into an English fallback.
 */
function frenchMessage(error: unknown): string {
  const code = (error as { code?: string })?.code ?? '';
  const raw = error instanceof Error ? error.message : String(error);

  switch (code) {
    case 'auth/invalid-credential':
    case 'auth/wrong-password':
    case 'auth/user-not-found':
      return 'Email ou mot de passe incorrect.';
    case 'auth/email-already-in-use':
      return 'Un compte existe déjà avec cet email. Connecte-toi.';
    case 'auth/invalid-email':
      return "Cette adresse email n'est pas valide.";
    case 'auth/weak-password':
      return 'Le mot de passe doit faire au moins 6 caractères.';
    case 'auth/too-many-requests':
      return 'Trop de tentatives. Réessaie dans quelques minutes.';
    case 'auth/network-request-failed':
      return 'Serveur injoignable. Vérifie ta connexion.';
    case 'auth/operation-not-allowed':
      return "Ce mode de connexion n'est pas encore activé.";
    case 'auth/user-disabled':
      return 'Ce compte a été désactivé.';
    default:
      break;
  }
  // Thrown by AuthContext when the Google client id is missing, which means
  // the provider was never switched on in the Firebase console.
  if (raw.includes('provider is not enabled')) {
    return "La connexion Google n'est pas encore disponible. Utilise ton email.";
  }
  return raw;
}


export function LoginScreen() {
  const navigation = useNavigation<Nav>();
  const { signIn, signUp, signInWithGoogle, canSignIn, canUseGoogle } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [pending, setPending] = useState<'email' | 'google' | null>(null);

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
        await signUp(address, password);
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

  const handleGoogle = async () => {
    setPending('google');
    try {
      // The browser flow resolves in AuthContext, which signs in and lets
      // onIdTokenChanged take over — there is nothing to navigate to here.
      await signInWithGoogle();
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
          onPress={handleGoogle}
          variant="outline"
          loading={pending === 'google'}
          disabled={!canSignIn || !canUseGoogle || busy}
          style={styles.socialButton}
        />
        {canSignIn && !canUseGoogle && (
          <Text style={styles.providerHint}>
            Google sera disponible dès son activation côté SwipeWear.
          </Text>
        )}

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
  providerHint: {
    ...typography.caption,
    color: colors.textSecondary,
    textAlign: 'center',
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
