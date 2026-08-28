import React from 'react';
import { Inbox, SearchX, FileText, Plus, RotateCcw } from 'lucide-react';
import { Button } from '../ui/Button';

export type EmptyStateVariant = 'default' | 'filtered' | 'announcements' | 'card';

export interface EmptyStateProps {
  variant?: EmptyStateVariant;
  icon?: React.ReactNode;
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  variant = 'default',
  icon,
  title,
  description,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  className = '',
  style,
}) => {
  // Preset defaults according to approved Nano Board D5
  let defaultIcon: React.ReactNode = <Inbox size={28} />;
  let defaultTitle = 'لا توجد بيانات حالياً';
  let defaultDescription = 'لم يتم العثور على أي سجلات في هذا القسم.';
  let defaultActionLabel = actionLabel;
  let defaultSecondaryActionLabel = secondaryActionLabel;

  if (variant === 'announcements') {
    defaultIcon = <FileText size={28} />;
    defaultTitle = 'لا توجد إعلانات حتى الآن';
    defaultDescription = 'ابدأ بإنشاء أول إعلان للمدرسة لمشاركته مع الكادر التعليمي وأولياء الأمور.';
    defaultActionLabel = defaultActionLabel || 'إنشاء إعلان';
  } else if (variant === 'filtered') {
    defaultIcon = <SearchX size={28} />;
    defaultTitle = 'لا توجد نتائج مطابقة';
    defaultDescription = 'جرّب تغيير معايير البحث أو التصفية للوصول إلى النتائج المطلوبة.';
    defaultSecondaryActionLabel = defaultSecondaryActionLabel || 'إعادة تعيين الفلاتر';
  }

  const finalTitle = title || defaultTitle;
  const finalDescription = description !== undefined ? description : defaultDescription;
  const finalActionLabel = actionLabel || (variant === 'announcements' ? defaultActionLabel : undefined);
  const finalSecondaryActionLabel = secondaryActionLabel || (variant === 'filtered' ? defaultSecondaryActionLabel : undefined);

  return (
    <div className={`empty-state ${variant === 'card' ? 'empty-state-card' : ''} ${className}`.trim()} style={style}>
      <div className="empty-state-icon">
        {icon || defaultIcon}
      </div>
      <h4 className="empty-state-title">{finalTitle}</h4>
      {finalDescription && <p className="empty-state-description">{finalDescription}</p>}
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        {finalActionLabel && onAction && (
          <Button variant="primary" size="sm" onClick={onAction} leftIcon={<Plus size={14} />}>
            {finalActionLabel}
          </Button>
        )}
        {finalSecondaryActionLabel && onSecondaryAction && (
          <Button variant="outline" size="sm" onClick={onSecondaryAction} leftIcon={<RotateCcw size={14} />}>
            {finalSecondaryActionLabel}
          </Button>
        )}
      </div>
    </div>
  );
};
