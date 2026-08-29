import 'package:flutter/material.dart';

enum AppVisualRole { teacher, student, parent }

abstract final class RoleVisualTokens {
  static const teacher = Color(0xff2457d6);
  static const student = Color(0xff198754);
  static const parent = Color(0xff7447c8);

  static Color accent(AppVisualRole role) => switch (role) {
        AppVisualRole.teacher => teacher,
        AppVisualRole.student => student,
        AppVisualRole.parent => parent,
      };

  static Color softSurface(AppVisualRole role) =>
      accent(role).withOpacity(.08);
}
