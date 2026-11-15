import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/app.dart';
import '../data/auth_repository.dart';

String changePasswordError(Object error) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map) {
      final errors = data['errors'] is Map ? data['errors'] as Map : data;
      for (final value in errors.values) {
        if (value is List && value.isNotEmpty && value.first is String) {
          return value.first as String;
        }
        if (value is String && value.isNotEmpty) return value;
      }
    }
  }
  return 'تعذر تغيير كلمة المرور. تحقق من الاتصال وحاول مجددًا.';
}

class ChangePasswordScreen extends StatefulWidget {
  const ChangePasswordScreen({
    super.key,
    required this.onSubmit,
    required this.onDone,
  });
  final Future<void> Function(String current, String next) onSubmit;
  final Future<void> Function() onDone;

  @override
  State<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends State<ChangePasswordScreen> {
  final current = TextEditingController();
  final next = TextEditingController();
  final confirm = TextEditingController();
  bool saving = false;
  bool done = false;
  String? error;

  @override
  void dispose() {
    current.dispose();
    next.dispose();
    confirm.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (next.text.length < 8) {
      setState(() =>
          error = 'كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل.');
      return;
    }
    if (next.text != confirm.text) {
      setState(() => error = 'كلمتا المرور غير متطابقتين.');
      return;
    }
    setState(() {
      saving = true;
      error = null;
    });
    try {
      await widget.onSubmit(current.text, next.text);
      if (mounted) setState(() => done = true);
    } catch (e) {
      if (mounted) setState(() => error = changePasswordError(e));
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('تغيير كلمة المرور')),
        body: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: done
                ? [
                    const Icon(Icons.verified_user_outlined, size: 64),
                    const SizedBox(height: 16),
                    const Text(
                      'تم تغيير كلمة المرور. سُجّل خروجك من كل الأجهزة، '
                      'سجّل الدخول بكلمة المرور الجديدة.',
                      key: Key('change-password-done'),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: () async {
                        Navigator.of(context)
                            .popUntil((route) => route.isFirst);
                        await widget.onDone();
                      },
                      child: const Text('تسجيل الدخول من جديد'),
                    ),
                  ]
                : [
                    TextField(
                      key: const Key('cp-current'),
                      controller: current,
                      obscureText: true,
                      decoration: const InputDecoration(
                          labelText: 'كلمة المرور الحالية'),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      key: const Key('cp-new'),
                      controller: next,
                      obscureText: true,
                      decoration: const InputDecoration(
                          labelText: 'كلمة المرور الجديدة'),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      key: const Key('cp-confirm'),
                      controller: confirm,
                      obscureText: true,
                      decoration: const InputDecoration(
                          labelText: 'تأكيد كلمة المرور الجديدة'),
                    ),
                    if (error != null) ...[
                      const SizedBox(height: 8),
                      Text(error!,
                          style: TextStyle(
                              color: Theme.of(context).colorScheme.error)),
                    ],
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: saving ? null : _submit,
                      child: saving
                          ? const SizedBox.square(
                              dimension: 20,
                              child: CircularProgressIndicator(strokeWidth: 2))
                          : const Text('حفظ'),
                    ),
                  ],
          ),
        ),
      );
}

/// Settings tile that opens the change-password flow. Providers are read only on tap,
/// so screens rendered without a ProviderScope (e.g. widget tests) still build.
class ChangePasswordTile extends StatelessWidget {
  const ChangePasswordTile({super.key});

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          key: const Key('open-change-password'),
          leading: const Icon(Icons.key_outlined),
          title: const Text('تغيير كلمة المرور'),
          trailing: const Icon(Icons.chevron_left),
          onTap: () {
            final container = ProviderScope.containerOf(context);
            final repository = AuthRepository(
                container.read(apiProvider).dio, container.read(storeProvider));
            Navigator.of(context).push(MaterialPageRoute<void>(
              builder: (_) => ChangePasswordScreen(
                onSubmit: repository.changePassword,
                onDone: () =>
                    container.read(sessionProvider.notifier).logout(),
              ),
            ));
          },
        ),
      );
}
