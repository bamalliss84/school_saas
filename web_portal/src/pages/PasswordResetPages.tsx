import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AlertCircle, CheckCircle2, GraduationCap } from 'lucide-react';
import { authService } from '../services/authService';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

const errorText = (err: unknown, fallback: string): string => {
  if (err && typeof err === 'object') {
    const errors = (err as { errors?: Record<string, unknown> }).errors;
    const first = errors && Object.values(errors).flat().find((v) => typeof v === 'string');
    if (typeof first === 'string') return first;
    const message = (err as { message?: string }).message;
    if (message) return message;
  }
  return fallback;
};

const AuthCard: React.FC<{ title: string; subtitle: string; children: React.ReactNode }> = ({ title, subtitle, children }) => (
  <div className="login-page-container">
    <main className="login-card-wrapper" style={{ maxWidth: 480 }}>
      <section className="login-form-pane" aria-labelledby="auth-heading" style={{ width: '100%' }}>
        <div className="login-brand-badge">
          <span className="login-brand-icon-wrap" aria-hidden="true"><GraduationCap size={17} /></span>
          <span className="login-brand-title">منصة المدرسة</span>
        </div>
        <h1 id="auth-heading" className="login-heading">{title}</h1>
        <p className="login-subheading">{subtitle}</p>
        {children}
        <div className="login-footer-caption"><Link to="/login">العودة إلى تسجيل الدخول</Link></div>
      </section>
    </main>
  </div>
);

const Notice: React.FC<{ kind: 'error' | 'success'; text: string }> = ({ kind, text }) => (
  <div
    className="login-error-alert"
    role={kind === 'error' ? 'alert' : 'status'}
    style={kind === 'success' ? { background: '#ecfdf5', borderColor: '#a7f3d0', color: '#065f46' } : undefined}
  >
    {kind === 'error' ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
    <span>{text}</span>
  </div>
);

export const ForgotPasswordPage: React.FC = () => {
  const [identifier, setIdentifier] = useState('');
  const [sending, setSending] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!identifier.trim()) return setError('أدخل اسم المستخدم أو البريد الإلكتروني.');
    setSending(true);
    setError(null);
    try {
      const response = await authService.requestPasswordReset(identifier.trim());
      setDone(response.detail);
    } catch (err) {
      setError(errorText(err, 'تعذر إرسال الطلب، حاول مرة أخرى بعد قليل.'));
    } finally {
      setSending(false);
    }
  };

  return (
    <AuthCard title="نسيت كلمة المرور؟" subtitle="أدخل اسم المستخدم أو البريد الإلكتروني، وسنرسل رابطًا لاختيار كلمة مرور جديدة.">
      {error && <Notice kind="error" text={error} />}
      {done ? (
        <Notice kind="success" text={done} />
      ) : (
        <form onSubmit={submit} noValidate>
          <Input
            label="اسم المستخدم أو البريد الإلكتروني"
            autoComplete="username"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
          />
          <div style={{ marginTop: '1.125rem' }}>
            <Button type="submit" variant="primary" fullWidth size="lg" isLoading={sending} loadingText="جارٍ الإرسال...">
              إرسال رابط إعادة التعيين
            </Button>
          </div>
        </form>
      )}
    </AuthCard>
  );
};

export const ResetPasswordPage: React.FC = () => {
  const [params] = useSearchParams();
  const uid = params.get('uid') || '';
  const token = params.get('token') || '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (password.length < 8) return setError('كلمة المرور يجب أن تكون 8 أحرف على الأقل.');
    if (password !== confirm) return setError('كلمتا المرور غير متطابقتين.');
    setSaving(true);
    try {
      const response = await authService.confirmPasswordReset(uid, token, password);
      setDone(response.detail);
    } catch (err) {
      setError(errorText(err, 'تعذر تغيير كلمة المرور.'));
    } finally {
      setSaving(false);
    }
  };

  if (!uid || !token) {
    return (
      <AuthCard title="رابط غير صالح" subtitle="الرابط ناقص أو منسوخ بشكل خاطئ.">
        <Link to="/forgot-password">اطلب رابطًا جديدًا</Link>
      </AuthCard>
    );
  }

  return (
    <AuthCard title="اختر كلمة مرور جديدة" subtitle="استخدم 8 أحرف على الأقل، ويفضّل مزيج من حروف وأرقام ورموز.">
      {error && <Notice kind="error" text={error} />}
      {done ? (
        <>
          <Notice kind="success" text={done} />
          <Link to="/login">تسجيل الدخول</Link>
        </>
      ) : (
        <form onSubmit={submit} noValidate>
          <Input label="كلمة المرور الجديدة" type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <Input label="تأكيد كلمة المرور" type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          <div style={{ marginTop: '1.125rem' }}>
            <Button type="submit" variant="primary" fullWidth size="lg" isLoading={saving} loadingText="جارٍ الحفظ...">
              حفظ كلمة المرور
            </Button>
          </div>
        </form>
      )}
    </AuthCard>
  );
};
