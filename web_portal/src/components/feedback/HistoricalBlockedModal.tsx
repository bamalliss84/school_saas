import React from 'react';
import { AlertTriangle, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../context';
import { Button } from '../ui/Button';

export interface HistoricalBlockedModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToCurrent?: () => void;
}

export const HistoricalBlockedModal: React.FC<HistoricalBlockedModalProps> = ({
  isOpen,
  onClose,
  onSwitchToCurrent,
}) => {
  const { setShowContextModal } = useAuth();

  if (!isOpen) return null;

  const handleSwitchContext = () => {
    onClose();
    if (onSwitchToCurrent) {
      onSwitchToCurrent();
    } else {
      setShowContextModal(true);
    }
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
      aria-labelledby="historical-blocked-title"
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '440px',
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
          <AlertTriangle size={28} />
        </div>

        <h3
          id="historical-blocked-title"
          style={{
            fontSize: '1.25rem',
            fontWeight: 800,
            color: 'var(--text-primary)',
            marginBottom: '0.5rem',
          }}
        >
          لا يمكن تعديل بيانات عام سابق
        </h3>

        <p
          style={{
            fontSize: '0.875rem',
            color: 'var(--text-secondary)',
            marginBottom: '1.75rem',
            lineHeight: 1.6,
          }}
        >
          أنت تعمل حالياً في عام دراسي سابق. يمكنك استعراض البيانات فقط، ولا يُسمح بالإضافة أو التعديل أو الحذف.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', justifyContent: 'center' }}>
          <Button
            variant="primary"
            onClick={handleSwitchContext}
            style={{ flex: 1 }}
          >
            الانتقال للعام الحالي
          </Button>
          <Button
            variant="outline"
            onClick={onClose}
            leftIcon={<ArrowLeft size={15} />}
            style={{ flex: 1 }}
          >
            العودة للعرض
          </Button>
        </div>
      </div>
    </div>
  );
};
