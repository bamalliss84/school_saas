import React from 'react';
import { Loader2 } from 'lucide-react';

export interface LoadingSpinnerProps {
  size?: number;
  text?: string;
  fullPage?: boolean;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 36,
  text = 'جاري التحميل...',
  fullPage = false,
}) => {
  const content = (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.75rem',
        padding: '2rem',
        color: 'var(--primary-600)',
      }}
    >
      <Loader2 className="animate-spin" size={size} />
      {text && (
        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          {text}
        </span>
      )}
    </div>
  );

  if (fullPage) {
    return (
      <div
        style={{
          position: 'fixed',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'var(--bg-app)',
          zIndex: 9999,
        }}
      >
        {content}
      </div>
    );
  }

  return content;
};
