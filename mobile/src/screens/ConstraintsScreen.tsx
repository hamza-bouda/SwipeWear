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
      // Stub API call — will connect to real backend when KAN-33/34 are done
      await new Promise((resolve) => setTimeout(resolve, 1500));
      navigation.replace('Main');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Building your profile...</Text>
        <Text style={styles.loadingSubtext}>
          {onboardingRoute === 'images'
            ? 'Analyzing your inspiration images'
            : 'Matching your style preferences'}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Almost there!</Text>
        <Text style={styles.subtitle}>Set your size and budget preferences</Text>
      </View>

      <View style={styles.content}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your sizes</Text>
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
          <Text style={styles.sectionTitle}>Maximum budget</Text>
          <Text style={styles.budgetValue}>
            {maxBudget >= MAX_BUDGET ? 'No limit' : `${maxBudget} €`}
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
            <Text style={styles.sliderLabel}>No limit</Text>
          </View>
        </View>
      </View>

      <View style={styles.footer}>
        <Button title="Start discovering" onPress={handleSubmit} />
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
