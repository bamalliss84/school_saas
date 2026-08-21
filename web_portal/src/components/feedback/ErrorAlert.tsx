import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle, Info, X } from 'lucide-react';

export interface ErrorAlertProps {
  variant?: 'danger' | 'warning' | 'success' | 'info';
  title?: string;
  message: string;
  errors?: Record<string, unknown>;
  onClose?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  variant = 'danger',
  title,
  message,
  errors,
  onClose,
}) => {
  const icons = {
    danger: <AlertCircle size={20} className="flex-shrink-0" />,
    warning: <AlertTriangle size={20} className="flex-shrink-0" />,
    success: <CheckCircle size={20} className="flex-shrink-0" />,
    info: <Info size={20} className="flex-shrink-0" />,
  };

  const fieldErrors = errors ? Object.entries(errors).filter(([k]) => k !== 'code') : [];

  return (
    <div className={`alert alert-${variant}`} role="alert">
      {icons[variant]}
      <div style={{ flex: 1 }}>
        {title && <strong style={{ display: 'block', marginBottom: '0.25rem' }}>{title}</strong>}
        <div>{message}</div>
        {fieldErrors.length > 0 && (
          <ul style={{ marginTop: '0.5rem', paddingRight: '1.25rem', fontSize: '0.8125rem' }}>
            {fieldErrors.map(([field, err]) => (
              <li key={field}>
                <strong>{field}:</strong> {Array.isArray(err) ? err.join(', ') : String(err)}
              </li>
            ))}
          </ul>
        )}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: 'inherit',
            cursor: 'pointer',
            padding: '0.25rem',
            display: 'flex',
            alignItems: 'center',
          }}
          aria-label="إغلاق"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};
