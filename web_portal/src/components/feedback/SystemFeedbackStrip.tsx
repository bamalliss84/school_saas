import React from 'react';
import { CheckCircle2, Info, AlertTriangle, XCircle, Bell, ShieldAlert, Check } from 'lucide-react';

export const SystemFeedbackStrip: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`feedback-token-strip ${className}`.trim()} aria-label="شريط رموز واستجابات النظام">
      <span className="token-pill success">
        <CheckCircle2 size={13} />
        <span>Success</span>
      </span>

      <span className="token-pill info">
        <Info size={13} />
        <span>Info</span>
      </span>

      <span className="token-pill warning">
        <AlertTriangle size={13} />
        <span>Warning</span>
      </span>

      <span className="token-pill error">
        <XCircle size={13} />
        <span>Error</span>
      </span>

      <span className="token-pill info" style={{ backgroundColor: '#f0fdf4', color: '#166534', borderColor: '#bbf7d0' }}>
        <Bell size={13} />
        <span>Toast</span>
      </span>

      <span className="token-pill success" style={{ backgroundColor: '#ecfdf5', color: '#047857' }}>
        <Check size={13} />
        <span>Inline alert</span>
      </span>

      <span className="token-pill error" style={{ backgroundColor: '#fef2f2', color: '#b91c1c' }}>
        <ShieldAlert size={13} />
        <span>Field validation</span>
      </span>

      <span className="token-pill warning" style={{ backgroundColor: '#fffbeb', color: '#b45309' }}>
        <span>Modal alert</span>
      </span>
    </div>
  );
};
