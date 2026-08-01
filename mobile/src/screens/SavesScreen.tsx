import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Image,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { Product } from '../types';
import { useSaves } from '../context/SavesContext';

type Nav = NativeStackNavigationProp<RootStackParamList>;

const CATEGORIES = ['Tout', 'Hauts', 'Bas', 'Chaussures', 'Accessoires'];
type SortMode = 'recent' | 'price_asc' | 'price_desc';
const SORT_OPTIONS: { key: SortMode; label: string }[] = [
  { key: 'recent', label: 'Récent' },
  { key: 'price_asc', label: 'Prix ↑' },
  { key: 'price_desc', label: 'Prix ↓' },
];

function categoryMatch(product: Product, filter: string): boolean {
  if (filter === 'Tout') return true;
  const cat = product.category?.toLowerCase() ?? '';
  if (filter === 'Hauts') return cat.includes('top') || cat.includes('jacket') || cat.includes('shirt') || cat.includes('coat') || cat.includes('sweater');
  if (filter === 'Bas') return cat.includes('pants') || cat.includes('jeans') || cat.includes('shorts') || cat.includes('skirt');
  if (filter === 'Chaussures') return cat.includes('shoe') || cat.includes('sneaker') || cat.includes('boot') || cat.includes('footwear');
  if (filter === 'Accessoires') return cat.includes('bag') || cat.includes('hat') || cat.includes('watch') || cat.includes('accessories');
  return false;
}

function sortProducts(products: Product[], mode: SortMode): Product[] {
  if (mode === 'recent') return products;
  const sorted = [...products];
  if (mode === 'price_asc') sorted.sort((a, b) => a.price - b.price);
  if (mode === 'price_desc') sorted.sort((a, b) => b.price - a.price);
  return sorted;
}

function ProductCard({ product, onPress, onRemove }: { product: Product; onPress: () => void; onRemove: () => void }) {
  const soldOut = product.available === false;
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.85}>
      <View style={styles.cardImageWrap}>
        <Image source={{ uri: product.imageUrls[0] }} style={styles.cardImage} resizeMode="cover" />
        {soldOut && (
          <View style={styles.soldOutOverlay}>
            <View style={styles.soldOutBadge}>
              <Text style={styles.soldOutText}>Vendu</Text>
            </View>
          </View>
        )}
        <TouchableOpacity style={styles.removeBtn} onPress={onRemove} accessibilityLabel="Retirer du dressing">
          <Ionicons name="close" size={12} color={colors.textInverse} />
        </TouchableOpacity>
      </View>
      <View style={[styles.cardInfo, soldOut && styles.cardInfoSoldOut]}>
        <Text style={[styles.cardTitle, soldOut && styles.textSoldOut]} numberOfLines={1}>{product.title}</Text>
        <Text style={[styles.cardPrice, soldOut && styles.textSoldOut]}>{product.price} {product.currency}</Text>
        <Text style={styles.cardMeta}>{product.source}</Text>
      </View>
    </TouchableOpacity>
  );
}

