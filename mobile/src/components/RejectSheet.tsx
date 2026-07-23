import React, { useCallback, useMemo, forwardRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import BottomSheet, { BottomSheetBackdrop } from '@gorhom/bottom-sheet';
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
          opacity={0.4}
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
          <Text style={styles.title}>Why not this one?</Text>
          <TouchableOpacity
            style={styles.option}
            onPress={() => onSelect('swipe_left_style')}
            activeOpacity={0.7}
            accessibilityRole="button"
            accessibilityLabel="Not my style"
          >
            <Text style={styles.optionIcon}>{'🚫'}</Text>
            <Text style={styles.optionText}>Not my style</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.option}
            onPress={() => onSelect('swipe_left_price')}
            activeOpacity={0.7}
            accessibilityRole="button"
            accessibilityLabel="Too expensive"
          >
            <Text style={styles.optionIcon}>{'💸'}</Text>
            <Text style={styles.optionText}>Too expensive</Text>
          </TouchableOpacity>
        </View>
      </BottomSheet>
    );
  },
);

const styles = StyleSheet.create({
  background: {
    backgroundColor: colors.secondary,
    borderTopLeftRadius: borderRadius.lg,
    borderTopRightRadius: borderRadius.lg,
  },
  indicator: {
    backgroundColor: colors.disabled,
    width: 40,
  },
  content: {
    padding: spacing.lg,
    gap: spacing.md,
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
  },
  optionIcon: {
    fontSize: 24,
  },
  optionText: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
});
