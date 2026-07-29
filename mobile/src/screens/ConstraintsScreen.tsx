import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import Slider from '@react-native-community/slider';
import { Button } from '../components';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { useSubmitOnboarding } from '../api';
import { usePreferences } from '../context/PreferencesContext';

const AVAILABLE_SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
const MIN_BUDGET = 10;
const MAX_BUDGET = 300;

interface Props {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Constraints'>;
  route: RouteProp<RootStackParamList, 'Constraints'>;
}

export function ConstraintsScreen({ navigation, route }: Props) {
  const { route: onboardingRoute, selectedStyles, imageUris } = route.params;

  const [selectedSizes, setSelectedSizes] = useState<Set<string>>(new Set());
  const [maxBudget, setMaxBudget] = useState(MAX_BUDGET);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submitOnboarding = useSubmitOnboarding();
  const { gender, completeOnboarding } = usePreferences();

  const toggleSize = (size: string) => {
    setSelectedSizes((prev) => {
      const next = new Set(prev);
      if (next.has(size)) {
        next.delete(size);
      } else {
        next.add(size);
      }
      return next;
    });
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      // This was a setTimeout pretending to be a request, so every choice made
      // during onboarding — styles, sizes, budget — was discarded on the way to
      // the feed, and the first deck ignored all of it.
      await submitOnboarding({
        style_ids: selectedStyles ?? [],
        sizes: Array.from(selectedSizes),
        max_price_eur: maxBudget,
        gender,
      });
    } catch (e) {
      // A profile that failed to save is worth saying out loud: the feed would
      // otherwise open with none of the preferences the user just set.
      setError(
        e instanceof Error ? e.message : 'Impossible d\'enregistrer tes préférences',
      );
      setLoading(false);
      return;
    }
    setLoading(false);
    await completeOnboarding();
    navigation.replace('Main');
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Création de ton profil…</Text>
        <Text style={styles.loadingSubtext}>
          {onboardingRoute === 'images'
            ? "Analyse de tes images d'inspiration"
            : 'On accorde tes préférences de style'}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Presque fini !</Text>
        <Text style={styles.subtitle}>Indique tes tailles et ton budget</Text>
      </View>

      <View style={styles.content}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Tes tailles</Text>
          <View style={styles.sizeGrid}>
            {AVAILABLE_SIZES.map((size) => {
              const isSelected = selectedSizes.has(size);
              return (
                <TouchableOpacity
                  key={size}
                  style={[styles.sizeChip, isSelected && styles.sizeChipSelected]}
                  onPress={() => toggleSize(size)}
                >
                  <Text
                    style={[styles.sizeText, isSelected && styles.sizeTextSelected]}
                  >
                    {size}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Budget maximum</Text>
          <Text style={styles.budgetValue}>
            {maxBudget >= MAX_BUDGET ? 'Sans limite' : `${maxBudget} €`}
          </Text>
          <Slider
            style={styles.slider}
            minimumValue={MIN_BUDGET}
            maximumValue={MAX_BUDGET}
            step={5}
            value={maxBudget}
            onValueChange={setMaxBudget}
            minimumTrackTintColor={colors.primary}
            maximumTrackTintColor={colors.border}
            thumbTintColor={colors.primary}
          />
          <View style={styles.sliderLabels}>
            <Text style={styles.sliderLabel}>{MIN_BUDGET} €</Text>
            <Text style={styles.sliderLabel}>Sans limite</Text>
          </View>
        </View>
      </View>

      <View style={styles.footer}>
        {error && <Text style={styles.error}>{error}</Text>}
        <Button title="Commencer à swiper" onPress={handleSubmit} />
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
  content: {
    flex: 1,
    paddingHorizontal: spacing.lg,
  },
  section: {
    marginBottom: spacing.xl,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  sizeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  sizeChip: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  sizeChipSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  sizeText: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  sizeTextSelected: {
    color: colors.textInverse,
  },
  budgetValue: {
    ...typography.h2,
    color: colors.primary,
    marginBottom: spacing.md,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  sliderLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  sliderLabel: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  error: {
    ...typography.caption,
    color: colors.error,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  footer: {
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
    padding: spacing.lg,
  },
  loadingText: {
    ...typography.h2,
    color: colors.textPrimary,
    marginTop: spacing.lg,
  },
  loadingSubtext: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
});
