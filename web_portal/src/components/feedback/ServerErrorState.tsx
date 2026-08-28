import React from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/Button';

export interface ServerErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
  showHomeButton?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const ServerErrorState: React.FC<ServerErrorStateProps> = ({
  title = 'تعذر تحميل البيانات',
  description = 'حدث خطأ أثناء جلب البيانات. يمكنك المحاولة مرة أخرى.',
  onRetry,
  isRetrying = false,
  showHomeButton = true,
  className = '',
  style,
}) => {
  const navigate = useNavigate();

  return (
    <div className={`system-state-container ${className}`.trim()} style={style}>
      <div className="system-state-icon-wrap danger" aria-hidden="true">
        <AlertCircle size={32} />
      </div>
      <h3 className="system-state-title">{title}</h3>
      <p className="system-state-description">{description}</p>
      
      <div className="system-state-actions">
        {onRetry && (
          <Button
            variant="primary"
            onClick={onRetry}
            disabled={isRetrying}
            leftIcon={<RefreshCw size={15} className={isRetrying ? 'animate-spin' : ''} />}
          >
            {isRetrying ? 'جاري إعادة المحاولة...' : 'إعادة المحاولة'}
          </Button>
        )}
        {showHomeButton && (
          <Button
            variant="outline"
            onClick={() => navigate('/dashboard')}
            leftIcon={<Home size={15} />}
          >
            العودة للرئيسية
          </Button>
        )}
      </div>
    </div>
  );
};
