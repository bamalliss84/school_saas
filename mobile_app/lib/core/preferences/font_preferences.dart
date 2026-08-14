import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

enum AppFont {
  tajawal('Tajawal', 'تجوال'),
  cairo('Cairo', 'كايرو'),
  notoSansArabic('NotoSansArabic', 'نوتو سانس عربي');

  const AppFont(this.family, this.label);
  final String family;
  final String label;
}

abstract interface class FontPreferenceStore {
  Future<AppFont> read();
  Future<void> write(AppFont font);
}

class SharedPreferencesFontStore implements FontPreferenceStore {
  static const _key = 'appearance.font_family';
  @override
  Future<AppFont> read() async {
    final value = (await SharedPreferences.getInstance()).getString(_key);
    return AppFont.values.firstWhere((font) => font.name == value,
        orElse: () => AppFont.tajawal);
  }

  @override
  Future<void> write(AppFont font) async =>
      (await SharedPreferences.getInstance()).setString(_key, font.name);
}

class FontController extends StateNotifier<AppFont> {
  FontController(this._store) : super(AppFont.tajawal) {
    _load();
  }
  final FontPreferenceStore _store;
  Future<void> _load() async => state = await _store.read();
  Future<void> select(AppFont font) async {
    state = font;
    await _store.write(font);
  }
}

final fontStoreProvider =
    Provider<FontPreferenceStore>((ref) => SharedPreferencesFontStore());
final fontProvider = StateNotifierProvider<FontController, AppFont>(
  (ref) => FontController(ref.read(fontStoreProvider)),
);
