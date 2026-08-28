import React from 'react';
import { LogIn, Clock } from 'lucide-react';
import { useAuth } from '../../context';
import { Button } from '../ui/Button';

export interface SessionExpiredModalProps {
  isOpen: boolean;
  onClose?: () => void;
}

export const SessionExpiredModal: React.FC<SessionExpiredModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { logout } = useAuth();

  if (!isOpen) return null;

  const handleReLogin = () => {
    logout();
  };

  return (
    <div
      className="modal-overlay"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="session-expired-title"
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '420px',
          padding: '2rem 1.75rem',
          textAlign: 'center',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          borderRadius: 'var(--radius-xl)',
          animation: 'modalPop 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        <div
          style={{
            width: '56px',
            height: '56px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--warning-50)',
            color: 'var(--warning-600)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.25rem auto',
          }}
        >
          <Clock size={28} />
        </div>

        <h3
          id="session-expired-title"
          style={{
            fontSize: '1.25rem',
            fontWeight: 800,
            color: 'var(--text-primary)',
            marginBottom: '0.5rem',
          }}
        >
          انتهت جلسة الدخول
        </h3>

        <p
          style={{
            fontSize: '0.875rem',
            color: 'var(--text-secondary)',
            marginBottom: '1.75rem',
            lineHeight: 1.5,
          }}
        >
          انتهت صلاحية جلستك. يرجى تسجيل الدخول مرة أخرى للمتابعة.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', justifyContent: 'center' }}>
          <Button
            variant="primary"
            onClick={handleReLogin}
            leftIcon={<LogIn size={15} />}
            style={{ flex: 1 }}
          >
            تسجيل الدخول مرة أخرى
          </Button>
          {onClose && (
            <Button
              variant="outline"
              onClick={onClose}
              style={{ flex: 1 }}
            >
              إلغاء
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
