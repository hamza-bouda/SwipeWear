import React from 'react';
import { View, Text, StyleSheet, Alert, ScrollView, TouchableOpacity } from 'react-native';
import { useNavigation, CommonActions } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Button } from '../components';
import { useAuth } from '../context/AuthContext';
import { usePreferences, NotificationFrequency } from '../context/PreferencesContext';
import { usePremium } from '../billing';
import { apiPatch } from '../api/client';
import { colors, typography, spacing, borderRadius } from '../theme';
import type { RootStackParamList } from '../navigation/types';

const GENDER_LABELS = {
  men: 'Homme',
  women: 'Femme',
  unisex: 'Tout',
} as const;

const ALL_SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL'] as const;

const NOTIF_OPTIONS: { key: NotificationFrequency; label: string; desc: string }[] = [
  { key: 'instant', label: 'Instantané', desc: 'Chaque alerte dès qu\'elle matche' },
  { key: 'daily_digest', label: 'Résumé quotidien', desc: 'Un récap par jour à 19h' },
  { key: 'disabled', label: 'Désactivées', desc: 'Aucune notification push' },
];

export function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const rootNav = navigation.getParent<NativeStackNavigationProp<RootStackParamList>>();
  const { isAuthenticated, email, token, logout, deleteAccount } = useAuth();
  const { gender, sizes, notificationFrequency, setSizes, setNotificationFrequency } = usePreferences();
  const { isActive: isPremium, isTrialing, loading: premiumLoading } = usePremium();

  const nav = rootNav ?? navigation;

  const resetToOnboarding = () =>
    nav.dispatch(
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

  const toggleSize = (size: string) => {
    const next = sizes.includes(size)
      ? sizes.filter(s => s !== size)
      : [...sizes, size];
    setSizes(next);
    if (token) {
      apiPatch('/profile', { hard_constraints: { sizes: next } }, { token }).catch(() => {});
    }
  };

  const handleNotifChange = (freq: NotificationFrequency) => {
    setNotificationFrequency(freq);
    if (token) {
      apiPatch('/notifications/preferences', { preference: freq }, { token }).catch(() => {});
    }
  };

  const premiumLabel = premiumLoading
    ? 'Chargement…'
    : isPremium
      ? isTrialing ? 'Gold (essai)' : 'Gold'
      : 'Gratuit';

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 120 }}>
      <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
        <Text style={styles.title}>Profil</Text>
      </View>

      <View style={styles.body}>
        {/* Account card */}
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

        {/* Subscription */}
        <View style={styles.menuSection}>
          <Text style={styles.menuLabel}>ABONNEMENT</Text>
          <View style={styles.menuCard}>
            <View style={styles.subscriptionRow}>
              <View style={styles.subscriptionInfo}>
                <Text style={styles.subscriptionStatus}>{premiumLabel}</Text>
                <Text style={styles.subscriptionSub}>
                  {isPremium ? 'Alertes instantanées et illimitées' : 'Alertes limitées, délai 30 min'}
                </Text>
              </View>
              {isPremium ? (
                <View style={styles.premiumBadge}>
                  <Ionicons name="flash" size={12} color={colors.gold} />
                  <Text style={styles.premiumBadgeText}> GOLD</Text>
                </View>
              ) : (
                <TouchableOpacity
                  style={styles.upgradeBtn}
                  onPress={() => nav.navigate('Paywall' as never)}
                  activeOpacity={0.8}
                >
                  <Text style={styles.upgradeBtnText}>Passer Gold</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        </View>

        {/* Personalisation */}
        <View style={styles.menuSection}>
          <Text style={styles.menuLabel}>PERSONNALISATION</Text>
          <View style={styles.menuCard}>
            <Button
              title="Mon algorithme"
              onPress={() => nav.navigate('Algorithm' as never)}
            />
            <Button
              title={`Je cherche : ${GENDER_LABELS[gender ?? 'unisex']}`}
              variant="outline"
              onPress={() => nav.navigate('GenderLanguage' as never)}
              style={styles.settingButton}
            />
          </View>
        </View>

        {/* Sizes */}
        <View style={styles.menuSection}>
          <Text style={styles.menuLabel}>MES TAILLES</Text>
          <View style={styles.menuCard}>
            <Text style={styles.sizesHint}>Sélectionne tes tailles pour filtrer les résultats</Text>
            <View style={styles.sizesGrid}>
              {ALL_SIZES.map(size => {
                const selected = sizes.includes(size);
                return (
                  <TouchableOpacity
                    key={size}
                    style={[styles.sizeChip, selected && styles.sizeChipActive]}
                    onPress={() => toggleSize(size)}
                    activeOpacity={0.7}
                  >
                    <Text style={[styles.sizeText, selected && styles.sizeTextActive]}>{size}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
        </View>

        {/* Notification frequency */}
        <View style={styles.menuSection}>
          <Text style={styles.menuLabel}>NOTIFICATIONS</Text>
          <View style={styles.menuCard}>
            {NOTIF_OPTIONS.map(opt => {
              const active = notificationFrequency === opt.key;
              return (
                <TouchableOpacity
                  key={opt.key}
                  style={[styles.notifRow, active && styles.notifRowActive]}
                  onPress={() => handleNotifChange(opt.key)}
                  activeOpacity={0.7}
                >
                  <View style={styles.notifRadio}>
                    {active && <View style={styles.notifRadioDot} />}
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.notifLabel, active && styles.notifLabelActive]}>{opt.label}</Text>
                    <Text style={styles.notifDesc}>{opt.desc}</Text>
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Account */}
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
                onPress={() => nav.navigate('Login' as never)}
              />
            )}
          </View>
        </View>
      </View>
    </ScrollView>
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
  subscriptionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.xs,
  },
  subscriptionInfo: {
    flex: 1,
  },
  subscriptionStatus: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  subscriptionSub: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  premiumBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.goldBg,
    borderRadius: borderRadius.sm,
    borderWidth: 1,
    borderColor: colors.gold,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
  },
  premiumBadgeText: {
    color: colors.gold,
    fontSize: 10,
    fontWeight: '700',
  },
  upgradeBtn: {
    backgroundColor: colors.accent,
    borderRadius: borderRadius.sm,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  upgradeBtnText: {
    color: colors.accentText,
    fontSize: 12,
    fontWeight: '700',
  },
  sizesHint: {
    ...typography.caption,
    color: colors.textSecondary,
    paddingHorizontal: spacing.xs,
  },
  sizesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
    paddingHorizontal: spacing.xs,
    paddingTop: spacing.xs,
  },
  sizeChip: {
    width: 48,
    height: 40,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sizeChipActive: {
    backgroundColor: colors.textPrimary,
    borderColor: colors.textPrimary,
  },
  sizeText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  sizeTextActive: {
    color: colors.textInverse,
  },
  notifRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  notifRowActive: {
    backgroundColor: colors.accentLight,
  },
  notifRadio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  notifRadioDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.accent,
  },
  notifLabel: {
    ...typography.bodyBold,
    color: colors.textPrimary,
    fontSize: 14,
  },
  notifLabelActive: {
    color: colors.accentDark,
  },
  notifDesc: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 1,
  },
});
