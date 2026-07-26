import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button } from '../components';
import { colors, typography, spacing, borderRadius } from '../theme';
import { RootStackParamList } from '../navigation/types';
import { usePreferences, Gender } from '../context/PreferencesContext';
import { trackEvent } from '../analytics';

interface Props {
  navigation: NativeStackNavigationProp<RootStackParamList, 'GenderLanguage'>;
}

const GENDERS: { id: Gender; label: string; hint: string }[] = [
  { id: 'women', label: 'Femme', hint: 'Pièces femme et unisexe' },
  { id: 'men', label: 'Homme', hint: 'Pièces homme et unisexe' },
  { id: 'unisex', label: 'Tout me va', hint: 'Aucun filtre de genre' },
];

export function GenderLanguageScreen({ navigation }: Props) {
  const { gender, setGender } = usePreferences();
  const [selectedGender, setSelectedGender] = useState<Gender | null>(gender);

  const handleContinue = async () => {
    if (!selectedGender) return;
    await setGender(selectedGender);
    trackEvent({ name: 'onboarding_started' });
    navigation.navigate('Onboarding');
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.title}>Pour qui cherches-tu ?</Text>
        <Text style={styles.subtitle}>
          Ça évite de te montrer des pièces qui ne te concernent pas.
        </Text>

        <View style={styles.group}>
          {GENDERS.map((option) => {
            const isSelected = selectedGender === option.id;
            return (
              <TouchableOpacity
                key={option.id}
                style={[styles.card, isSelected && styles.cardSelected]}
                onPress={() => setSelectedGender(option.id)}
                activeOpacity={0.8}
                accessibilityRole="radio"
                accessibilityState={{ selected: isSelected }}
              >
                <View style={styles.cardText}>
                  <Text style={styles.cardLabel}>{option.label}</Text>
                  <Text style={styles.cardHint}>{option.hint}</Text>
                </View>
                <View style={[styles.radio, isSelected && styles.radioSelected]}>
                  {isSelected && <View style={styles.radioDot} />}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

        <Text style={styles.note}>Tu pourras changer ça dans les paramètres.</Text>
      </ScrollView>

      <View style={styles.footer}>
        <Button title="Continuer" onPress={handleContinue} disabled={!selectedGender} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingTop: spacing.xxl },
  title: { ...typography.h1, color: colors.textPrimary, marginBottom: spacing.xs },
  subtitle: { ...typography.body, color: colors.textSecondary, marginBottom: spacing.xl },
  group: { gap: spacing.sm },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  cardSelected: { borderColor: colors.accent, borderWidth: 2 },
  cardText: { flex: 1 },
  cardLabel: { ...typography.bodyBold, color: colors.textPrimary },
  cardHint: { ...typography.caption, color: colors.textSecondary, marginTop: 2 },
  radio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioSelected: { borderColor: colors.accent },
  radioDot: {
    width: 12, height: 12, borderRadius: 6, backgroundColor: colors.accent,
  },
  note: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.lg,
  },
  footer: { padding: spacing.lg },
});
