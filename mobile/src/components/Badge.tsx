import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { borderRadius, spacing } from '../theme/spacing';

type BadgeVariant = 'default' | 'success' | 'warning' | 'error';

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  style?: ViewStyle;
}

const variantColors: Record<BadgeVariant, { bg: string; text: string }> = {
  default: { bg: colors.surface, text: colors.textPrimary },
  success: { bg: '#FEF9C3', text: '#A16207' },
  warning: { bg: '#FFF3E0', text: colors.warning },
  error: { bg: '#FFEBEE', text: colors.error },
};

export function Badge({ label, variant = 'default', style }: BadgeProps) {
  const { bg, text } = variantColors[variant];
  return (
    <View style={[styles.container, { backgroundColor: bg }, style]}>
      <Text style={[styles.text, { color: text }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
    alignSelf: 'flex-start',
  },
  text: {
    ...typography.captionBold,
  },
});
