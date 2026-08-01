import React, { useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Image,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius } from '../theme';
import { useDrop } from '../api';
import { Product } from '../types';
import { RootStackParamList } from '../navigation/types';

type Nav = NativeStackNavigationProp<RootStackParamList>;

function DropCard({ product, onPress }: { product: Product; onPress: () => void }) {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.85}>
      <View style={styles.cardImage}>
        <Image source={{ uri: product.imageUrls[0] }} style={styles.image} resizeMode="cover" />
        <View style={styles.badgeWrap}>
          <Text style={styles.badge}>{product.source.toUpperCase()}</Text>
        </View>
      </View>
      <View style={styles.cardInfo}>
        <Text style={styles.cardTitle} numberOfLines={1}>{product.title}</Text>
        <Text style={styles.cardPrice}>{product.price} {product.currency}</Text>
        {product.size && <Text style={styles.cardMeta}>{product.size}</Text>}
      </View>
    </TouchableOpacity>
  );
}

export function DropScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<Nav>();
  const { products: dropProducts, loading, reload } = useDrop();

  const handlePress = useCallback((product: Product) => {
    navigation.navigate('ProductDetail', { productId: product.id, product });
  }, [navigation]);

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
        <View style={styles.headerTop}>
          <Text style={styles.title}>Le Drop du jour</Text>
          <View style={styles.countChip}>
            <Ionicons name="time-outline" size={11} color={colors.textInverse} style={{ marginRight: 3 }} />
            <Text style={styles.countText}>ce soir à 19h</Text>
          </View>
        </View>
        <Text style={styles.subtitle}>Les meilleures pépites du jour, sélectionnées par ton IA</Text>
        {dropProducts.length > 0 && (
          <View style={styles.progressWrap}>
            <View style={styles.progressBg}>
              <View style={[styles.progressFill, { width: `${(dropProducts.length / 15) * 100}%` as any }]} />
            </View>
            <Text style={styles.progressLabel}>{dropProducts.length} / 15 PÉPITES</Text>
          </View>
        )}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.accent} size="large" />
        </View>
      ) : (
        <FlatList
          data={dropProducts}
          keyExtractor={p => p.id}
          numColumns={2}
          columnWrapperStyle={styles.row}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          renderItem={({ item }) => (
            <DropCard product={item} onPress={() => handlePress(item)} />
          )}
          ListEmptyComponent={
            <View style={styles.center}>
              <View style={styles.emptyIconWrap}>
                <Ionicons name="flash-outline" size={32} color={colors.disabled} />
              </View>
              <Text style={styles.emptyText}>Le Drop arrive ce soir à 19h</Text>
              <TouchableOpacity style={styles.reloadBtn} onPress={reload}>
                <Text style={styles.reloadText}>Actualiser</Text>
              </TouchableOpacity>
            </View>
          }
          ListFooterComponent={dropProducts.length > 0 ? (
            <View style={styles.footer}>
              <View style={styles.footerRow}>
                <Ionicons name="information-circle-outline" size={14} color={colors.textSecondary} style={{ marginRight: 6, marginTop: 1 }} />
                <Text style={styles.footerTitle}>Le Drop est épuisable — c'est voulu.</Text>
              </View>
              <Text style={styles.footerSub}>
                Reviens demain à 19h, ou crée une alerte pour être prévenu·e avant tout le monde.
              </Text>
            </View>
          ) : null}
        />
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
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  title: {
    ...typography.h1,
    color: colors.textPrimary,
    letterSpacing: -0.5,
  },
  countChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.error,
    borderRadius: borderRadius.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
  },
  countText: {
    color: colors.textInverse,
    fontSize: 11,
    fontWeight: '700',
  },
  subtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  progressWrap: {
    gap: 4,
  },
  progressBg: {
    height: 3,
    backgroundColor: colors.border,
    borderRadius: 99,
    overflow: 'hidden',
  },
  progressFill: {
    height: 3,
    backgroundColor: colors.accent,
    borderRadius: 99,
  },
  progressLabel: {
    ...typography.label,
    color: colors.textSecondary,
    fontSize: 10,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
    paddingVertical: spacing.xxl,
  },
  list: {
    paddingHorizontal: spacing.lg,
    paddingBottom: 120,
  },
  row: {
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  card: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
  },
  cardImage: {
    height: 150,
    backgroundColor: colors.cardBg,
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  badgeWrap: {
    position: 'absolute',
    top: spacing.xs,
    left: spacing.xs,
    backgroundColor: 'rgba(0,0,0,0.7)',
    borderRadius: borderRadius.sm,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  badge: {
    color: colors.textInverse,
    fontSize: 9,
    fontWeight: '700',
    opacity: 0.8,
  },
  cardInfo: {
    padding: spacing.sm,
  },
  cardTitle: {
    ...typography.caption,
    color: colors.textPrimary,
    fontWeight: '600',
    marginBottom: 2,
  },
  cardPrice: {
    ...typography.bodyBold,
    color: colors.accent,
    fontSize: 14,
  },
  cardMeta: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 1,
  },
  footer: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.lg,
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  footerTitle: {
    ...typography.bodyBold,
    color: colors.textPrimary,
    flex: 1,
  },
  footerSub: {
    ...typography.caption,
    color: colors.textSecondary,
    lineHeight: 16,
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
    marginBottom: spacing.lg,
  },
  reloadBtn: {
    backgroundColor: colors.accent,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  reloadText: {
    ...typography.bodyBold,
    color: colors.accentText,
  },
});
