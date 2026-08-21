import React from 'react';
import { School, ShieldCheck, RefreshCw, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface DashboardHeaderProps {
  onRefresh: () => void;
  isLoading: boolean;
  isAggregateGap: boolean;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  onRefresh,
  isLoading,
  isAggregateGap,
}) => {
  const { user, activeMembership, setShowContextModal } = useAuth();

  // Dynamic Arabic greeting based on time of day
  const currentHour = new Date().getHours();
  const greeting = currentHour < 12 ? 'صباح الخير' : 'مساء الخير';
  const userName = user?.full_name || user?.username || 'أحمد محمد';
  const schoolName = activeMembership?.school?.name || 'مدرسة النور الأهلية';
  const yearName = activeMembership?.academic_year?.name || 'العام الدراسي 2026/2027';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
      {/* Page Title & Breadcrumbs */}
      <div className="page-header-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-header-title">الرئيسية</h1>
          <div className="page-header-breadcrumbs">
            <span>الرئيسية</span>
            <span>/</span>
            <span>لوحة التحكم التشغيلية</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {isAggregateGap && (
            <Badge variant="warning" icon={<AlertCircle size={12} />}>
              واجهة التجميع الموحدة (W2/W3 Gap)
            </Badge>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isLoading}
            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', height: '28px' }}
          >
            <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
            <span>تحديث البيانات</span>
          </Button>
        </div>
      </div>

      {/* Greeting & Active Context Banner */}
      <div className="dashboard-welcome-banner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="dashboard-welcome-icon-wrap">
            <School size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <h2 className="dashboard-welcome-title">
                {greeting}، {userName}
              </h2>
              <Badge variant="primary" icon={<ShieldCheck size={12} />}>
                لوحة الإدارة المدرسية
              </Badge>
            </div>
            <p className="dashboard-welcome-subtitle">
              السياق النشط: <strong>{schoolName}</strong> • {yearName}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowContextModal(true)}
            style={{ fontSize: '0.75rem', height: '30px', padding: '0.25rem 0.625rem' }}
          >
            تغيير السياق
          </Button>
        </div>
      </div>
    </div>
  );
};
