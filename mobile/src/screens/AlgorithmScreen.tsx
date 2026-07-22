import React, { useMemo, useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useAlgorithm, type AlgorithmPreference, type PreferenceKind } from '../context/AlgorithmContext';
import { colors, spacing, typography } from '../theme';
import type { RootStackParamList } from '../navigation/types';

const brandSuggestions = ['Adidas', 'Carhartt WIP', 'Dickies', 'Levi\'s', 'New Balance', 'Nike', 'Stussy', 'The North Face'];

const sections: Array<{ title: string; kinds: PreferenceKind[] }> = [
  { title: 'Liked brands', kinds: ['liked_brand'] },
  { title: 'Excluded brands', kinds: ['excluded_brand'] },
  { title: 'Colours & styles', kinds: ['color', 'style'] },
  { title: 'Budget', kinds: ['budget'] },
  { title: 'Sizes', kinds: ['size'] },
];

function PreferenceChip({ item, onLock, onRemove }: { item: AlgorithmPreference; onLock: () => void; onRemove: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${item.label}, ${item.source}, ${item.locked ? 'locked' : 'unlocked'}. Tap to ${item.locked ? 'unlock' : 'lock'}; long press to remove.`}
      onPress={onLock}
      onLongPress={onRemove}
      style={[styles.chip, item.locked && styles.chipLocked]}
    >
      <Text style={styles.chipText}>{item.label}</Text>
      <Text accessibilityLabel={item.source === 'manual' ? 'Manual preference' : 'Learned from your swipes'} style={styles.chipMeta}>
        {item.source === 'manual' ? '✎' : '✦'} {item.locked ? '🔒' : '🔓'}
      </Text>
    </Pressable>
  );
}

export function AlgorithmScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { preferences, addPreference, removePreference, toggleLock } = useAlgorithm();
  const [brandQuery, setBrandQuery] = useState('');

  const suggestions = useMemo(() => brandSuggestions.filter((brand) => (
    brand.toLowerCase().includes(brandQuery.trim().toLowerCase())
    && !preferences.some((item) => item.kind === 'liked_brand' && item.label.toLowerCase() === brand.toLowerCase())
  )).slice(0, 4), [brandQuery, preferences]);

  const liked = preferences.filter((item) => item.kind === 'liked_brand').map((item) => item.label);
  const style = preferences.find((item) => item.kind === 'style')?.label.toLowerCase() ?? 'personal';
  const budget = preferences.find((item) => item.kind === 'budget')?.label.toLowerCase() ?? 'your budget';
  const phrase = `${style} finds ${budget}${liked.length ? `, with ${liked.slice(0, 2).join(' and ')}` : ''}.`;

  const selectBrand = (brand: string) => {
    addPreference('liked_brand', brand);
    setBrandQuery('');
  };

  const confirmRemoval = (item: AlgorithmPreference) => {
    Alert.alert('Remove preference?', `Remove ${item.label} from your algorithm?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Remove', style: 'destructive', onPress: () => removePreference(item.id) },
    ]);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Pressable accessibilityRole="button" accessibilityLabel="Go back to profile" onPress={() => navigation.goBack()}>
        <Text style={styles.back}>‹ Profile</Text>
      </Pressable>
      <Text style={styles.title}>My algorithm</Text>
      <View style={styles.summaryCard}>
        <Text style={styles.summaryLabel}>YOUR PROFILE, BASED ON YOUR SETTINGS</Text>
        <Text style={styles.summaryText}>{phrase}</Text>
        <Text style={styles.summaryHint}>Changes shape your next feed refresh.</Text>
      </View>

      {sections.map((section) => {
        const items = preferences.filter((item) => section.kinds.includes(item.kind));
        return (
          <View key={section.title} style={styles.section}>
            <Text style={styles.sectionTitle}>{section.title}</Text>
            <View style={styles.chipRow}>
              {items.length ? items.map((item) => (
                <PreferenceChip key={item.id} item={item} onLock={() => toggleLock(item.id)} onRemove={() => confirmRemoval(item)} />
              )) : <Text style={styles.empty}>No preferences yet</Text>}
            </View>
          </View>
        );
      })}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Add a brand</Text>
        <TextInput
          value={brandQuery}
          onChangeText={setBrandQuery}
          placeholder="Search brands"
          placeholderTextColor={colors.textSecondary}
          style={styles.search}
          autoCapitalize="words"
          returnKeyType="done"
          onSubmitEditing={() => selectBrand(brandQuery)}
          accessibilityLabel="Search and add a liked brand"
        />
        {brandQuery.trim() ? (
          <View style={styles.suggestions}>
            {suggestions.map((brand) => (
              <Pressable key={brand} accessibilityRole="button" accessibilityLabel={`Add ${brand}`} onPress={() => selectBrand(brand)} style={styles.suggestion}>
                <Text style={styles.suggestionText}>{brand}</Text><Text style={styles.add}>Add</Text>
              </Pressable>
            ))}
            {!suggestions.length ? <Pressable onPress={() => selectBrand(brandQuery)} style={styles.suggestion}><Text style={styles.suggestionText}>Add “{brandQuery.trim()}”</Text><Text style={styles.add}>Add</Text></Pressable> : null}
          </View>
        ) : null}
      </View>
      <Text style={styles.legend}>✦ learned from your swipes · ✎ added by you · tap a chip to lock it · long press to remove it</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingTop: 64, paddingBottom: spacing.xl },
  back: { ...typography.body, color: colors.textSecondary, marginBottom: spacing.md },
  title: { ...typography.h1, color: colors.textPrimary, marginBottom: spacing.md },
  summaryCard: { backgroundColor: colors.primary, borderRadius: 16, padding: spacing.lg, marginBottom: spacing.xl },
  summaryLabel: { ...typography.caption, color: colors.background, opacity: 0.8, marginBottom: spacing.xs },
  summaryText: { ...typography.h3, color: colors.background },
  summaryHint: { ...typography.caption, color: colors.background, marginTop: spacing.sm, opacity: 0.9 },
  section: { marginBottom: spacing.lg },
  sectionTitle: { ...typography.bodyBold, color: colors.textPrimary, marginBottom: spacing.sm },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: { backgroundColor: colors.surface, borderRadius: 20, borderWidth: 1, borderColor: colors.border, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, flexDirection: 'row', gap: spacing.xs, alignItems: 'center' },
  chipLocked: { borderColor: colors.accent, backgroundColor: colors.accentLight },
  chipText: { ...typography.caption, color: colors.textPrimary },
  chipMeta: { ...typography.caption, color: colors.textSecondary },
  empty: { ...typography.caption, color: colors.textSecondary },
  search: { ...typography.body, color: colors.textPrimary, backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1, borderRadius: 10, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  suggestions: { marginTop: spacing.xs, borderRadius: 10, overflow: 'hidden', borderWidth: 1, borderColor: colors.border },
  suggestion: { padding: spacing.md, backgroundColor: colors.surface, flexDirection: 'row', justifyContent: 'space-between', borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border },
  suggestionText: { ...typography.body, color: colors.textPrimary },
  add: { ...typography.bodyBold, color: colors.accentDark },
  legend: { ...typography.caption, color: colors.textSecondary, lineHeight: 18 },
});
