import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/auth_models.dart';
import '../models/school_context.dart';

class LocalSessionSnapshot {
  const LocalSessionSnapshot({required this.user, required this.context});
  final AuthenticatedUser user;
  final SchoolContext context;

  Map<String, Object?> toJson() => {
        'user': user.toJson(),
        'context': context.toLocalJson(),
      };

  factory LocalSessionSnapshot.fromJson(Map<String, dynamic> json) =>
      LocalSessionSnapshot(
        user: AuthenticatedUser.fromJson(
            Map<String, dynamic>.from(json['user'] as Map)),
        context: SchoolContext.fromLocalJson(
            Map<String, dynamic>.from(json['context'] as Map)),
      );
}

abstract interface class SessionSnapshotStore {
  Future<LocalSessionSnapshot?> read();
  Future<void> write(LocalSessionSnapshot snapshot);
  Future<void> clear();
}

class SharedPreferencesSessionSnapshotStore implements SessionSnapshotStore {
  static const _key = 'session.local_snapshot_v1';

  @override
  Future<LocalSessionSnapshot?> read() async {
    final raw = (await SharedPreferences.getInstance()).getString(_key);
    if (raw == null || raw.isEmpty) return null;
    try {
      return LocalSessionSnapshot.fromJson(
          Map<String, dynamic>.from(jsonDecode(raw) as Map));
    } catch (_) {
      await clear();
      return null;
    }
  }

  @override
  Future<void> write(LocalSessionSnapshot snapshot) async =>
      (await SharedPreferences.getInstance())
          .setString(_key, jsonEncode(snapshot.toJson()));

  @override
  Future<void> clear() async =>
      (await SharedPreferences.getInstance()).remove(_key);
}
