import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Image,
  TouchableOpacity,
  Linking,
  RefreshControl,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { Badge, Button } from '../components';
import { trackEvent } from '../analytics';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { MOCK_PRODUCTS } from '../data/mockProducts';

interface LadderEntry {
  productId: string;
  title: string;
  price: number;
  currency: string;
  source: string;
  condition: string;
  isNew: boolean;
  confidence: 'exact' | 'similar';
  imageUrl: string | null;
  affiliateUrl: string;
}

interface Props {
  navigation: NativeStackNavigationProp<RootStackParamList, 'PriceLadder'>;
  route: RouteProp<RootStackParamList, 'PriceLadder'>;
}

function buildMockLadder(productId: string): LadderEntry[] {
  const source = MOCK_PRODUCTS.find((p) => p.id === productId);
  if (!source) return [];

  const entries: LadderEntry[] = [
    {
      productId: `${productId}-used-1`,
      title: `${source.title} — Occasion`,
      price: Math.round(source.price * 0.5),
      currency: source.currency,
      source: 'ebay',
      condition: 'good',
      isNew: false,
      confidence: 'exact',
      imageUrl: source.imageUrls[0],
      affiliateUrl: `https://www.ebay.com/itm/${productId}-used`,
    },
    {
      productId: `${productId}-used-2`,
      title: `${source.title} — Comme neuf`,
      price: Math.round(source.price * 0.7),
      currency: source.currency,
      source: 'ebay',
      condition: 'like_new',
      isNew: false,
      confidence: 'exact',
      imageUrl: source.imageUrls[0],
      affiliateUrl: `https://www.ebay.com/itm/${productId}-likenew`,
    },
    {
      productId: `${productId}-new`,
      title: `${source.title} — Neuf`,
      price: Math.round(source.price * 1.4),
      currency: source.currency,
      source: 'awin',
      condition: 'new',
      isNew: true,
      confidence: 'exact',
      imageUrl: source.imageUrls[0],
      affiliateUrl: `https://shop.example.com/${productId}-new`,
    },
  ];
  return entries.sort((a, b) => a.price - b.price);
}

const conditionLabels: Record<string, { text: string; variant: 'success' | 'warning' | 'default' }> = {
  new: { text: 'Neuf', variant: 'success' },
  like_new: { text: 'Comme neuf', variant: 'success' },
  good: { text: 'Bon état', variant: 'default' },
  fair: { text: 'État correct', variant: 'warning' },
};

export function PriceLadderScreen({ navigation, route }: Props) {
  const { productId } = route.params;
  const [entries, setEntries] = useState<LadderEntry[]>(() => buildMockLadder(productId));
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    setTimeout(() => {
      setEntries(buildMockLadder(productId));
      setRefreshing(false);
    }, 800);
  }, [productId]);

  const handleOfferPress = useCallback((entry: LadderEntry) => {
    trackEvent({
      name: 'offer_clicked',
      properties: { product_id: entry.productId, url: entry.affiliateUrl },
    });
    Linking.openURL(entry.affiliateUrl);
  }, []);

  const minPrice = entries.length > 0 ? entries[0].price : 0;
  const maxPrice = entries.length > 0 ? entries[entries.length - 1].price : 0;
  const savingsPct = maxPrice > 0 ? Math.round((1 - minPrice / maxPrice) * 100) : 0;

  const renderItem = ({ item }: { item: LadderEntry }) => {
    const cond = conditionLabels[item.condition] ?? { text: item.condition, variant: 'default' as const };
    return (
      <TouchableOpacity style={styles.row} onPress={() => handleOfferPress(item)} activeOpacity={0.7}>
        {item.imageUrl ? (
          <Image source={{ uri: item.imageUrl }} style={styles.thumbnail} />
        ) : (
          <View style={[styles.thumbnail, styles.thumbnailPlaceholder]} />
        )}
        <View style={styles.rowContent}>
          <Text style={styles.rowTitle} numberOfLines={1}>{item.title}</Text>
          <View style={styles.rowBadges}>
            <Badge label={item.isNew ? 'Neuf' : 'Occasion'} variant={item.isNew ? 'success' : 'default'} />
            <Badge label={cond.text} variant={cond.variant} />
            <Badge label={item.source.toUpperCase()} />
          </View>
          <Text style={styles.rowConfidence}>
            {item.confidence === 'exact' ? 'Même pièce' : 'Style similaire'}
          </Text>
        </View>
        <View style={styles.rowPriceCol}>
          <Text style={styles.rowPrice}>{item.price} {item.currency}</Text>
          <Text style={styles.rowArrow}>→</Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Échelle de prix</Text>
        <View style={styles.backButton} />
      </View>

      {entries.length > 0 && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>
            De {minPrice} € (occasion) à {maxPrice} € (neuf) — jusqu'à {savingsPct} % d'économie
          </Text>
        </View>
      )}

      {entries.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>Aucune offre comparable trouvée</Text>
          <Text style={styles.emptySubtitle}>
            Nous n'avons pas encore d'offres similaires pour ce produit
          </Text>
          <Button
            title="Créer une alerte"
            variant="outline"
            onPress={() => {}}
            style={styles.alertButton}
          />
        </View>
      ) : (
        <FlatList
          data={entries}
          renderItem={renderItem}
          keyExtractor={(item) => item.productId}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
          }
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 60,
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.md,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backText: {
    fontSize: 24,
    color: colors.textPrimary,
  },
  headerTitle: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  summary: {
    backgroundColor: colors.surface,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    marginHorizontal: spacing.md,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
  },
  summaryText: {
    ...typography.bodyBold,
    color: colors.textPrimary,
    textAlign: 'center',
  },
  list: {
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.xxl,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    marginBottom: spacing.sm,
  },
  thumbnail: {
    width: 64,
    height: 64,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.border,
  },
  thumbnailPlaceholder: {
    backgroundColor: colors.disabled,
  },
  rowContent: {
    flex: 1,
    marginLeft: spacing.sm,
    marginRight: spacing.sm,
  },
  rowTitle: {
    ...typography.bodyBold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  rowBadges: {
    flexDirection: 'row',
    gap: 4,
    flexWrap: 'wrap',
    marginBottom: 2,
  },
  rowConfidence: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  rowPriceCol: {
    alignItems: 'flex-end',
    minWidth: 70,
  },
  rowPrice: {
    ...typography.h3,
    color: colors.accent,
  },
  rowArrow: {
    ...typography.caption,
    color: colors.textSecondary,
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
    textAlign: 'center',
  },
  emptySubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
    textAlign: 'center',
  },
  alertButton: {
    minWidth: 180,
  },
});
