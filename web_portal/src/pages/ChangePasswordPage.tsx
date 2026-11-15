import React, { useState } from 'react';
import { Button, Card, CardHeader, CardTitle } from '../components/ui';
import { useAuth } from '../context';
import { authService } from '../services/authService';

const field: React.CSSProperties = { display: 'grid', gap: '.3rem', fontSize: '.9rem' };
const input: React.CSSProperties = {
  minHeight: 40, padding: '.5rem .7rem', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)',
  background: 'var(--surface-primary)', color: 'var(--text-primary)',
};

const firstError = (err: unknown): string => {
  const errors = (err as { errors?: Record<string, unknown> })?.errors;
  if (errors) {
    const first = Object.values(errors).flat().find((value) => typeof value === 'string');
    if (typeof first === 'string') return first;
  }
  return err instanceof Error && err.message ? err.message : 'تعذر تغيير كلمة المرور.';
};

/** Changing the password revokes every session, so the user signs in again afterwards. */
export const ChangePasswordPage: React.FC = () => {
  const { logout } = useAuth();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [saving, setSaving] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (next.length < 8) { setError('كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل.'); return; }
    if (next !== confirm) { setError('كلمتا المرور غير متطابقتين.'); return; }
    setSaving(true);
    try {
      await authService.changePassword(current, next);
      setDone(true);
    } catch (err) {
      setError(firstError(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card style={{ maxWidth: 520 }}>
      <CardHeader><CardTitle>تغيير كلمة المرور</CardTitle></CardHeader>
      <div style={{ padding: '0 1rem 1rem' }}>
        {done ? (
          <div style={{ display: 'grid', gap: '.75rem' }}>
            <p role="status" style={{ margin: 0 }}>تم تغيير كلمة المرور. سُجّل خروجك من كل الأجهزة، سجّل الدخول بكلمة المرور الجديدة.</p>
            <div><Button onClick={() => logout()}>تسجيل الدخول من جديد</Button></div>
          </div>
        ) : (
          <form onSubmit={submit} style={{ display: 'grid', gap: '.8rem' }} aria-label="تغيير كلمة المرور">
            <label style={field}>كلمة المرور الحالية
              <input style={input} type="password" autoComplete="current-password" required value={current} onChange={(e) => setCurrent(e.target.value)} />
            </label>
            <label style={field}>كلمة المرور الجديدة
              <input style={input} type="password" autoComplete="new-password" required value={next} onChange={(e) => setNext(e.target.value)} />
            </label>
            <label style={field}>تأكيد كلمة المرور الجديدة
              <input style={input} type="password" autoComplete="new-password" required value={confirm} onChange={(e) => setConfirm(e.target.value)} />
            </label>
            {error && <p role="alert" style={{ margin: 0, color: 'var(--danger-600, #b91c1c)' }}>{error}</p>}
            <div><Button type="submit" isLoading={saving}>حفظ</Button></div>
          </form>
        )}
      </div>
    </Card>
  );
};
