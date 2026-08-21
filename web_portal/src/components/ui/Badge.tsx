import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral';
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  icon,
  className = '',
  ...props
}) => {
  return (
    <span className={`badge badge-${variant} ${className}`.trim()} {...props}>
      {icon && <span className="badge-icon">{icon}</span>}
      {children}
    </span>
  );
};
