import React from 'react';
import { ShieldAlert, Home, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context';
import { Button } from '../ui/Button';

export interface UnauthorizedStateProps {
  title?: string;
  description?: string;
  showSwitchContext?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const UnauthorizedState: React.FC<UnauthorizedStateProps> = ({
  title = 'ليس لديك صلاحية للوصول',
  description = 'هذه الصفحة غير متاحة لصلاحيات حسابك الحالية.',
  showSwitchContext = true,
  className = '',
  style,
}) => {
  const navigate = useNavigate();
  const { setShowContextModal } = useAuth();

  return (
    <div className={`system-state-container ${className}`.trim()} style={style}>
      <div className="system-state-icon-wrap danger" aria-hidden="true">
        <ShieldAlert size={32} />
      </div>
      <h3 className="system-state-title">{title}</h3>
      <p className="system-state-description">{description}</p>
      
      <div className="system-state-actions">
        <Button
          variant="primary"
          onClick={() => navigate('/dashboard')}
          leftIcon={<Home size={15} />}
        >
          العودة للرئيسية
        </Button>
        {showSwitchContext && (
          <Button
            variant="outline"
            onClick={() => setShowContextModal(true)}
            leftIcon={<RefreshCw size={15} />}
          >
            تغيير سياق العمل
          </Button>
        )}
      </div>
    </div>
  );
};
