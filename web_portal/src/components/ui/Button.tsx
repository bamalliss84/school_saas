import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  isLoading?: boolean;
  loadingText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  isLoading = false,
  loadingText = 'جاري التحميل...',
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}) => {
  const variantClass = `btn-${variant}`;
  const sizeClass = size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : '';
  const widthClass = fullWidth ? 'btn-full' : '';

  return (
    <button
      className={`btn ${variantClass} ${sizeClass} ${widthClass} ${className}`.trim()}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <Loader2 className="animate-spin" size={16} />
          <span>{loadingText}</span>
        </>
      ) : (
        <>
          {leftIcon && <span className="btn-icon">{leftIcon}</span>}
          {children}
          {rightIcon && <span className="btn-icon">{rightIcon}</span>}
        </>
      )}
    </button>
  );
};
