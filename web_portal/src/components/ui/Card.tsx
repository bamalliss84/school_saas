import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  hoverable = false,
  className = '',
  ...props
}) => {
  return (
    <div
      className={`card ${hoverable ? 'card-hover' : ''} ${className}`.trim()}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => <div className={`card-header ${className}`.trim()} {...props}>{children}</div>;

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className = '',
  ...props
}) => <h3 className={`card-title ${className}`.trim()} {...props}>{children}</h3>;

export const CardSubtitle: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  children,
  className = '',
  ...props
}) => <p className={`card-subtitle ${className}`.trim()} {...props}>{children}</p>;

export const CardBody: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => <div className={`card-body ${className}`.trim()} {...props}>{children}</div>;

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => <div className={`card-footer ${className}`.trim()} {...props}>{children}</div>;
