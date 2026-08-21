import React from 'react';
import { Inbox } from 'lucide-react';
import { Button } from '../ui/Button';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">
        {icon || <Inbox size={28} />}
      </div>
      <h4 className="empty-state-title">{title}</h4>
      {description && <p className="empty-state-description">{description}</p>}
      {actionLabel && onAction && (
        <Button variant="primary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
