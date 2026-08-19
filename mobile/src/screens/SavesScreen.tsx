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
const AVAILABILITY_OPTIONS = [
  { key: 'all', label: 'Toutes' },
  { key: 'available', label: 'Disponibles' },
  { key: 'sold', label: 'Vendues' },
] as const;
type AvailabilityFilter = typeof AVAILABILITY_OPTIONS[number]['key'];
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

function availabilityMatch(product: Product, filter: AvailabilityFilter): boolean {
  if (filter === 'all') return true;
  return filter === 'available' ? product.available !== false : product.available === false;
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
        <Text style={[styles.cardBrand, soldOut && styles.textSoldOut]} numberOfLines={1}>{product.brand || product.source}</Text>
        <Text style={[styles.cardTitle, soldOut && styles.textSoldOut]} numberOfLines={2}>{product.title}</Text>
        <View style={styles.cardFooter}>
          <Text style={[styles.cardPrice, soldOut && styles.textSoldOut]}>{product.price.toFixed(0)} €</Text>
          <Text style={styles.cardMeta}>{soldOut ? 'Vendu' : 'Disponible'}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

export function SavesScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<Nav>();
  const { savedProducts, toggleSave } = useSaves();
  const [activeFilter, setActiveFilter] = useState('Tout');
  const [availabilityFilter, setAvailabilityFilter] = useState<AvailabilityFilter>('all');
  const [sortMode, setSortMode] = useState<SortMode>('recent');

  const filtered = useMemo(
    () => sortProducts(
      savedProducts.filter(
        (product) => categoryMatch(product, activeFilter)
          && availabilityMatch(product, availabilityFilter),
      ),
      sortMode,
    ),
    [savedProducts, activeFilter, availabilityFilter, sortMode],
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
          <Text style={styles.emptySub}>Balaye vers le haut ou appuie sur le cœur pour garder tes pièces préférées.</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
        <Text style={styles.eyebrow}>Ta sélection</Text>
        <Text style={styles.title}>Mon dressing</Text>
      </View>

      <View style={styles.summaryCard}>
        <View style={styles.summaryIcon}>
          <Ionicons name="shirt" size={20} color={colors.accentText} />
        </View>
        <View style={styles.summaryCopy}>
          <Text style={styles.summaryTitle}>{savedProducts.length} {savedProducts.length === 1 ? 'pièce sauvegardée' : 'pièces sauvegardées'}</Text>
          <Text style={styles.summarySub}>Tes trouvailles, au même endroit.</Text>
        </View>
        <View style={styles.summaryValueWrap}>
          <Text style={styles.summaryValue}>{totalValue.toFixed(0)} €</Text>
          <Text style={styles.summaryValueLabel}>valeur</Text>
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

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.controlsRow}>
        {AVAILABILITY_OPTIONS.map((option) => (
          <TouchableOpacity
            key={option.key}
            style={[styles.sortChip, availabilityFilter === option.key && styles.sortChipActive]}
            onPress={() => setAvailabilityFilter(option.key)}
            activeOpacity={0.7}
          >
            <Text style={[styles.sortText, availabilityFilter === option.key && styles.sortTextActive]}>
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
        <View style={styles.controlDivider} />
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
    paddingBottom: spacing.sm,
  },
  eyebrow: {
    ...typography.label,
    color: colors.accentDark,
    marginBottom: 2,
  },
  title: {
    ...typography.h1,
    color: colors.textPrimary,
    letterSpacing: -0.5,
  },
  summaryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    marginHorizontal: spacing.lg,
    marginBottom: spacing.lg,
    backgroundColor: colors.textPrimary,
    borderRadius: borderRadius.md,
  },
  summaryIcon: {
    width: 42,
    height: 42,
    borderRadius: 14,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacing.md,
  },
  summaryCopy: {
    flex: 1,
    marginLeft: spacing.sm,
  },
  summaryTitle: {
    ...typography.captionBold,
    color: colors.textInverse,
  },
  summarySub: {
    ...typography.caption,
    color: '#B9B5AA',
    marginTop: 1,
  },
  summaryValueWrap: {
    alignItems: 'flex-end',
    marginRight: spacing.md,
  },
  summaryValue: {
    ...typography.h3,
    color: colors.accent,
  },
  summaryValueLabel: {
    ...typography.caption,
    color: '#B9B5AA',
    fontSize: 11,
  },
  filterRow: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    gap: spacing.sm,
  },
  filterChip: {
    paddingHorizontal: 13,
    paddingVertical: 8,
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
  controlsRow: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    gap: spacing.sm,
    alignItems: 'center',
  },
  sortChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
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
    fontSize: 10,
    fontWeight: '500',
  },
  sortTextActive: {
    color: colors.textInverse,
    fontWeight: '600',
  },
  controlDivider: {
    height: 26,
    width: 1,
    backgroundColor: colors.borderStrong,
    marginHorizontal: 2,
  },
  grid: {
    paddingHorizontal: spacing.lg,
    paddingBottom: 120,
  },
  row: {
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  card: {
    width: '48.5%',
    flexGrow: 0,
    backgroundColor: colors.surfaceElevated,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardImageWrap: {
    height: 210,
    position: 'relative',
    backgroundColor: colors.cardBg,
  },
  cardImage: {
    width: '100%',
    height: '100%',
  },
  soldOutOverlay: {
    ...StyleSheet.absoluteFill,
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
    padding: spacing.md,
  },
  cardInfoSoldOut: {
    opacity: 0.5,
  },
  cardTitle: {
    ...typography.caption,
    color: colors.textPrimary,
    fontWeight: '500',
    lineHeight: 17,
    marginTop: 2,
    minHeight: 34,
  },
  cardBrand: {
    ...typography.label,
    color: colors.textSecondary,
    fontSize: 10,
  },
  cardFooter: {
    marginTop: spacing.sm,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardPrice: {
    ...typography.bodyBold,
    color: colors.accent,
    fontSize: 15,
  },
  cardMeta: {
    ...typography.caption,
    color: colors.textSecondary,
    fontSize: 10,
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
