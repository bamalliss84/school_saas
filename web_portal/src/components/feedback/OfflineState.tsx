import React from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';
import { Button } from '../ui/Button';

export interface OfflineStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const OfflineState: React.FC<OfflineStateProps> = ({
  title = 'تعذر الاتصال بالخادم',
  description = 'تحقق من اتصال الإنترنت ثم حاول مرة أخرى.',
  onRetry,
  isRetrying = false,
  className = '',
  style,
}) => {
  return (
    <div className={`system-state-container ${className}`.trim()} style={style}>
      <div className="system-state-icon-wrap neutral" aria-hidden="true">
        <WifiOff size={32} />
      </div>
      <h3 className="system-state-title">{title}</h3>
      <p className="system-state-description">{description}</p>
      
      {onRetry && (
        <div className="system-state-actions">
          <Button
            variant="primary"
            onClick={onRetry}
            disabled={isRetrying}
            leftIcon={<RefreshCw size={15} className={isRetrying ? 'animate-spin' : ''} />}
          >
            {isRetrying ? 'جاري إعادة المحاولة...' : 'إعادة المحاولة'}
          </Button>
        </div>
      )}
    </div>
  );
};

export const OfflineBanner: React.FC<{ message?: string; className?: string }> = ({
  message = 'الاتصال بالإنترنت غير متاح — سيتم تحديث البيانات عند عودة الاتصال.',
  className = '',
}) => {
  return (
    <div className={`offline-banner ${className}`.trim()} role="alert">
      <WifiOff size={15} style={{ flexShrink: 0 }} />
      <span>{message}</span>
    </div>
  );
};
