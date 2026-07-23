import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Button } from '../components';
import { trackEvent } from '../analytics';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';

interface Props {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Onboarding'>;
}

export function OnboardingScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();

  useEffect(() => {
    trackEvent({ name: 'onboarding_started' });
  }, []);

  return (
    <View style={styles.container}>
      <View style={[styles.topSpacer, { height: insets.top + 60 }]} />

      <View style={styles.content}>
        <View style={styles.logoWrap}>
          <Text style={styles.logoMark}>SW</Text>
        </View>
        <Text style={styles.title}>
          Swipe<Text style={styles.titleAccent}>Wear</Text>
        </Text>
        <Text style={styles.subtitle}>
          Découvre des pièces de seconde main sélectionnées par ton IA, en swipant comme sur Tinder.
        </Text>
      </View>

      <View style={[styles.actions, { paddingBottom: insets.bottom + spacing.lg }]}>
        <Button
          title="Choisir mes styles"
          onPress={() => {
            trackEvent({ name: 'onboarding_completed', properties: { route: 'styles' } });
            navigation.navigate('StyleSelection');
          }}
        />
        <Button
          title="Importer mes inspirations"
          variant="outline"
          onPress={() => {
            trackEvent({ name: 'onboarding_completed', properties: { route: 'images' } });
            navigation.navigate('ImageImport');
          }}
          style={styles.secondaryButton}
        />
        <Button
          title="Passer"
          variant="ghost"
          onPress={() => {
            trackEvent({ name: 'onboarding_completed', properties: { route: 'skip' } });
            navigation.replace('Main');
          }}
          style={styles.skipButton}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    paddingHorizontal: spacing.lg,
    justifyContent: 'space-between',
  },
  topSpacer: {},
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.md,
  },
  logoWrap: {
    width: 72,
    height: 72,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  logoMark: {
    fontSize: 26,
    fontWeight: '800',
    color: colors.accentText,
    letterSpacing: -1,
  },
  title: {
    ...typography.h1,
    color: colors.textPrimary,
    fontSize: 36,
    letterSpacing: -1,
  },
  titleAccent: {
    color: colors.accent,
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: spacing.sm,
  },
  actions: {
    gap: spacing.sm,
  },
  secondaryButton: {
    borderColor: colors.border,
  },
  skipButton: {},
});
