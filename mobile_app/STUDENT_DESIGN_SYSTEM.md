# Student Design System — Sprint 5B.0

## Foundations

- Arabic-first RTL on Android and iOS from one Flutter codebase.
- Colors: primary `#3157D5`, background `#F7F8FC`, surface `#FFFFFF`, primary text `#182230`, secondary text `#667085`; semantic success/warning/error/info/divider/disabled tokens live in `core/design_system`.
- Spacing tokens: 4, 8, 12, 16, 24, 32. Cards use radius 16; sheets 24; chips 10.
- Typography respects system scaling. Bundled offline families are Tajawal (default), Cairo, and Noto Sans Arabic. Preference changes immediately and persists independently of session/logout/context.

## Student shell

The shared shell uses `SafeArea` for notch, Dynamic Island, and home-indicator insets. It does not depend on Android hardware-back behavior. Bottom navigation is: الرئيسية، الواجبات، النتائج، الرسائل، المزيد. All destinations except appearance settings remain explicit placeholders in 5B.0.

Reusable components: `AppCard`, primary/secondary buttons, text field, status chip, header, bottom navigation, historical/offline banners, last-updated label, empty/error states, and skeleton card. Screens must use tokens instead of hardcoded presentation values.

## Accessibility and responsiveness

Layouts use flexible constraints, ellipsis/wrapping for long Arabic names, 44+ logical-pixel controls, semantic labels, and non-color-only status cues. Widget coverage includes RTL, long Arabic text, and 150% text scaling. Android device acceptance covers small/normal/large phone behavior; iOS native visual acceptance remains pending macOS/Xcode.
