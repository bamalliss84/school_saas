import 'package:flutter/material.dart';

/// Requests a reset link by e-mail. The link opens the web reset page.
class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key, required this.onSubmit});
  final Future<String> Function(String identifier) onSubmit;

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final identifier = TextEditingController();
  bool sending = false;
  String? done;
  String? error;

  @override
  void dispose() {
    identifier.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (identifier.text.trim().isEmpty) {
      setState(() => error = 'أدخل اسم المستخدم أو البريد الإلكتروني.');
      return;
    }
    setState(() {
      sending = true;
      error = null;
    });
    try {
      final message = await widget.onSubmit(identifier.text);
      if (mounted) {
        setState(() => done = message.isEmpty
            ? 'إذا كان الحساب مرتبطًا ببريد إلكتروني فستصلك رسالة بالخطوات.'
            : message);
      }
    } catch (_) {
      if (mounted) {
        setState(() => error = 'تعذر إرسال الطلب. تحقق من الاتصال وحاول مجددًا.');
      }
    } finally {
      if (mounted) setState(() => sending = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('استعادة كلمة المرور')),
        body: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 420),
                child: done != null
                    ? Column(mainAxisSize: MainAxisSize.min, children: [
                        const Icon(Icons.mark_email_read_outlined, size: 64),
                        const SizedBox(height: 16),
                        Text(done!,
                            key: const Key('forgot-done'),
                            textAlign: TextAlign.center),
                        const SizedBox(height: 24),
                        FilledButton(
                          onPressed: () => Navigator.of(context).maybePop(),
                          child: const Text('العودة لتسجيل الدخول'),
                        ),
                      ])
                    : Column(mainAxisSize: MainAxisSize.min, children: [
                        const Text(
                          'أدخل اسم المستخدم أو البريد الإلكتروني المسجل، وسنرسل رابطًا لتعيين كلمة مرور جديدة. '
                          'إذا لم يكن لحسابك بريد إلكتروني فتواصل مع إدارة المدرسة.',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 24),
                        TextField(
                          key: const Key('forgot-identifier'),
                          controller: identifier,
                          textInputAction: TextInputAction.send,
                          onSubmitted: (_) => _submit(),
                          decoration: const InputDecoration(
                              labelText: 'اسم المستخدم أو البريد الإلكتروني'),
                        ),
                        if (error != null) ...[
                          const SizedBox(height: 8),
                          Text(error!,
                              style: TextStyle(
                                  color: Theme.of(context).colorScheme.error)),
                        ],
                        const SizedBox(height: 16),
                        FilledButton(
                          onPressed: sending ? null : _submit,
                          child: sending
                              ? const SizedBox.square(
                                  dimension: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2))
                              : const Text('إرسال رابط الاستعادة'),
                        ),
                      ]),
              ),
            ),
          ),
        ),
      );
}
