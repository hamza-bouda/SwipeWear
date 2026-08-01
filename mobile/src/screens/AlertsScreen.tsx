import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  TextInput,
  Modal,
  Switch,
  Alert as RNAlert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius } from '../theme';
import { useAlerts } from '../api';
import type { AlertItem } from '../api/useAlerts';
import type { RootStackParamList } from '../navigation/types';
import { ApiError } from '../api/client';

export function AlertsScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const rootNav = navigation.getParent<NativeStackNavigationProp<RootStackParamList>>();
  const nav = rootNav ?? navigation;
  const { alerts, missedDeals, freeLimit, loading, reload, create, remove, toggle } = useAlerts();
  const [showCreate, setShowCreate] = useState(false);
  const [newLabel, setNewLabel] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [creating, setCreating] = useState(false);

  const activeCount = alerts.filter(a => a.status === 'active').length;
  const atLimit = activeCount >= freeLimit;

  const goToPaywall = () => nav.navigate('Paywall' as never);

  const handleCreate = async () => {
    if (!newLabel.trim()) return;
    setCreating(true);
    try {
      await create({
        alert_type: 'style',
        label: newLabel.trim(),
        constraints: maxPrice ? { max_price: parseFloat(maxPrice) } : {},
      });
      setShowCreate(false);
      setNewLabel('');
      setMaxPrice('');
    } catch (e: any) {
      if (e instanceof ApiError && e.status === 403) {
        setShowCreate(false);
        goToPaywall();
      } else if (e.message?.includes('403')) {
        setShowCreate(false);
        goToPaywall();
      } else {
        RNAlert.alert('Erreur', 'Impossible de créer l\'alerte. Réessaie.');
      }
    } finally {
      setCreating(false);
    }
  };

  const handleRemove = (item: AlertItem) => {
    RNAlert.alert(
      'Supprimer l\'alerte',
      `Supprimer "${item.label}" ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        { text: 'Supprimer', style: 'destructive', onPress: () => remove(item.alert_id) },
      ],
    );
  };

  const renderAlert = ({ item }: { item: AlertItem }) => (
    <View style={styles.alertRow}>
      <View style={styles.alertIconWrap}>
        <Ionicons name="notifications" size={16} color={colors.accent} />
      </View>
      <View style={styles.alertInfo}>
        <Text style={styles.alertLabel} numberOfLines={1}>{item.label}</Text>
        <Text style={styles.alertSub}>
          {item.constraints?.max_price ? `Max ${item.constraints.max_price} €` : 'Pas de budget max'}
          {' · '}{item.status === 'active' ? 'Active' : 'En pause'}
        </Text>
      </View>
      <Switch
        value={item.status === 'active'}
        onValueChange={() => toggle(item.alert_id, item.status)}
        trackColor={{ false: colors.border, true: colors.accent }}
        thumbColor={item.status === 'active' ? colors.accentText : colors.textSecondary}
      />
      <TouchableOpacity onPress={() => handleRemove(item)} style={styles.deleteBtn} accessibilityLabel="Supprimer l'alerte">
        <Ionicons name="close" size={16} color={colors.textSecondary} />
      </TouchableOpacity>
    </View>
  );

  const ListHeader = () => (
    <View style={styles.listHeader}>
      {missedDeals > 0 && (
        <TouchableOpacity style={styles.missedBanner} onPress={goToPaywall} activeOpacity={0.8}>
          <View style={styles.missedRow}>
            <Ionicons name="time" size={14} color={colors.gold} style={{ marginRight: 6 }} />
            <Text style={styles.missedTitle}>{missedDeals} pépite{missedDeals > 1 ? 's' : ''} ratée{missedDeals > 1 ? 's' : ''}</Text>
          </View>
          <Text style={styles.missedSub}>
            Des articles sont partis pendant le délai de 30 min du plan gratuit. En Gold, tu es prévenu·e instantanément.
          </Text>
          <View style={styles.missedCta}>
            <Text style={styles.missedCtaText}>Passer Gold →</Text>
          </View>
        </TouchableOpacity>
      )}
      <Text style={styles.sectionTitle}>Mes alertes</Text>
    </View>
  );

  const ListFooter = () => (
    <View>
      <TouchableOpacity
        style={[styles.addRow, atLimit && styles.addRowLocked]}
        onPress={() => atLimit ? goToPaywall() : setShowCreate(true)}
        activeOpacity={0.7}
      >
        <View style={[styles.addIconWrap, atLimit && styles.addIconLocked]}>
          <Ionicons name="add" size={20} color={atLimit ? colors.disabled : colors.accent} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={[styles.addLabel, atLimit && styles.addLabelLocked]}>Nouvelle alerte</Text>
          <Text style={styles.addSub}>{activeCount} / {freeLimit} alertes actives · Gold pour l'illimité</Text>
        </View>
        {atLimit && (
          <View style={styles.goldChip}>
            <Ionicons name="lock-closed" size={10} color={colors.gold} />
            <Text style={styles.goldChipText}> GOLD</Text>
          </View>
        )}
      </TouchableOpacity>

      <TouchableOpacity style={styles.goldBanner} onPress={goToPaywall} activeOpacity={0.8}>
        <View style={styles.goldBannerRow}>
          <View style={styles.goldBannerLeft}>
            <Ionicons name="flash" size={14} color={colors.gold} style={{ marginRight: 6 }} />
            <Text style={styles.goldBannerTitle}>Passe en Gold</Text>
          </View>
          <View style={styles.goldPriceChip}>
            <Text style={styles.goldPriceText}>4,99 €/mois</Text>
          </View>
        </View>
        <Text style={styles.goldBannerSub}>
          Alertes illimitées + instantanées. Les gratuits sont prévenus 30 min après toi — la pièce part souvent avant.
        </Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
        <Text style={styles.title}>Alertes</Text>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.accent} size="large" />
        </View>
      ) : (
        <FlatList
          data={alerts}
          keyExtractor={a => a.alert_id}
          renderItem={renderAlert}
          ListHeaderComponent={ListHeader}
          ListFooterComponent={ListFooter}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.emptyWrap}>
              <View style={styles.emptyIconWrap}>
                <Ionicons name="notifications-outline" size={32} color={colors.disabled} />
              </View>
              <Text style={styles.emptyText}>Aucune alerte</Text>
              <Text style={styles.emptySub}>Crée une alerte pour être prévenu·e dès qu'une pièce correspond à ta recherche</Text>
            </View>
          }
        />
      )}

      <Modal visible={showCreate} animationType="slide" presentationStyle="pageSheet">
        <KeyboardAvoidingView
          style={styles.modal}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <ScrollView contentContainerStyle={styles.modalContent}>
            <Text style={styles.modalTitle}>Nouvelle alerte</Text>
            <Text style={styles.modalSub}>Décris la pièce que tu cherches</Text>

            <Text style={styles.fieldLabel}>Recherche</Text>
            <TextInput
              style={styles.input}
              placeholder="Ex : Perfecto cuir · Taille M · Vintage"
              placeholderTextColor={colors.textSecondary}
              value={newLabel}
              onChangeText={setNewLabel}
              autoFocus
            />

            <Text style={styles.fieldLabel}>Budget max (optionnel)</Text>
            <TextInput
              style={styles.input}
              placeholder="Ex : 80"
              placeholderTextColor={colors.textSecondary}
              value={maxPrice}
              onChangeText={setMaxPrice}
              keyboardType="numeric"
            />

            <TouchableOpacity
              style={[styles.createBtn, (!newLabel.trim() || creating) && styles.createBtnDisabled]}
              onPress={handleCreate}
              disabled={!newLabel.trim() || creating}
              activeOpacity={0.8}
            >
              <Text style={styles.createBtnText}>{creating ? 'Création…' : 'Créer l\'alerte'}</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={() => setShowCreate(false)} style={styles.cancelBtn}>
              <Text style={styles.cancelText}>Annuler</Text>
            </TouchableOpacity>
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
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
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  list: {
    paddingHorizontal: spacing.lg,
    paddingBottom: 120,
  },
  listHeader: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
    textTransform: 'uppercase',
    fontSize: 11,
    letterSpacing: 1,
  },
  missedBanner: {
    backgroundColor: colors.goldBg,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.gold,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  missedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  missedTitle: {
    ...typography.bodyBold,
    color: colors.gold,
  },
  missedSub: {
    ...typography.caption,
    color: colors.textSecondary,
    lineHeight: 16,
  },
  missedCta: {
    marginTop: spacing.sm,
    alignSelf: 'flex-start',
  },
  missedCtaText: {
    ...typography.bodyBold,
    color: colors.gold,
    fontSize: 13,
  },
  alertRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    gap: spacing.sm,
  },
  alertIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.accentLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  alertInfo: {
    flex: 1,
    minWidth: 0,
  },
  alertLabel: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  alertSub: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  deleteBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  addRowLocked: {
    opacity: 0.6,
  },
  addIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.accentLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addIconLocked: {
    backgroundColor: colors.surfaceElevated,
  },
  addLabel: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  addLabelLocked: {
    color: colors.textSecondary,
  },
  addSub: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  goldChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.goldBg,
    borderRadius: borderRadius.sm,
    borderWidth: 1,
    borderColor: colors.gold,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
  },
  goldChipText: {
    color: colors.gold,
    fontSize: 10,
    fontWeight: '700',
  },
  goldBanner: {
    backgroundColor: colors.goldBg,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.gold,
    padding: spacing.md,
    marginBottom: spacing.lg,
  },
  goldBannerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  goldBannerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  goldBannerTitle: {
    ...typography.bodyBold,
    color: colors.gold,
  },
  goldPriceChip: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
  },
  goldPriceText: {
    ...typography.label,
    color: colors.textPrimary,
  },
  goldBannerSub: {
    ...typography.caption,
    color: colors.textSecondary,
    lineHeight: 17,
  },
  emptyWrap: {
    alignItems: 'center',
    paddingVertical: spacing.xxl,
  },
  emptyIconWrap: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  emptyText: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  emptySub: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
    paddingHorizontal: spacing.md,
  },
  modal: {
    flex: 1,
    backgroundColor: colors.background,
  },
  modalContent: {
    padding: spacing.lg,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.xxl,
  },
  modalTitle: {
    ...typography.h1,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
    letterSpacing: -0.5,
  },
  modalSub: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.xl,
  },
  fieldLabel: {
    ...typography.label,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
    letterSpacing: 0.8,
  },
  input: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    color: colors.textPrimary,
    ...typography.body,
    marginBottom: spacing.lg,
  },
  createBtn: {
    backgroundColor: colors.accent,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  createBtnDisabled: {
    opacity: 0.35,
  },
  createBtnText: {
    ...typography.bodyBold,
    color: colors.accentText,
  },
  cancelBtn: {
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  cancelText: {
    ...typography.body,
    color: colors.textSecondary,
  },
});
