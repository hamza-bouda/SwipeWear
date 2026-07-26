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
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { Badge, Button } from '../components';
import { trackEvent } from '../analytics';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { useLadder, useAlerts, ApiError } from '../api';
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

export function PriceLadderScreen({ navigation, route }: Props) {
  const { productId } = route.params;
  // The list used to be invented from MOCK_PRODUCTS: two fabricated offers
  // around a hardcoded item, and a saving that was arithmetic on fiction.
  const { entries, savingsPct, loading, error, reload } = useLadder(productId);
  const { create: createAlert } = useAlerts();
  const [alertLabel, setAlertLabel] = useState('Créer une alerte');
  const [alertDone, setAlertDone] = useState(false);

  // The button in the empty state was onPress={() => {}} — no comparable offer
  // today is exactly when someone wants to be told about one later.
  const handleCreateAlert = useCallback(async () => {
    try {
      await createAlert({
        alert_type: 'specific_item',
        label: `Offre pour ${productId}`,
        reference_product_id: productId,
      });
      setAlertLabel('Alerte créée');
      setAlertDone(true);
    } catch (e) {
      setAlertLabel(
        e instanceof ApiError && e.status === 403
          ? 'Limite de 3 alertes atteinte'
          : 'Échec — réessayer',
      );
    }
  }, [createAlert, productId]);

  const handleOfferPress = useCallback((entry: LadderEntry) => {
    trackEvent({
      name: 'offer_clicked',
      properties: { product_id: entry.productId, url: entry.affiliateUrl },
    });
    Linking.openURL(entry.affiliateUrl);
  }, []);

  // Entries arrive sorted by price, so the ends are the range. The saving
  // comes from the server rather than being recomputed here — one definition,
  // one number, whatever the client does with the list.
  const minPrice = entries.length > 0 ? entries[0].price : 0;
  const maxPrice = entries.length > 0 ? entries[entries.length - 1].price : 0;

  const renderItem = ({ item }: { item: LadderEntry }) => {
    const cond = conditionLabels[item.condition] ?? { text: item.condition, variant: 'default' as const };
    return (
      <TouchableOpacity style={styles.row} onPress={() => handleOfferPress(item)} activeOpacity={0.7} accessibilityRole="button" accessibilityLabel={`${item.title}, ${item.price} ${item.currency} on ${item.source}`}>
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
        <View style={styles.backButton} />
      </View>

      {entries.length > 0 && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>
            De {minPrice.toFixed(2)} € à {maxPrice.toFixed(2)} €{savingsPct ? ` — jusqu'à ${Math.round(savingsPct)} % d'économie` : ''}
          </Text>
        </View>
      )}

      {loading ? (
        <View style={styles.emptyState}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : error ? (
        // "Aucune offre comparable" and "the request failed" mean different things
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
          data={entries}
          renderItem={renderItem}
          keyExtractor={(item) => item.productId}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
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
