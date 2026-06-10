import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button } from '../components';
import { trackEvent } from '../analytics';
import { colors, typography, spacing } from '../theme';
import { RootStackParamList } from '../navigation/types';

interface Props {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Onboarding'>;
}

export function OnboardingScreen({ navigation }: Props) {
  useEffect(() => {
    trackEvent({ name: 'onboarding_started' });
  }, []);

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>SwipeWear</Text>
        <Text style={styles.subtitle}>
          Discover second-hand fashion pieces picked for your style
        </Text>
      </View>
      <View style={styles.actions}>
        <Button
          title="Choose my styles"
          onPress={() => {
            trackEvent({ name: 'onboarding_completed', properties: { route: 'styles' } });
            navigation.navigate('StyleSelection');
          }}
        />
        <Button
          title="Import my inspirations"
          variant="outline"
          onPress={() => {
            trackEvent({ name: 'onboarding_completed', properties: { route: 'images' } });
            navigation.navigate('ImageImport');
          }}
          style={styles.secondaryButton}
        />
        <Button
          title="Skip"
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
    backgroundColor: colors.primary,
    padding: spacing.lg,
    justifyContent: 'space-between',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    ...typography.h1,
    color: colors.textInverse,
    fontSize: 36,
    marginBottom: spacing.md,
  },
  subtitle: {
    ...typography.body,
    color: colors.textInverse,
    textAlign: 'center',
    opacity: 0.8,
  },
  actions: {
    paddingBottom: spacing.xl,
  },
  secondaryButton: {
    marginTop: spacing.sm,
    borderColor: colors.textInverse,
  },
  skipButton: {
    marginTop: spacing.sm,
  },
});
