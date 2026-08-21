import React from 'react';
import { Info } from 'lucide-react';
import { useAuth } from '../../context';
import { Button } from '../ui/Button';

export const HistoricalBanner: React.FC = () => {
  const { isHistorical, setShowContextModal } = useAuth();

  if (!isHistorical) return null;

  return (
    <div className="historical-banner" role="status" aria-live="polite">
      <div className="historical-banner-content">
        <Info size={16} />
        <span>أنت تستعرض عامًا دراسيًا سابقًا — البيانات للعرض فقط</span>
      </div>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setShowContextModal(true)}
        style={{
          borderColor: '#d97706',
          color: '#92400e',
          backgroundColor: '#ffffff',
          padding: '0.25rem 0.625rem',
          fontSize: '0.75rem',
          height: '28px',
        }}
      >
        تغيير السياق
      </Button>
    </div>
  );
};
