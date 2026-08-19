import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Image,
  TouchableOpacity,
  Linking,
  RefreshControl,
  ActivityIndicator,
  Share,
  TextInput,
} from 'react-native';
import { Directory, File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { Badge, Button } from '../components';
import { trackEvent } from '../analytics';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { useLadder, useAlerts, ApiError, API_BASE_URL } from '../api';
import type { LadderEntry } from '../api';

interface Props {
  navigation: NativeStackNavigationProp<RootStackParamList, 'PriceLadder'>;
  route: RouteProp<RootStackParamList, 'PriceLadder'>;
}

const conditionLabels: Record<string, { text: string; variant: 'success' | 'default' | 'warning' }> = {
  new: { text: 'Neuf', variant: 'success' },
  like_new: { text: 'Comme neuf', variant: 'success' },
  good: { text: 'Bon état', variant: 'default' },
  fair: { text: 'État correct', variant: 'warning' },
};

const conditionRank: Record<string, number> = {
  fair: 0,
  good: 1,
  like_new: 2,
  new: 3,
};

export function PriceLadderScreen({ navigation, route }: Props) {
  const { productId } = route.params;
  // The list used to be invented from MOCK_PRODUCTS: two fabricated offers
  // around a hardcoded item, and a saving that was arithmetic on fiction.
  const { entries, savingsPct, loading, error, reload } = useLadder(productId);
  const { create: createAlert } = useAlerts();
  const [alertLabel, setAlertLabel] = useState('Créer une alerte');
  const [alertDone, setAlertDone] = useState(false);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [minimumCondition, setMinimumCondition] = useState<string>('');
  const [minimumPrice, setMinimumPrice] = useState('');
  const [maximumPrice, setMaximumPrice] = useState('');

  useEffect(() => {
    trackEvent({ name: 'ladder_viewed', properties: { product_id: productId } });
  }, [productId]);

  // The button in the empty state was onPress={() => {}} — no comparable offer
  // today is exactly when someone wants to be told about one later.
  const handleCreateAlert = useCallback(async () => {
    try {
      await createAlert({
        alert_type: 'specific_item',
        label: `Offre pour ${productId}`,
        reference_product_id: productId,
      });
      trackEvent({ name: 'alert_created', properties: { alert_type: 'specific_item', product_id: productId } });
      setAlertLabel('Alerte créée');
      setAlertDone(true);
    } catch (e) {
      setAlertLabel(
        e instanceof ApiError && e.status === 403
          ? 'Ton alerte gratuite est déjà active'
          : 'Échec — réessayer',
      );
    }
  }, [createAlert, productId]);

  const handleShare = useCallback(async () => {
    trackEvent({ name: 'share_card_generated', properties: { product_id: productId } });
    const pct = savingsPct ? Math.round(savingsPct) : 0;
    const shareUrl = `${API_BASE_URL}/share/${productId}${pct > 0 ? `?savings_pct=${pct}` : ''}`;
    try {
      if (await Sharing.isAvailableAsync()) {
        const destination = new Directory(Paths.cache, 'swipewear-share');
        destination.create({ idempotent: true, intermediates: true });
        const image = await File.downloadFileAsync(shareUrl, destination);
        await Sharing.shareAsync(image.uri, {
          mimeType: 'image/png',
          dialogTitle: 'Partager ma pépite SwipeWear',
        });
        return;
      }

      await Share.share({
        message: pct > 0
          ? `J'ai trouvé cette pièce avec -${pct}% vs le neuf sur SwipeWear ! ${shareUrl}`
          : `Regarde cette pièce sur SwipeWear ! ${shareUrl}`,
      });
    } catch {
      // User cancelled
    }
  }, [productId, savingsPct]);

  const handleOfferPress = useCallback((entry: LadderEntry, position: number) => {
    trackEvent({
      name: 'outbound_click',
      properties: {
        product_id: entry.productId,
        source: entry.source,
        price: entry.price,
        position,
      },
    });
    Linking.openURL(entry.affiliateUrl);
  }, []);

  const sources = useMemo(
    () => [...new Set(entries.map((entry) => entry.source))].sort(),
    [entries],
  );
  const filteredEntries = useMemo(() => {
    const min = Number(minimumPrice.replace(',', '.'));
    const max = Number(maximumPrice.replace(',', '.'));
    const hasMin = minimumPrice.trim() !== '' && Number.isFinite(min);
    const hasMax = maximumPrice.trim() !== '' && Number.isFinite(max);
    const minRank = minimumCondition ? conditionRank[minimumCondition] : undefined;
    return entries.filter((entry) => (
      (selectedSources.length === 0 || selectedSources.includes(entry.source))
      && (minRank === undefined || (conditionRank[entry.condition] ?? -1) >= minRank)
      && (!hasMin || entry.price >= min)
      && (!hasMax || entry.price <= max)
    ));
  }, [entries, maximumPrice, minimumCondition, minimumPrice, selectedSources]);

  const minPrice = filteredEntries.length > 0 ? filteredEntries[0].price : 0;
  const maxPrice = filteredEntries.length > 0 ? filteredEntries[filteredEntries.length - 1].price : 0;
  const toggleSource = useCallback((source: string) => {
    setSelectedSources((current) => (
      current.includes(source)
        ? current.filter((value) => value !== source)
        : [...current, source]
    ));
  }, []);
  const resetFilters = useCallback(() => {
    setSelectedSources([]);
    setMinimumCondition('');
    setMinimumPrice('');
    setMaximumPrice('');
  }, []);

  const renderItem = ({ item, index }: { item: LadderEntry; index: number }) => {
    const cond = conditionLabels[item.condition] ?? { text: item.condition, variant: 'default' as const };
    return (
      <TouchableOpacity style={styles.row} onPress={() => handleOfferPress(item, index + 1)} activeOpacity={0.7} accessibilityRole="button" accessibilityLabel={`${item.title}, ${item.price} ${item.currency} sur ${item.source}`}>
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
          <Text style={styles.rowPrice}>{item.price.toFixed(2)} {item.currency}</Text>
          <Text style={styles.rowArrow}>→</Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton} accessibilityRole="button" accessibilityLabel="Retour">
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Échelle de prix</Text>
        <TouchableOpacity onPress={handleShare} style={styles.backButton} accessibilityRole="button" accessibilityLabel="Partager">
          <Ionicons name="share-outline" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      {entries.length > 0 && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>
            {filteredEntries.length > 0
              ? `De ${minPrice.toFixed(2)} € à ${maxPrice.toFixed(2)} €${savingsPct ? ` — jusqu'à ${Math.round(savingsPct)} % d'économie` : ''}`
              : 'Aucune offre ne correspond aux filtres'}
          </Text>
        </View>
      )}

      {loading ? (
        <View style={styles.emptyState}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : error ? (
        // "No comparable offer" and "the request failed" mean different things
        // to someone deciding whether to buy.
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>Comparaison indisponible</Text>
          <Text style={styles.emptySubtitle}>
            Impossible de récupérer les offres pour le moment.
          </Text>
          <Button title="Réessayer" onPress={reload} style={styles.alertButton} />
        </View>
      ) : entries.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>Aucune offre comparable trouvée</Text>
          <Text style={styles.emptySubtitle}>
            Nous n'avons pas encore d'offres similaires pour ce produit
          </Text>
          <Button
            title={alertLabel}
            variant="outline"
            onPress={handleCreateAlert}
            disabled={alertDone}
            style={styles.alertButton}
          />
        </View>
      ) : (
        <FlatList
          data={filteredEntries}
          renderItem={renderItem}
          keyExtractor={(item) => item.productId}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          ListHeaderComponent={
            <View style={styles.filters}>
              <Text style={styles.filterTitle}>Filtrer les offres</Text>
              <View style={styles.filterRow}>
                {sources.map((source) => {
                  const active = selectedSources.includes(source);
                  return (
                    <TouchableOpacity
                      key={source}
                      onPress={() => toggleSource(source)}
                      style={[styles.filterChip, active && styles.filterChipActive]}
                    >
                      <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{source.toUpperCase()}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
              <View style={styles.filterRow}>
                {['', 'good', 'like_new', 'new'].map((condition) => {
                  const active = minimumCondition === condition;
                  const label = condition ? `État min. ${conditionLabels[condition].text}` : 'Tout état';
                  return (
                    <TouchableOpacity
                      key={condition || 'all'}
                      onPress={() => setMinimumCondition(condition)}
                      style={[styles.filterChip, active && styles.filterChipActive]}
                    >
                      <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{label}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
              <View style={styles.priceFilterRow}>
                <TextInput
                  value={minimumPrice}
                  onChangeText={setMinimumPrice}
                  keyboardType="decimal-pad"
                  placeholder="Prix min."
                  placeholderTextColor={colors.textSecondary}
                  style={styles.priceInput}
                />
                <TextInput
                  value={maximumPrice}
                  onChangeText={setMaximumPrice}
                  keyboardType="decimal-pad"
                  placeholder="Prix max."
                  placeholderTextColor={colors.textSecondary}
                  style={styles.priceInput}
                />
                <TouchableOpacity onPress={resetFilters} style={styles.resetFilters}>
                  <Text style={styles.resetFiltersText}>Réinitialiser</Text>
                </TouchableOpacity>
              </View>
              {filteredEntries.length === 0 && (
                <Text style={styles.noFilteredEntries}>Aucune offre avec ces filtres.</Text>
              )}
            </View>
          }
          refreshControl={
            <RefreshControl refreshing={loading} onRefresh={reload} tintColor={colors.primary} />
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
  filters: {
    marginBottom: spacing.md,
  },
  filterTitle: {
    ...typography.bodyBold,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  filterRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
    marginBottom: spacing.xs,
  },
  filterChip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
  },
  filterChipActive: {
    borderColor: colors.accent,
    backgroundColor: colors.accent,
  },
  filterChipText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  filterChipTextActive: {
    color: colors.accentText,
  },
  priceFilterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginTop: spacing.xs,
  },
  priceInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.sm,
    color: colors.textPrimary,
    paddingHorizontal: spacing.sm,
    paddingVertical: 7,
    ...typography.caption,
  },
  resetFilters: {
    paddingVertical: 7,
  },
  resetFiltersText: {
    ...typography.caption,
    color: colors.accentDark,
    textDecorationLine: 'underline',
  },
  noFilteredEntries: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.sm,
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
    color: colors.accentDark,
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
