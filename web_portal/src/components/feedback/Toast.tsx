import React from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import { useToast, ToastItem } from '../../context';

const getToastIcon = (type: ToastItem['type']) => {
  switch (type) {
    case 'success':
      return <CheckCircle2 size={16} />;
    case 'error':
      return <AlertCircle size={16} />;
    case 'warning':
      return <AlertTriangle size={16} />;
    case 'info':
    default:
      return <Info size={16} />;
  }
};

export const Toast: React.FC<{ toast: ToastItem; onDismiss: (id: string) => void }> = ({
  toast,
  onDismiss,
}) => {
  return (
    <div className={`toast-item toast-${toast.type}`} role="status" aria-live="polite">
      <div className="toast-icon-wrap">{getToastIcon(toast.type)}</div>
      <div className="toast-content">
        {toast.title && <h5 className="toast-title">{toast.title}</h5>}
        <p className="toast-message">{toast.message}</p>
      </div>
      <button
        type="button"
        className="toast-close-btn"
        onClick={() => onDismiss(toast.id)}
        aria-label="إغلاق التنبيه"
      >
        <X size={14} />
      </button>
    </div>
  );
};

export const ToastContainer: React.FC = () => {
  const { toasts, hideToast } = useToast();

  if (toasts.length === 0) {
    return null;
  }

  return (
    <div className="toast-container" aria-label="تنبيهات النظام">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onDismiss={hideToast} />
      ))}
    </div>
  );
};
