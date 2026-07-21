import React from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
} from 'react-native';
import { Product } from '../types';
import { Badge } from './Badge';
import { colors, typography, spacing, borderRadius } from '../theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
export const CARD_WIDTH = SCREEN_WIDTH - spacing.lg * 2;
export const CARD_HEIGHT = CARD_WIDTH * 1.35;

interface SwipeCardProps {
  product: Product;
  onTap?: () => void;
  onSave?: () => void;
}

const conditionLabels: Record<string, string> = {
  new: 'New',
  like_new: 'Like new',
  good: 'Good',
  fair: 'Fair',
};

export function SwipeCard({ product, onTap, onSave }: SwipeCardProps) {
  return (
    <TouchableOpacity activeOpacity={0.95} onPress={onTap} style={styles.card}>
      <Image
        source={{ uri: product.imageUrls[0] }}
        style={styles.image}
        resizeMode="cover"
      />
      <View style={styles.overlay}>
        <View style={styles.badges}>
          <Badge
            label={conditionLabels[product.condition] ?? product.condition}
            variant={product.condition === 'new' ? 'success' : 'default'}
          />
          {product.size && <Badge label={product.size} style={styles.sizeBadge} />}
        </View>
        <View style={styles.info}>
          <Text style={styles.brand}>{product.brand}</Text>
          <Text style={styles.title} numberOfLines={1}>
            {product.title}
          </Text>
          {product.recommendationReason ? (
            <Text style={styles.reason} numberOfLines={1}>
              {product.recommendationReason}
            </Text>
          ) : null}
          <View style={styles.priceRow}>
            <Text style={styles.price}>{product.price} {product.currency}</Text>
            <TouchableOpacity onPress={onSave} style={styles.saveButton}>
              <Text style={styles.saveIcon}>{'♡'}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    backgroundColor: colors.surface,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  overlay: {
    ...StyleSheet.absoluteFill,
    justifyContent: 'space-between',
    padding: spacing.md,
  },
  badges: {
    flexDirection: 'row',
    gap: spacing.xs,
  },
  sizeBadge: {
    marginLeft: spacing.xs,
  },
  info: {
    backgroundColor: 'rgba(0,0,0,0.65)',
    borderRadius: borderRadius.md,
    padding: spacing.md,
  },
  brand: {
    ...typography.label,
    color: colors.textInverse,
    opacity: 0.8,
    marginBottom: 2,
  },
  title: {
    ...typography.bodyBold,
    color: colors.textInverse,
    marginBottom: spacing.xs,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  reason: {
    ...typography.label,
    color: colors.textInverse,
    opacity: 0.82,
    marginBottom: spacing.xs,
  },
  price: {
    ...typography.h3,
    color: colors.textInverse,
  },
  saveButton: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.full,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveIcon: {
    fontSize: 22,
    color: colors.textInverse,
  },
});
