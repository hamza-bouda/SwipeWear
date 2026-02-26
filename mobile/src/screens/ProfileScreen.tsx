import React from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { useNavigation, CommonActions } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Button } from '../components';
import { useAuth } from '../context/AuthContext';
import { usePreferences } from '../context/PreferencesContext';
import { colors, typography, spacing, borderRadius } from '../theme';
import type { RootStackParamList } from '../navigation/types';

const GENDER_LABELS = {
  men: 'Homme',
  women: 'Femme',
  unisex: 'Tout',
} as const;

export function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const rootNav = navigation.getParent<NativeStackNavigationProp<RootStackParamList>>();
  const { isAuthenticated, email, logout, deleteAccount } = useAuth();
  const { gender } = usePreferences();

  const resetToOnboarding = () =>
    (rootNav ?? navigation).dispatch(
      CommonActions.reset({ index: 0, routes: [{ name: 'Onboarding' }] }),
    );

  const handleLogout = () => {
    Alert.alert('Se déconnecter', 'Confirmer la déconnexion ?', [
      { text: 'Annuler', style: 'cancel' },
      {
        text: 'Se déconnecter',
        style: 'destructive',
        onPress: async () => {
          await logout();
          resetToOnboarding();
        },
      },
    ]);
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Supprimer le compte',
      'Cette action supprimera définitivement ton compte, tes préférences et toutes tes données. Impossible de revenir en arrière.',
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: async () => {
            try {
              // This used to call logout() only: the account, the profile and
              // the event log stayed on the server while the screen claimed
              // they were deleted for good.
              await deleteAccount();
              resetToOnboarding();
            } catch {
              Alert.alert(
                'Suppression impossible',
                'Ton compte n\'a pas pu être supprimé. Réessaie quand tu es connecté à internet.',
              );
            }
          },
        },
      ],
    );
  };

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
        <Text style={styles.title}>Profil</Text>
      </View>

      <View style={styles.body}>
        {isAuthenticated ? (
          <View style={styles.accountCard}>
            <View style={styles.avatarWrap}>
              <Ionicons name="person" size={24} color={colors.accent} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.email} numberOfLines={1}>{email}</Text>
              <Text style={styles.accountSub}>Compte actif</Text>
            </View>
          </View>
        ) : (
          <View style={styles.accountCard}>
            <View style={styles.avatarWrapGuest}>
              <Ionicons name="person-outline" size={24} color={colors.disabled} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.email}>Non connecté</Text>
              <Text style={styles.accountSub}>
                Connecte-toi pour retrouver tes pièces sur tous tes appareils
              </Text>
            </View>
          </View>
        )}

        {/* Personalisation used to be rendered only for signed-in users, so a
            visitor browsing without an account had no way to change the gender
            or the algorithm — while the first screen promised exactly that. */}
        <View style={styles.menuSection}>
          <Text style={styles.menuLabel}>PERSONNALISATION</Text>
          <View style={styles.menuCard}>
            <Button
              title="Mon algorithme"
              onPress={() => (rootNav ?? navigation).navigate('Algorithm' as never)}
            />
            <Button
              title={`Je cherche : ${GENDER_LABELS[gender ?? 'unisex']}`}
              variant="outline"
              onPress={() => (rootNav ?? navigation).navigate('GenderLanguage' as never)}
              style={styles.settingButton}
            />
          </View>
        </View>

        <View style={styles.menuSection}>
          <Text style={styles.menuLabel}>COMPTE</Text>
          <View style={styles.menuCard}>
            {isAuthenticated ? (
              <>
                <Button title="Se déconnecter" onPress={handleLogout} variant="outline" />
                <Button
                  title="Supprimer le compte"
                  onPress={handleDeleteAccount}
                  variant="ghost"
                  style={styles.deleteButton}
                />
              </>
            ) : (
              <Button
                title="Se connecter"
                onPress={() => (rootNav ?? navigation).navigate('Login' as never)}
              />
            )}
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
  },
  title: {
    ...typography.h1,
    color: colors.textPrimary,
    letterSpacing: -0.5,
  },
  body: {
    flex: 1,
    paddingHorizontal: spacing.lg,
    gap: spacing.lg,
  },
  accountCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    gap: spacing.md,
  },
  avatarWrap: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.accentLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarWrapGuest: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  email: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  accountSub: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  menuSection: {
    gap: spacing.xs,
  },
  menuLabel: {
    ...typography.label,
    color: colors.textSecondary,
    fontSize: 10,
    letterSpacing: 1,
    paddingHorizontal: spacing.xs,
  },
  menuCard: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    gap: spacing.sm,
  },
  settingButton: {
    marginTop: 0,
  },
  deleteButton: {
    opacity: 0.55,
  },
});