export function SavesScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<Nav>();
  const { savedProducts, toggleSave } = useSaves();
  const [activeFilter, setActiveFilter] = useState('Tout');
  const [sortMode, setSortMode] = useState<SortMode>('recent');

  const filtered = useMemo(
    () => sortProducts(
      savedProducts.filter(p => categoryMatch(p, activeFilter)),
      sortMode,
    ),
    [savedProducts, activeFilter, sortMode],
  );

  const totalValue = savedProducts.reduce((sum, p) => sum + p.price, 0);

  if (savedProducts.length === 0) {
    return (
      <View style={styles.container}>
        <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
          <Text style={styles.title}>Mon dressing</Text>
        </View>
        <View style={styles.empty}>
          <View style={styles.emptyIconWrap}>
            <Ionicons name="shirt-outline" size={32} color={colors.disabled} />
          </View>
          <Text style={styles.emptyTitle}>Dressing vide</Text>
          <Text style={styles.emptySub}>Swipe à droite ou appuie sur le cœur pour ajouter des pièces ici</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
        <Text style={styles.title}>Mon dressing</Text>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{savedProducts.length}</Text>
          <Text style={styles.statLabel}>pièces</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{totalValue.toFixed(0)} €</Text>
          <Text style={styles.statLabel}>valeur totale</Text>
        </View>
        <View style={[styles.statCard, styles.statCardAccent]}>
          <Text style={[styles.statValue, styles.statValueAccent]}>{(totalValue * 0.6).toFixed(0)} €</Text>
          <Text style={styles.statLabel}>économisés</Text>
        </View>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filterRow}
      >
        {CATEGORIES.map(cat => (
          <TouchableOpacity
            key={cat}
            style={[styles.filterChip, activeFilter === cat && styles.filterChipActive]}
            onPress={() => setActiveFilter(cat)}
            activeOpacity={0.7}
          >
            <Text style={[styles.filterText, activeFilter === cat && styles.filterTextActive]}>
              {cat}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.sortRow}
      >
        {SORT_OPTIONS.map(opt => (
          <TouchableOpacity
            key={opt.key}
            style={[styles.sortChip, sortMode === opt.key && styles.sortChipActive]}
            onPress={() => setSortMode(opt.key)}
            activeOpacity={0.7}
          >
            <Text style={[styles.sortText, sortMode === opt.key && styles.sortTextActive]}>
              {opt.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <FlatList
        data={filtered}
        keyExtractor={p => p.id}
        numColumns={2}
        columnWrapperStyle={styles.row}
        contentContainerStyle={styles.grid}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <ProductCard
            product={item}
            onPress={() => navigation.navigate('ProductDetail', { productId: item.id, product: item })}
            onRemove={() => toggleSave(item)}
          />
        )}
        ListEmptyComponent={
          <View style={styles.emptyFilter}>
            <Text style={styles.emptySub}>Aucune pièce dans cette catégorie</Text>
          </View>
        }
      />
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
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: spacing.lg,
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    alignItems: 'center',
  },
  statCardAccent: {
    backgroundColor: colors.accentLight,
    borderWidth: 1,
    borderColor: colors.accentDark,
  },
  statValue: {
    ...typography.h3,
    color: colors.textPrimary,
    fontSize: 17,
    fontWeight: '700',
  },
  statValueAccent: {
    color: colors.accent,
  },
  statLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    fontSize: 10,
    marginTop: 2,
  },
  filterRow: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.sm,
    gap: spacing.xs,
  },
  filterChip: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: borderRadius.full,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterChipActive: {
    backgroundColor: colors.accent,
    borderColor: colors.accent,
  },
  filterText: {
    ...typography.label,
    color: colors.textSecondary,
    fontSize: 12,
    fontWeight: '500',
  },
  filterTextActive: {
    color: colors.accentText,
    fontWeight: '700',
  },
  sortRow: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    gap: spacing.xs,
  },
  sortChip: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: borderRadius.full,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
  },
  sortChipActive: {
    borderColor: colors.textPrimary,
    backgroundColor: colors.textPrimary,
  },
  sortText: {
    ...typography.label,
    color: colors.textSecondary,
    fontSize: 11,
    fontWeight: '500',
  },
  sortTextActive: {
    color: colors.textInverse,
    fontWeight: '600',
  },
  grid: {
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
  cardImageWrap: {
    height: 140,
    position: 'relative',
    backgroundColor: colors.cardBg,
  },
  cardImage: {
    width: '100%',
    height: '100%',
  },
  soldOutOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255,255,255,0.6)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  soldOutBadge: {
    backgroundColor: colors.textPrimary,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: borderRadius.sm,
  },
  soldOutText: {
    color: colors.textInverse,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  removeBtn: {
    position: 'absolute',
    top: spacing.xs,
    right: spacing.xs,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(0,0,0,0.65)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardInfo: {
    padding: spacing.sm,
  },
  cardInfoSoldOut: {
    opacity: 0.5,
  },
  cardTitle: {
    ...typography.caption,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  cardPrice: {
    ...typography.bodyBold,
    color: colors.accent,
    fontSize: 14,
    marginTop: 2,
  },
  cardMeta: {
    ...typography.caption,
    color: colors.textSecondary,
    fontSize: 10,
    marginTop: 1,
  },
  textSoldOut: {
    textDecorationLine: 'line-through',
    color: colors.textSecondary,
  },
  empty: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  emptyFilter: {
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
  emptyTitle: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  emptySub: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
});
