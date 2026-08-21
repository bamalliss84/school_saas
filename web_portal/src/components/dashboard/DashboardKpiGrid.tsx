import React from 'react';
import {
  Users,
  GraduationCap,
  LayoutGrid,
  CheckCircle,
  UserX,
  Clock,
  TrendingUp,
  Info,
} from 'lucide-react';
import { KpiMetric, MetricIconType } from '../../types/dashboard';
import { Card, CardBody } from '../ui/Card';

interface DashboardKpiGridProps {
  metrics: KpiMetric[];
  isLoading?: boolean;
}

const getMetricIcon = (iconName: MetricIconType) => {
  switch (iconName) {
    case 'users':
      return <Users size={16} />;
    case 'teachers':
      return <GraduationCap size={16} />;
    case 'classes':
      return <LayoutGrid size={16} />;
    case 'attendance':
      return <CheckCircle size={16} />;
    case 'absent':
      return <UserX size={16} />;
    case 'late':
      return <Clock size={16} />;
    default:
      return <Users size={16} />;
  }
};

export const DashboardKpiGrid: React.FC<DashboardKpiGridProps> = ({ metrics, isLoading }) => {
  if (isLoading) {
    return (
      <div className="dashboard-kpi-grid">
        {[1, 2, 3, 4, 5, 6].map((idx) => (
          <div key={idx} className="skeleton" style={{ height: '96px', borderRadius: 'var(--radius-lg)' }} />
        ))}
      </div>
    );
  }

  return (
    <div className="dashboard-kpi-grid">
      {metrics.map((metric) => {
        return (
          <Card key={metric.id} hoverable className="dashboard-kpi-card">
            <CardBody style={{ padding: '0.75rem 0.875rem' }}>
              {/* Header row: Title + Icon */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <span className="dashboard-kpi-title">{metric.title}</span>
                <div
                  className="dashboard-kpi-icon-wrap"
                  style={{
                    backgroundColor: metric.bgColor,
                    color: metric.color,
                  }}
                >
                  {getMetricIcon(metric.iconName)}
                </div>
              </div>

              {/* Main KPI Value */}
              <div className="dashboard-kpi-value-row">
                <span className="dashboard-kpi-value">{metric.value}</span>
                {metric.trend && metric.trend.value.includes('▲') && (
                  <span className="dashboard-kpi-trend-badge success">
                    <TrendingUp size={11} />
                    {metric.trend.value}
                  </span>
                )}
              </div>

              {/* Subtext + Status / Gap badge */}
              <div className="dashboard-kpi-subtext-row">
                <span className="dashboard-kpi-subtext">{metric.subtext}</span>
                {!metric.isAvailable && metric.gapCode && (
                  <span
                    className="dashboard-kpi-gap-tag"
                    title={metric.gapDescription || 'واجهة التجميع غير متوفرة بعد'}
                  >
                    <Info size={10} />
                    {metric.gapCode}
                  </span>
                )}
              </div>
            </CardBody>
          </Card>
        );
      })}
    </div>
  );
};
