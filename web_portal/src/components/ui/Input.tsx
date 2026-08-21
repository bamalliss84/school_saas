import React, { forwardRef } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  endAdornment?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, leftIcon, rightIcon, endAdornment, className = '', id, style, ...props }, ref) => {
    const inputId = id || (label ? `input-${label.replace(/\s+/g, '-').toLowerCase()}` : undefined);

    const hasEndContent = Boolean(leftIcon || endAdornment);
    const hasStartContent = Boolean(rightIcon);

    return (
      <div className="form-group">
        {label && (
          <label htmlFor={inputId} className="form-label">
            {label}
          </label>
        )}
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center', width: '100%' }}>
          {hasStartContent && (
            <span
              style={{
                position: 'absolute',
                right: '0.875rem',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                pointerEvents: 'none',
                zIndex: 1,
              }}
            >
              {rightIcon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            className={`form-input ${error ? 'has-error' : ''} ${className}`.trim()}
            style={{
              paddingLeft: hasEndContent ? '2.75rem' : undefined,
              paddingRight: hasStartContent ? '2.75rem' : undefined,
              ...style,
            }}
            {...props}
          />
          {hasEndContent && (
            <div
              style={{
                position: 'absolute',
                left: '0.75rem',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1,
              }}
            >
              {endAdornment || leftIcon}
            </div>
          )}
        </div>
        {error && <span className="form-error">{error}</span>}
        {hint && !error && <span className="form-hint">{hint}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';
