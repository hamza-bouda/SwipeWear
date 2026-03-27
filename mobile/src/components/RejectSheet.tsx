import React, { useCallback, useMemo, forwardRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import BottomSheet, { BottomSheetBackdrop } from '@gorhom/bottom-sheet';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius } from '../theme';

export type RejectReason = 'swipe_left_style' | 'swipe_left_price';

interface RejectSheetProps {
  onSelect: (reason: RejectReason) => void;
}

export const RejectSheet = forwardRef<BottomSheet, RejectSheetProps>(
  function RejectSheet({ onSelect }, ref) {
    const snapPoints = useMemo(() => ['30%'], []);

    const renderBackdrop = useCallback(
      (props: React.ComponentProps<typeof BottomSheetBackdrop>) => (
        <BottomSheetBackdrop
          {...props}
          disappearsOnIndex={-1}
          appearsOnIndex={0}
          opacity={0.25}
        />
      ),
      [],
    );

    return (
      <BottomSheet
        ref={ref}
        index={-1}
        snapPoints={snapPoints}
        enablePanDownToClose
        backdropComponent={renderBackdrop}
        backgroundStyle={styles.background}
        handleIndicatorStyle={styles.indicator}
      >
        <View style={styles.content}>
          <Text style={styles.title}>Pourquoi pas celle-ci ?</Text>
          <TouchableOpacity
            style={styles.option}
            onPress={() => onSelect('swipe_left_style')}
            activeOpacity={0.7}
            accessibilityRole="button"
            accessibilityLabel="Pas mon style"
          >
            <View style={styles.optionIconWrap}>
              <Ionicons name="close-circle" size={20} color={colors.error} />
            </View>
            <Text style={styles.optionText}>Pas mon style</Text>
            <Ionicons name="chevron-forward" size={16} color={colors.textTertiary} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.option}
            onPress={() => onSelect('swipe_left_price')}
            activeOpacity={0.7}
            accessibilityRole="button"
            accessibilityLabel="Trop cher"
          >
            <View style={styles.optionIconWrap}>
              <Ionicons name="pricetag" size={20} color={colors.warning} />
            </View>
            <Text style={styles.optionText}>Trop cher</Text>
            <Ionicons name="chevron-forward" size={16} color={colors.textTertiary} />
          </TouchableOpacity>
        </View>
      </BottomSheet>
    );
  },
);

const styles = StyleSheet.create({
  background: {
    backgroundColor: colors.background,
    borderTopLeftRadius: borderRadius.lg,
    borderTopRightRadius: borderRadius.lg,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 8,
  },
  indicator: {
    backgroundColor: colors.border,
    width: 36,
  },
  content: {
    padding: spacing.lg,
    gap: spacing.sm,
  },
  title: {
    ...typography.h3,
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: spacing.xs,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    gap: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  optionIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  optionText: {
    ...typography.bodyBold,
    color: colors.textPrimary,
    flex: 1,
  },
});
