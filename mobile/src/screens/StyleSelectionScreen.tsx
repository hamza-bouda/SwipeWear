import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Image,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button } from '../components';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { styleArchetypes, StyleArchetype } from '../data/styleArchetypes';

const { width } = Dimensions.get('window');
const COLUMN_GAP = spacing.sm;
const CARD_WIDTH = (width - spacing.lg * 2 - COLUMN_GAP) / 2;
const CARD_HEIGHT = CARD_WIDTH * 1.3;

interface Props {
  navigation: NativeStackNavigationProp<RootStackParamList, 'StyleSelection'>;
}

export function StyleSelectionScreen({ navigation }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const renderItem = ({ item }: { item: StyleArchetype }) => {
    const isSelected = selected.has(item.id);
    return (
      <TouchableOpacity
        style={[styles.card, isSelected && styles.cardSelected]}
        onPress={() => toggle(item.id)}
        activeOpacity={0.8}
      >
        <Image source={{ uri: item.imageUrl }} style={styles.cardImage} />
        <View style={styles.cardOverlay}>
          <Text style={styles.cardLabel}>{item.label}</Text>
        </View>
        {isSelected && (
          <View style={styles.checkBadge}>
            <Text style={styles.checkMark}>✓</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Choisis tes styles</Text>
        <Text style={styles.subtitle}>Sélectionne ceux qui te ressemblent</Text>
      </View>
      <FlatList
        data={styleArchetypes}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        numColumns={2}
        columnWrapperStyle={styles.row}
        contentContainerStyle={styles.grid}
        showsVerticalScrollIndicator={false}
      />
      <View style={styles.footer}>
        <Button
          title={
            selected.size === 0 ? 'Continuer' : `Continuer (${selected.size})`
          }
          onPress={() =>
            navigation.navigate('Constraints', {
              route: 'styles',
              selectedStyles: Array.from(selected),
            })
          }
          disabled={selected.size === 0}
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
  header: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.md,
  },
  title: {
    ...typography.h1,
    color: colors.textPrimary,
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  grid: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.lg,
  },
  row: {
    gap: COLUMN_GAP,
    marginBottom: COLUMN_GAP,
  },
  card: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  cardSelected: {
    borderColor: colors.accent,
  },
  cardImage: {
    width: '100%',
    height: '100%',
    // Seller photos are fetched over the network and a delisted item 404s.
    // The neutral fill keeps the tile readable — the label sits on top of it —
    // instead of leaving a hole in the grid.
    backgroundColor: '#EFEFEF',
  },
  cardOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: colors.overlay,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm,
  },
  cardLabel: {
    ...typography.bodyBold,
    color: colors.textInverse,
  },
  checkBadge: {
    position: 'absolute',
    top: spacing.sm,
    right: spacing.sm,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkMark: {
    color: colors.accentText,
    fontSize: 16,
    fontWeight: '700',
  },
  footer: {
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
});
