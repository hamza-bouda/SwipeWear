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
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button } from '../components';
import { useAuth } from '../context/AuthContext';
import { colors, typography, spacing } from '../theme';
import type { RootStackParamList } from '../navigation/types';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Login'>;

export function LoginScreen() {
  const navigation = useNavigation<Nav>();
  const { login, getAnonymousId } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Erreur', 'Remplis tous les champs.');
      return;
    }
    if (mode === 'register' && password.length < 8) {
      Alert.alert('Erreur', 'Le mot de passe doit faire au moins 8 caractères.');
      return;
    }

    setLoading(true);
    try {
      // Stub API call — will connect to real backend later
      const anonId = getAnonymousId();
      const stubUserId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      });
      const stubToken = 'stub-jwt-token';

      await new Promise((resolve) => setTimeout(resolve, 800));

      login(stubUserId, stubToken, email.trim().toLowerCase());
      navigation.replace('Main');
    } catch {
      Alert.alert('Erreur', 'La connexion a échoué. Réessaie.');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    navigation.replace('Main');
  };

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
            accessibilityLabel="Mot de passe"
            textContentType="password"
          />

          <Button
            title={mode === 'login' ? 'Se connecter' : 'Créer mon compte'}
            onPress={handleSubmit}
            loading={loading}
            disabled={loading}
          />
        </View>

        <View style={styles.divider}>
          <View style={styles.dividerLine} />
          <Text style={styles.dividerText}>ou</Text>
          <View style={styles.dividerLine} />
        </View>

        <Button
          title="Continuer avec Apple"
          onPress={() => Alert.alert('Bientôt disponible', 'La connexion avec Apple arrive bientôt.')}
          variant="outline"
          style={styles.socialButton}
        />
        <Button
          title="Continuer avec Google"
          onPress={() => Alert.alert('Bientôt disponible', 'La connexion avec Google arrive bientôt.')}
          variant="outline"
          style={styles.socialButton}
        />

        <TouchableOpacity
          style={styles.switchMode}
          onPress={() => setMode(mode === 'login' ? 'register' : 'login')}
          accessibilityRole="button"
          accessibilityLabel={mode === 'login' ? 'Passer à la création de compte' : 'Passer à la connexion'}
        >
          <Text style={styles.switchText}>
            {mode === 'login'
              ? "Pas encore de compte ? Inscris-toi"
              : 'Déjà un compte ? Connecte-toi'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.skipButton} onPress={handleSkip} accessibilityRole="button" accessibilityLabel="Passer la connexion">
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
