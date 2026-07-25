import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  Dimensions,
  TouchableOpacity,
  FlatList,
  Linking,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { Badge, Button } from '../components';

import { Product } from '../types';
import { useSaves } from '../context/SavesContext';
import { usePostEvent, useProduct } from '../api';

const { width } = Dimensions.get('window');

interface Props {
  navigation: NativeStackNavigationProp<RootStackParamList, 'ProductDetail'>;
  route: RouteProp<RootStackParamList, 'ProductDetail'>;
}

export function ProductDetailScreen({ navigation, route }: Props) {
  const { productId, product: passedProduct } = route.params;
  // The fallback used to be a hardcoded MOCK_PRODUCTS lookup, so opening an
  // item from the wardrobe or an alert showed an invented product under a real
  // id. The request is skipped when the feed already handed us the product.
  const { product: fetched, loading } = useProduct(productId, Boolean(passedProduct));
  const product: Product | undefined = passedProduct ?? fetched ?? undefined;
  const { isSaved, toggleSave } = useSaves();
  const postEvent = usePostEvent();
  const [activeImageIndex, setActiveImageIndex] = useState(0);

  useEffect(() => {
    postEvent(productId, 'open');
  }, [productId, postEvent]);

  if (loading) {
    return (
      <View style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color={colors.accent} />
      </View>
    );
  }

  if (!product) {
    return (
      <View style={styles.container}>
        <View style={styles.soldBanner}>
          <Text style={styles.soldText}>Produit indisponible</Text>
        </View>
        <View style={styles.soldContent}>
          <Text style={styles.soldTitle}>Cet article n'est plus en ligne</Text>
          <Text style={styles.soldSubtitle}>Regarde des pièces similaires dans ton feed</Text>
          <Button title="Retour au feed" onPress={() => navigation.goBack()} />
        </View>
      </View>
    );
  }

  const saved = isSaved(product.id);

  const conditionLabel: Record<string, { text: string; variant: 'success' | 'warning' | 'default' }> = {
    new: { text: 'Neuf', variant: 'success' },
    like_new: { text: 'Comme neuf', variant: 'success' },
    good: { text: 'Bon état', variant: 'default' },
    fair: { text: 'État correct', variant: 'warning' },
  };
  const cond = conditionLabel[product.condition] ?? { text: product.condition, variant: 'default' as const };

  const handleBuy = () => {
    // The URL used to be built as ebay.com/itm/<product.id>, but product.id is
    // our internal key ("ebay-v1|127396173312|428490506"), not an eBay item
    // number — every Buy tap landed on a 404. The API returns the seller's
    // real listing URL, affiliate-wrapped when that is switched on.
    if (!product.url) return;
    Linking.openURL(product.url);
  };

  const handleViewOffers = () => {
    navigation.navigate('PriceLadder', { productId: product.id });
  };

  const handleSave = () => {
    toggleSave(product);
    postEvent(product.id, 'save');
  };

  return (
    <View style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.imageContainer}>
          <FlatList
            data={product.imageUrls}
            horizontal
            pagingEnabled
            showsHorizontalScrollIndicator={false}
            onMomentumScrollEnd={(e) => {
              const index = Math.round(e.nativeEvent.contentOffset.x / width);
              setActiveImageIndex(index);
            }}
            renderItem={({ item }) => (
              <Image source={{ uri: item }} style={styles.image} accessibilityIgnoresInvertColors />
            )}
            keyExtractor={(_, i) => i.toString()}
          />
          {product.imageUrls.length > 1 && (
            <View style={styles.pagination}>
              {product.imageUrls.map((_, i) => (
                <View
                  key={i}
                  style={[styles.dot, i === activeImageIndex && styles.dotActive]}
                />
              ))}
            </View>
          )}
          <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()} accessibilityRole="button" accessibilityLabel="Go back">
            <Text style={styles.backText}>←</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.heartButton} onPress={handleSave} accessibilityRole="button" accessibilityLabel={saved ? 'Remove from saves' : 'Save item'}>
            <Text style={styles.heartText}>{saved ? '❤️' : '🤍'}</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.details}>
          <View style={styles.badges}>
            <Badge label={cond.text} variant={cond.variant} />
            {product.size && <Badge label={product.size} />}
            <Badge label={product.source.toUpperCase()} />
          </View>

          <Text style={styles.brand}>{product.brand}</Text>
          <Text style={styles.title}>{product.title}</Text>
          <Text style={styles.price}>{product.price.toFixed(2)} {product.currency}</Text>
          <Text style={styles.category}>{product.category}</Text>
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <Button title="Voir les offres" onPress={handleViewOffers} />
        <Button
          title="Acheter"
          variant="outline"
          onPress={handleBuy}
          disabled={!product.url}
          style={styles.buyButton}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  centered: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  imageContainer: {
    width,
    height: width * 1.25,
    backgroundColor: colors.surface,
  },
  image: {
    width,
    height: width * 1.25,
  },
  pagination: {
    position: 'absolute',
    bottom: spacing.md,
    alignSelf: 'center',
    flexDirection: 'row',
    gap: spacing.xs,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.disabled,
  },
  dotActive: {
    backgroundColor: colors.primary,
  },
  backButton: {
    position: 'absolute',
    top: spacing.xxl,
    left: spacing.md,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.overlay,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backText: {
    color: colors.textInverse,
    fontSize: 20,
  },
  heartButton: {
    position: 'absolute',
    top: spacing.xxl,
    right: spacing.md,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.overlay,
    alignItems: 'center',
    justifyContent: 'center',
  },
  heartText: {
    fontSize: 20,
  },
  details: {
    padding: spacing.lg,
  },
  badges: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  brand: {
    ...typography.label,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  title: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  price: {
    ...typography.h1,
    color: colors.accentDark,
    marginBottom: spacing.sm,
  },
  category: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  footer: {
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  buyButton: {
    marginTop: spacing.sm,
  },
  soldBanner: {
    backgroundColor: colors.error,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxl,
  },
  soldText: {
    ...typography.bodyBold,
    color: colors.textInverse,
    textAlign: 'center',
  },
  soldContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  soldTitle: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  soldSubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
});
