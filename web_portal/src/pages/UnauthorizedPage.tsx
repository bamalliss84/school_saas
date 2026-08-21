import React from 'react';
import { ShieldX, LogOut, RefreshCw } from 'lucide-react';
import { useAuth } from '../context';
import { Button } from '../components/ui/Button';

export const UnauthorizedPage: React.FC = () => {
  const { user, activeMembership, logout, setShowContextModal } = useAuth();

  const getRoleArabic = (role?: string) => {
    switch (role) {
      case 'teacher': return 'معلم';
      case 'parent': return 'ولي أمر';
      case 'student': return 'طالب';
      default: return role || 'غير محدد';
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-app)',
        padding: '1.5rem',
      }}
    >
      <div
        className="card"
        style={{
          maxWidth: '480px',
          width: '100%',
          padding: '2.5rem 2rem',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: 'var(--radius-xl)',
            backgroundColor: 'var(--danger-50)',
            color: 'var(--danger-600)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.5rem auto',
          }}
        >
          <ShieldX size={32} />
        </div>

        <h1 style={{ fontSize: '1.375rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          غير مصرح لك بالوصول
        </h1>

        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem', lineHeight: 1.6 }}>
          هذه البوابة مخصصة حصراً لـ <strong>مديري المدارس (School Admin)</strong> و<strong>المسؤولين العامين (Super Admin)</strong>.
        </p>

        <div
          style={{
            backgroundColor: 'var(--neutral-50)',
            padding: '1rem',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.8125rem',
            textAlign: 'right',
            marginBottom: '1.5rem',
          }}
        >
          <div>
            <span>الحساب الحالي: </span>
            <strong>{user?.username}</strong>
          </div>
          <div style={{ marginTop: '0.25rem' }}>
            <span>الدور الحالي: </span>
            <strong>{getRoleArabic(user?.role)}</strong>
          </div>
          {activeMembership && (
            <div style={{ marginTop: '0.25rem' }}>
              <span>المدرسة: </span>
              <strong>{activeMembership.school.name}</strong>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <Button
            variant="outline"
            fullWidth
            onClick={() => setShowContextModal(true)}
            leftIcon={<RefreshCw size={16} />}
          >
            تبديل سياق المدرسة
          </Button>

          <Button
            variant="danger"
            fullWidth
            onClick={() => logout()}
            leftIcon={<LogOut size={16} />}
          >
            تسجيل الخروج
          </Button>
        </div>
      </div>
    </div>
  );
};
