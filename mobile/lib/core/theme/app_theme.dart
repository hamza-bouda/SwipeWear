import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

abstract final class AppColors {
  // Soft eucalyptus palette: light enough for long sessions, with the
  // original SwipeWear gold reserved for the premium offer.
  static const accent = Color(0xFFB8E3CF);
  static const accentLight = Color(0xFFE8F5EE);
  static const gold = Color(0xFFE7C66A);
  static const goldLight = Color(0xFFFBF1D4);
  static const background = Color(0xFFFCFAF3);
  static const surface = Color(0xFFF3F0E7);
  static const textPrimary = Color(0xFF151515);
  static const textSecondary = Color(0xFF7F796E);
  static const border = Color(0xFFE7E0D2);
  static const error = Color(0xFFD33B3B);
  static const success = Color(0xFF0FA36B);
}

abstract final class AppGradients {
  static const background = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFFCFAF3), Color(0xFFEFF7F1)],
  );

  static const mint = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFDDF3E8), Color(0xFFB8E3CF)],
  );

  static const gold = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFF7EAC2), Color(0xFFE7C66A)],
  );
}

abstract final class AppTheme {
  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(
      seedColor: AppColors.accent,
      brightness: Brightness.light,
    ).copyWith(
      primary: AppColors.textPrimary,
      onPrimary: Colors.white,
      secondary: AppColors.accent,
      onSecondary: AppColors.textPrimary,
      tertiary: AppColors.gold,
      onTertiary: AppColors.textPrimary,
      surface: AppColors.background,
      onSurface: AppColors.textPrimary,
      error: AppColors.error,
      onError: Colors.white,
    );

    return ThemeData(
      colorScheme: scheme,
      // Every route gets a light fallback surface. Screens rendered inside
      // AppShell opt into its shared gradient explicitly.
      scaffoldBackgroundColor: AppColors.background,
      useMaterial3: true,
      fontFamily: 'sans-serif',
      textTheme: const TextTheme(
        bodyLarge: TextStyle(fontSize: 15, height: 1.35),
        bodyMedium: TextStyle(fontSize: 14, height: 1.3),
        titleLarge: TextStyle(fontWeight: FontWeight.w800, letterSpacing: -.2),
        headlineSmall: TextStyle(
          fontSize: 25,
          fontWeight: FontWeight.w900,
          letterSpacing: -.7,
          height: 1.05,
        ),
        headlineMedium: TextStyle(
          fontSize: 30,
          fontWeight: FontWeight.w900,
          letterSpacing: -1,
          height: 1.02,
        ),
        displaySmall: TextStyle(
          fontSize: 36,
          fontWeight: FontWeight.w900,
          letterSpacing: -1.2,
          height: 1.02,
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        foregroundColor: AppColors.textPrimary,
        elevation: 0,
        centerTitle: false,
        titleSpacing: 20,
        surfaceTintColor: Colors.transparent,
        toolbarHeight: 70,
        systemOverlayStyle: SystemUiOverlayStyle.dark,
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        margin: EdgeInsets.zero,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 68,
        backgroundColor: Colors.transparent,
        indicatorColor: AppColors.accentLight,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        iconTheme: WidgetStateProperty.resolveWith(
          (states) => IconThemeData(
            color:
                states.contains(WidgetState.selected)
                    ? AppColors.textPrimary
                    : AppColors.textSecondary,
            size: 21,
          ),
        ),
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => TextStyle(
            fontSize: 9,
            fontWeight: FontWeight.w700,
            color:
                states.contains(WidgetState.selected)
                    ? AppColors.textPrimary
                    : AppColors.textSecondary,
          ),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.accent,
          foregroundColor: AppColors.textPrimary,
          minimumSize: const Size.fromHeight(52),
          shape: const StadiumBorder(),
          textStyle: const TextStyle(
            fontWeight: FontWeight.w900,
            letterSpacing: -.1,
          ),
          elevation: 0,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.textPrimary,
          minimumSize: const Size.fromHeight(48),
          side: const BorderSide(color: AppColors.border),
          shape: const StadiumBorder(),
          textStyle: const TextStyle(fontWeight: FontWeight.w700),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.textPrimary,
          textStyle: const TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: Colors.white,
        selectedColor: AppColors.accent,
        checkmarkColor: AppColors.textPrimary,
        side: const BorderSide(color: AppColors.border),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        labelStyle: const TextStyle(
          color: AppColors.textPrimary,
          fontWeight: FontWeight.w700,
          fontSize: 12,
        ),
        secondaryLabelStyle: const TextStyle(
          color: AppColors.textPrimary,
          fontWeight: FontWeight.w700,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 7),
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: AppColors.accent,
        inactiveTrackColor: AppColors.accentLight,
        thumbColor: AppColors.textPrimary,
        overlayColor: AppColors.accent.withValues(alpha: .14),
        trackHeight: 5,
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: AppColors.accent,
        linearTrackColor: AppColors.accentLight,
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: AppColors.background,
        surfaceTintColor: Colors.transparent,
        showDragHandle: true,
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.accent, width: 2),
        ),
      ),
    );
  }
}
