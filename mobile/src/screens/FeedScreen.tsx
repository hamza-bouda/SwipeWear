import React, { useCallback, useRef, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import BottomSheet from '@gorhom/bottom-sheet';
import { SwipeDeck, RejectSheet, Button } from '../components';
import type { RejectReason } from '../components';
import { Product } from '../types';
import { MOCK_PRODUCTS } from '../data/mockProducts';
import { colors, typography, spacing } from '../theme';

export function FeedScreen() {
  const [products, setProducts] = useState<Product[]>(MOCK_PRODUCTS);
  const [deckEmpty, setDeckEmpty] = useState(false);
  const bottomSheetRef = useRef<BottomSheet>(null);
  const pendingProductRef = useRef<Product | null>(null);

  const handleSwipeRight = useCallback((product: Product) => {
    console.log('swipe_right', product.id);
  }, []);

  const handleSwipeLeft = useCallback((product: Product) => {
    pendingProductRef.current = product;
    bottomSheetRef.current?.snapToIndex(0);
  }, []);

  const handleRejectSelect = useCallback((reason: RejectReason) => {
    const product = pendingProductRef.current;
    if (product) {
      console.log(reason, product.id);
      pendingProductRef.current = null;
    }
    bottomSheetRef.current?.close();
  }, []);

  const handleTap = useCallback((product: Product) => {
    console.log('product_opened', product.id);
  }, []);

  const handleSave = useCallback((product: Product) => {
    console.log('save', product.id);
  }, []);

  const handleDeckEmpty = useCallback(() => {
    setDeckEmpty(true);
  }, []);

  const handleReload = useCallback(() => {
    setProducts([...MOCK_PRODUCTS]);
    setDeckEmpty(false);
  }, []);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.logo}>SwipeWear</Text>
      </View>

      {deckEmpty ? (
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
