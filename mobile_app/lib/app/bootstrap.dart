import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/config/app_environment.dart';
import 'app.dart';

Future<void> bootstrap() async {
  final problem = AppEnvironment.releaseProblem(
    AppEnvironment.apiBaseUrl,
    isRelease: kReleaseMode,
  );
  if (problem != null) {
    // Never start a store build that would talk to a dev server or over HTTP.
    runApp(MisconfiguredBuildApp(message: problem));
    return;
  }
  runApp(const ProviderScope(child: SchoolSaaSApp()));
}

/// Shown instead of the app when a release build was made with a wrong server address.
class MisconfiguredBuildApp extends StatelessWidget {
  const MisconfiguredBuildApp({super.key, required this.message});

  final String message;

  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(
            body: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.cloud_off_outlined, size: 48),
                    const SizedBox(height: 16),
                    Text(message, textAlign: TextAlign.center),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
}
