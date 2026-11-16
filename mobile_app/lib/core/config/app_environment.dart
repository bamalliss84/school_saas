abstract final class AppEnvironment {
  /// Server address. Set it at build time for store builds:
  ///   flutter build appbundle --dart-define=API_BASE_URL=https://school.example.com/api/v1/
  /// The default only reaches a local server from the Android emulator.
  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1/',
  );

  /// Why a build cannot be shipped with [url], or null when it is fine.
  /// Release builds must talk to a real server over HTTPS: they would otherwise
  /// send passwords and school data in clear text, or point at a dev machine.
  static String? releaseProblem(String url, {required bool isRelease}) {
    if (!isRelease) return null;
    final uri = Uri.tryParse(url);
    if (uri == null || uri.scheme != 'https' || uri.host.isEmpty) {
      return 'إعداد عنوان الخادم غير صحيح في هذه النسخة. '
          'يجب بناء التطبيق بعنوان HTTPS عبر API_BASE_URL.';
    }
    const devHosts = {'localhost', '127.0.0.1', '10.0.2.2'};
    if (devHosts.contains(uri.host)) {
      return 'هذه النسخة تشير إلى خادم تجريبي محلي. '
          'يجب بناؤها بعنوان الخادم الفعلي عبر API_BASE_URL.';
    }
    return null;
  }
}
