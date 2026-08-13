# School SaaS Mobile

Arabic-first Flutter client foundation for Student, Parent, and Teacher roles.

## Run

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1/
```

Use `127.0.0.1` for a Windows desktop client. The default Android emulator URL is `10.0.2.2`.

## Verification

```powershell
flutter pub get
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
```

The application authenticates against the real JWT API, loads memberships, selects an active or historical context, and sends `X-School-Membership-ID`. Admin roles intentionally receive an unsupported-mobile screen. Feature pages are placeholders for later sprints.

On Windows, Flutter plugins require Developer Mode (or another environment that permits symlinks). Never store production secrets in dart defines or source files.
