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
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { Badge, Button } from '../components';
import { MOCK_PRODUCTS } from '../data/mockProducts';
import { Product } from '../types';
import { useSaves } from '../context/SavesContext';

const { width } = Dimensions.get('window');

interface Props {
  navigation: NativeStackNavigationProp<RootStackParamList, 'ProductDetail'>;
  route: RouteProp<RootStackParamList, 'ProductDetail'>;
}

export function ProductDetailScreen({ navigation, route }: Props) {
  const { productId } = route.params;
  const product = MOCK_PRODUCTS.find((p) => p.id === productId);
  const { isSaved, toggleSave } = useSaves();
  const [activeImageIndex, setActiveImageIndex] = useState(0);

  useEffect(() => {
    console.log('open', productId);
  }, [productId]);

  if (!product) {
    return (
      <View style={styles.container}>
        <View style={styles.soldBanner}>
          <Text style={styles.soldText}>Product unavailable</Text>
        </View>
        <View style={styles.soldContent}>
          <Text style={styles.soldTitle}>This item is no longer available</Text>
          <Text style={styles.soldSubtitle}>Check out similar items in your feed</Text>
          <Button title="Back to feed" onPress={() => navigation.goBack()} />
        </View>
      </View>
    );
  }

  const saved = isSaved(product.id);

  const conditionLabel: Record<string, { text: string; variant: 'success' | 'warning' | 'default' }> = {
    new: { text: 'New', variant: 'success' },
    like_new: { text: 'Like new', variant: 'success' },
    good: { text: 'Good', variant: 'default' },
    fair: { text: 'Fair', variant: 'warning' },
  };
  const cond = conditionLabel[product.condition] ?? { text: product.condition, variant: 'default' as const };

  const handleBuy = () => {
    const url = `https://www.ebay.com/itm/${product.id}`;
    Linking.openURL(url);
  };

  const handleSave = () => {
    toggleSave(product);
    console.log(saved ? 'unsave' : 'save', product.id);
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
              <Image source={{ uri: item }} style={styles.image} />
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
          <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
            <Text style={styles.backText}>←</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.heartButton} onPress={handleSave}>
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
          <Text style={styles.price}>{product.price} {product.currency}</Text>
          <Text style={styles.category}>{product.category}</Text>
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <Button title="Buy" onPress={handleBuy} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
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
    color: colors.primary,
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
