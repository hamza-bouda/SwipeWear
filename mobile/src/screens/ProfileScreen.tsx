import React from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { useNavigation, CommonActions } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Button } from '../components';
import { useAuth } from '../context/AuthContext';
import { colors, typography, spacing, borderRadius } from '../theme';
import type { RootStackParamList } from '../navigation/types';

export function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const rootNav = navigation.getParent<NativeStackNavigationProp<RootStackParamList>>();
  const { isAuthenticated, email, logout } = useAuth();

  const handleLogout = () => {
    Alert.alert('Se déconnecter', 'Confirmer la déconnexion ?', [
      { text: 'Annuler', style: 'cancel' },
      {
        text: 'Se déconnecter',
        style: 'destructive',
        onPress: () => {
          logout();
          (rootNav ?? navigation).dispatch(
            CommonActions.reset({ index: 0, routes: [{ name: 'Onboarding' }] }),
          );
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
          onPress: () => {
            logout();
            navigation.dispatch(
              CommonActions.reset({ index: 0, routes: [{ name: 'Onboarding' }] }),
            );
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

      {isAuthenticated ? (
        <View style={styles.body}>
          <View style={styles.accountCard}>
            <View style={styles.avatarWrap}>
              <Ionicons name="person" size={24} color={colors.accent} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.email} numberOfLines={1}>{email}</Text>
              <Text style={styles.accountSub}>Compte actif</Text>
            </View>
          </View>

          <View style={styles.menuSection}>
            <Text style={styles.menuLabel}>PERSONNALISATION</Text>
            <View style={styles.menuCard}>
              <Button
                title="Mon algorithme"
                onPress={() => (rootNav ?? navigation).navigate('Algorithm' as never)}
              />
            </View>
          </View>

          <View style={styles.menuSection}>
            <Text style={styles.menuLabel}>COMPTE</Text>
            <View style={styles.menuCard}>
              <Button title="Se déconnecter" onPress={handleLogout} variant="outline" />
              <Button
                title="Supprimer le compte"
                onPress={handleDeleteAccount}
                variant="ghost"
                style={styles.deleteButton}
              />
            </View>
          </View>
        </View>
      ) : (
        <View style={styles.body}>
          <View style={styles.guestCard}>
            <View style={styles.guestIconWrap}>
              <Ionicons name="person-outline" size={32} color={colors.disabled} />
            </View>
            <Text style={styles.guestTitle}>Non connecté</Text>
            <Text style={styles.guestSub}>
              Connecte-toi pour sauvegarder tes préférences sur tous tes appareils
            </Text>
            <Button
              title="Se connecter"
              onPress={() => (rootNav ?? navigation).navigate('Login' as never)}
            />
          </View>
        </View>
      )}
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
  deleteButton: {
    opacity: 0.55,
  },
  guestCard: {
    alignItems: 'center',
    paddingVertical: spacing.xxl,
    gap: spacing.md,
  },
  guestIconWrap: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  guestTitle: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  guestSub: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
});
