import 'package:flutter/material.dart';
import '../preferences/font_preferences.dart';
import 'tokens.dart';

ThemeData buildAppTheme(AppFont font) {
  final scheme = ColorScheme.fromSeed(
    seedColor: AppColors.primary,
    brightness: Brightness.light,
    surface: AppColors.surface,
    error: AppColors.error,
  );
  final base = ThemeData(colorScheme: scheme, useMaterial3: true);
  return base.copyWith(
    scaffoldBackgroundColor: AppColors.background,
    textTheme: base.textTheme
        .apply(
          fontFamily: font.family,
          bodyColor: AppColors.textPrimary,
          displayColor: AppColors.textPrimary,
        )
        .copyWith(
          headlineLarge: base.textTheme.headlineLarge
              ?.copyWith(fontSize: 30, fontWeight: FontWeight.w700),
          headlineMedium: base.textTheme.headlineMedium
              ?.copyWith(fontSize: 22, fontWeight: FontWeight.w700),
          titleLarge: base.textTheme.titleLarge
              ?.copyWith(fontSize: 18, fontWeight: FontWeight.w700),
          titleMedium: base.textTheme.titleMedium
              ?.copyWith(fontSize: 16, fontWeight: FontWeight.w700),
          bodyLarge: base.textTheme.bodyLarge?.copyWith(fontSize: 16),
          bodyMedium: base.textTheme.bodyMedium?.copyWith(fontSize: 14),
          labelLarge: base.textTheme.labelLarge
              ?.copyWith(fontSize: 15, fontWeight: FontWeight.w700),
          bodySmall: base.textTheme.bodySmall
              ?.copyWith(fontSize: 12, color: AppColors.textSecondary),
        ),
    cardTheme: const CardTheme(
        color: AppColors.surface, elevation: 0, margin: EdgeInsets.zero),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.surface,
      border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.chip)),
    ),
  );
}
