import React, { useCallback, useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import BottomSheet from '@gorhom/bottom-sheet';
import { SwipeDeck, RejectSheet, Button } from '../components';
import type { RejectReason } from '../components';
import { trackEvent } from '../analytics';
import { Product } from '../types';
import { useFeed } from '../api';
import { colors, typography, spacing } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { useSaves } from '../context/SavesContext';
import { useAlgorithm } from '../context/AlgorithmContext';

export function FeedScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { toggleSave } = useSaves();
  const { preferences, revision } = useAlgorithm();
  const { products: feedProducts, loading, reload } = useFeed();
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
  }, []);

  const handleSwipeLeft = useCallback((product: Product) => {
    pendingProductRef.current = product;
    bottomSheetRef.current?.snapToIndex(0);
  }, []);

  const handleRejectSelect = useCallback((reason: RejectReason) => {
    const product = pendingProductRef.current;
    if (product) {
      trackEvent({ name: 'swipe', properties: { type: reason, product_id: product.id } });
      pendingProductRef.current = null;
    }
    bottomSheetRef.current?.close();
  }, []);

  const handleTap = useCallback((product: Product) => {
    trackEvent({ name: 'product_opened', properties: { product_id: product.id } });
    navigation.navigate('ProductDetail', { productId: product.id });
  }, [navigation]);

  const handleSave = useCallback((product: Product) => {
    trackEvent({ name: 'save', properties: { product_id: product.id } });
    toggleSave(product);
  }, [toggleSave]);

  const handleDeckEmpty = useCallback(() => {
    setDeckEmpty(true);
  }, []);

  const handleReload = useCallback(() => {
    reload();
  }, [reload]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.logo}>Swipe<Text style={styles.logoAccent}>Wear</Text></Text>
      </View>

      {loading ? (
        <View style={styles.emptyState}>
          <ActivityIndicator size="large" color={colors.textPrimary} />
        </View>
      ) : deckEmpty ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>All caught up!</Text>
          <Text style={styles.emptySubtitle}>
            No more items to swipe right now
          </Text>
          <Button
            title="Load more"
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
        />
      )}

      <RejectSheet ref={bottomSheetRef} onSelect={handleRejectSelect} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingTop: 60,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    alignItems: 'center',
  },
  logo: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  logoAccent: {
    color: colors.accent,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
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
  },
  reloadButton: {
    minWidth: 160,
  },
});
