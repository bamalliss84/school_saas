import 'package:flutter/material.dart';

abstract final class AppColors {
  static const primary = Color(0xff3157d5);
  static const background = Color(0xfff7f8fc);
  static const surface = Color(0xffffffff);
  static const textPrimary = Color(0xff182230);
  static const textSecondary = Color(0xff667085);
  static const success = Color(0xff197a55);
  static const warning = Color(0xffa15c00);
  static const error = Color(0xffb42318);
  static const info = Color(0xff175cd3);
  static const divider = Color(0xffe4e7ec);
  static const disabled = Color(0xff98a2b3);
}

abstract final class AppSpacing {
  static const x1 = 4.0;
  static const x2 = 8.0;
  static const x3 = 12.0;
  static const x4 = 16.0;
  static const x6 = 24.0;
  static const x8 = 32.0;
}

abstract final class AppRadius {
  static const card = 16.0;
  static const sheet = 24.0;
  static const chip = 10.0;
}
