import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Image,
  TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { Product } from '../types';
import { useSaves } from '../context/SavesContext';

type Nav = NativeStackNavigationProp<RootStackParamList>;

export function SavesScreen() {
  const navigation = useNavigation<Nav>();
  const { savedProducts, toggleSave } = useSaves();

  if (savedProducts.length === 0) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyIcon}>❤️</Text>
        <Text style={styles.emptyTitle}>No saves yet</Text>
        <Text style={styles.emptySubtitle}>
          Tap the heart on items you love to save them here
        </Text>
      </View>
    );
  }

  const renderItem = ({ item }: { item: Product }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('ProductDetail', { productId: item.id })}
      activeOpacity={0.8}
    >
      <Image source={{ uri: item.imageUrls[0] }} style={styles.cardImage} />
      <View style={styles.cardInfo}>
        <Text style={styles.cardBrand}>{item.brand}</Text>
        <Text style={styles.cardTitle} numberOfLines={1}>{item.title}</Text>
        <Text style={styles.cardPrice}>{item.price} {item.currency}</Text>
      </View>
      <TouchableOpacity style={styles.removeButton} onPress={() => toggleSave(item)}>
        <Text style={styles.removeText}>✕</Text>
      </TouchableOpacity>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Saved items</Text>
        <Text style={styles.headerCount}>{savedProducts.length}</Text>
      </View>
      <FlatList
        data={savedProducts}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.md,
  },
  headerTitle: {
    ...typography.h1,
    color: colors.textPrimary,
  },
  headerCount: {
    ...typography.h3,
    color: colors.textSecondary,
  },
  list: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.lg,
  },
  card: {
    flexDirection: 'row',
    backgroundColor: colors.secondary,
    borderRadius: borderRadius.md,
    marginBottom: spacing.sm,
    overflow: 'hidden',
    alignItems: 'center',
  },
  cardImage: {
    width: 80,
    height: 80,
  },
  cardInfo: {
    flex: 1,
    padding: spacing.sm,
  },
  cardBrand: {
    ...typography.label,
    color: colors.textSecondary,
  },
  cardTitle: {
    ...typography.body,
    color: colors.textPrimary,
    marginTop: 2,
  },
  cardPrice: {
    ...typography.bodyBold,
    color: colors.primary,
    marginTop: spacing.xs,
  },
  removeButton: {
    padding: spacing.md,
  },
  removeText: {
    ...typography.body,
    color: colors.textSecondary,
  },
  empty: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  emptyTitle: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  emptySubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
});
