import React from 'react';

export interface ProgressBarProps {
  value: number; // 0 to 100
  label?: string;
  showPercent?: boolean;
  variant?: 'primary' | 'success' | 'danger';
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  showPercent = true,
  variant = 'primary',
  className = '',
}) => {
  const clampedValue = Math.min(100, Math.max(0, value));

  return (
    <div className={`progress-bar-container ${className}`.trim()}>
      {(label || showPercent) && (
        <div className="progress-bar-header">
          {label && <span>{label}</span>}
          {showPercent && <span>{Math.round(clampedValue)}%</span>}
        </div>
      )}
      <div className="progress-bar-track" role="progressbar" aria-valuenow={clampedValue} aria-valuemin={0} aria-valuemax={100}>
        <div
          className={`progress-bar-fill ${variant === 'primary' ? '' : variant}`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
};
