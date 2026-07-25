import React, { useCallback, useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import BottomSheet from '@gorhom/bottom-sheet';
import { SwipeDeck, RejectSheet, Button } from '../components';
import type { RejectReason } from '../components';
import { trackEvent } from '../analytics';
import { Product } from '../types';
import { useFeed, usePostEvent, useAlerts, ApiError } from '../api';
import { colors, typography, spacing } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { useSaves } from '../context/SavesContext';
import { useAlgorithm } from '../context/AlgorithmContext';

export function FeedScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { toggleSave } = useSaves();
  const { create: createAlert } = useAlerts();
  const [alertToast, setAlertToast] = useState<string | null>(null);
  const { preferences, revision } = useAlgorithm();
  const { products: feedProducts, loading, error, reload } = useFeed();
  const postEvent = usePostEvent();
  const [products, setProducts] = useState<Product[]>([]);
  const [deckEmpty, setDeckEmpty] = useState(false);
  const bottomSheetRef = useRef<BottomSheet>(null);
  const pendingProductRef = useRef<Product | null>(null);

  useEffect(() => {
    trackEvent({ name: 'session_started' });
  }, []);

  useEffect(() => {
    if (feedProducts.length > 0) {
      const excluded = new Set(preferences
        .filter((preference) => preference.kind === 'excluded_brand')
        .map((preference) => preference.label.toLowerCase()));
      setProducts(feedProducts.filter((product) => !excluded.has(product.brand.toLowerCase())));
      setDeckEmpty(false);
    }
  }, [feedProducts, preferences, revision]);

  const handleSwipeRight = useCallback((product: Product) => {
    trackEvent({ name: 'swipe', properties: { type: 'swipe_right', product_id: product.id } });
    postEvent(product.id, 'swipe_right');
  }, [postEvent]);

  const handleSwipeLeft = useCallback((product: Product) => {
    pendingProductRef.current = product;
    bottomSheetRef.current?.snapToIndex(0);
  }, []);

  const handleRejectSelect = useCallback((reason: RejectReason) => {
    const product = pendingProductRef.current;
    if (product) {
      trackEvent({ name: 'swipe', properties: { type: reason, product_id: product.id } });
      const eventType = reason === 'swipe_left_price' ? 'swipe_left_price' : 'swipe_left_style';
      postEvent(product.id, eventType);
      pendingProductRef.current = null;
    }
    bottomSheetRef.current?.close();
  }, [postEvent]);

  const handleTap = useCallback((product: Product) => {
    trackEvent({ name: 'product_opened', properties: { product_id: product.id } });
    postEvent(product.id, 'open');
    navigation.navigate('ProductDetail', { productId: product.id, product });
  }, [navigation, postEvent]);

  const handleAlert = useCallback(async (product: Product) => {
    // This used to navigate to the Alerts tab and nothing else — the bell
    // looked like it did something and never created an alert.
    setAlertToast(null);
    try {
      await createAlert({
        alert_type: 'specific_item',
        label: product.title,
        reference_product_id: product.id,
      });
      trackEvent({ name: 'alert_created', properties: { product_id: product.id } });
      setAlertToast(`Alerte créée pour « ${product.title.slice(0, 30)} »`);
    } catch (e) {
      // The free tier caps active alerts at three, so a refusal is expected
      // traffic and has to be readable rather than silent.
      setAlertToast(
        e instanceof ApiError && e.status === 403
          ? 'Limite de 3 alertes atteinte — passe en Premium ou supprime-en une.'
          : "L'alerte n'a pas pu être créée.",
      );
    }
  }, [createAlert]);

  const handleSave = useCallback((product: Product) => {
    trackEvent({ name: 'save', properties: { product_id: product.id } });
    postEvent(product.id, 'save');
    toggleSave(product);
  }, [toggleSave, postEvent]);

  useEffect(() => {
    if (!alertToast) return;
    const timer = setTimeout(() => setAlertToast(null), 3000);
    return () => clearTimeout(timer);
  }, [alertToast]);

  const handleDeckEmpty = useCallback(() => {
    setDeckEmpty(true);
  }, []);

  const handleReload = useCallback(() => {
    reload();
  }, [reload]);

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
        <View style={styles.logoWrap}>
          <Text style={styles.logo}>Swipe<Text style={styles.logoAccent}>Wear</Text></Text>
          <View style={styles.headerDot} />
        </View>
        <TouchableOpacity
          onPress={() => (navigation as any).navigate('Alerts')}
          style={styles.bellBtn}
          accessibilityLabel="Alertes"
        >
          <Ionicons name="notifications-outline" size={22} color={colors.textSecondary} />
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.emptyState}>
          <ActivityIndicator size="large" color={colors.accent} />
        </View>
      ) : error ? (
        // The feed used to swap in fabricated products here, so an outage
        // looked exactly like a working app — with items nobody could buy.
        <View style={styles.emptyState}>
          <Ionicons name="cloud-offline-outline" size={56} color={colors.disabled} style={styles.emptyIcon} />
          <Text style={styles.emptyTitle}>Connexion impossible</Text>
          <Text style={styles.emptySubtitle}>
            Impossible de charger tes pièces pour le moment.
          </Text>
          <Button title="Réessayer" onPress={handleReload} style={styles.reloadButton} />
        </View>
      ) : deckEmpty || products.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="checkmark-circle-outline" size={56} color={colors.disabled} style={styles.emptyIcon} />
          <Text style={styles.emptyTitle}>Tout vu !</Text>
          <Text style={styles.emptySubtitle}>
            Plus de pièces à swiper pour l'instant
          </Text>
          <Button
            title="Charger plus"
            onPress={handleReload}
            style={styles.reloadButton}
          />
        </View>
      ) : (
        <SwipeDeck
          products={products}
          onSwipeRight={handleSwipeRight}
          onSwipeLeft={handleSwipeLeft}
          onTap={handleTap}
          onSave={handleSave}
          onDeckEmpty={handleDeckEmpty}
          onAlert={handleAlert}
          onSwipeUp={handleAlert}
        />
      )}

      {alertToast && (
        <View style={styles.toast} pointerEvents="none">
          <Ionicons name="notifications" size={16} color={colors.textPrimary} />
          <Text style={styles.toastText} numberOfLines={2}>{alertToast}</Text>
        </View>
      )}

      <RejectSheet ref={bottomSheetRef} onSelect={handleRejectSelect} />
    </View>
  );
}

const styles = StyleSheet.create({
  toast: {
    position: 'absolute',
    left: spacing.lg,
    right: spacing.lg,
    bottom: spacing.xl,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.accent,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: 12,
  },
  toastText: {
    ...typography.caption,
    color: colors.textPrimary,
    flex: 1,
    fontWeight: '600',
  },
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logoWrap: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  logo: {
    ...typography.h2,
    color: colors.textPrimary,
    letterSpacing: -0.5,
  },
  logoAccent: {
    color: colors.accent,
  },
  headerDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.accent,
    marginLeft: 4,
    marginBottom: 2,
  },
  bellBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  emptyIcon: {
    marginBottom: spacing.md,
  },
  emptyTitle: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  emptySubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
    textAlign: 'center',
  },
  reloadButton: {
    minWidth: 160,
  },
});
