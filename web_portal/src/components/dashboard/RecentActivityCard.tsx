import React from 'react';
import { Activity, Award, UserPlus, Bell, CheckCircle2 } from 'lucide-react';
import { ActivityItem } from '../../types/dashboard';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';

interface RecentActivityCardProps {
  activities: ActivityItem[];
  isLoading?: boolean;
}

export const RecentActivityCard: React.FC<RecentActivityCardProps> = ({
  activities,
  isLoading,
}) => {
  if (isLoading) {
    return <div className="skeleton" style={{ height: '140px', borderRadius: 'var(--radius-xl)' }} />;
  }

  const getActivityIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'exam':
        return <Award size={14} className="text-warning" />;
      case 'student':
        return <UserPlus size={14} className="text-primary" />;
      case 'announcement':
        return <Bell size={14} className="text-indigo" />;
      case 'attendance':
        return <CheckCircle2 size={14} className="text-success" />;
      default:
        return <Activity size={14} className="text-neutral" />;
    }
  };

  return (
    <Card className="dashboard-operational-card">
      <CardHeader style={{ padding: '0.625rem 1rem', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div
              style={{
                width: '24px',
                height: '24px',
                borderRadius: 'var(--radius-xs)',
                backgroundColor: 'var(--neutral-100)',
                color: 'var(--neutral-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Activity size={14} />
            </div>
            <CardTitle style={{ fontSize: '0.875rem', fontWeight: 700 }}>آخر النشاطات والتحديثات</CardTitle>
          </div>
          <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>سجل الأحداث المباشرة</span>
        </div>
      </CardHeader>

      <CardBody style={{ padding: '0.5rem 1rem' }}>
        <div className="activity-feed-list">
          {activities.map((item) => (
            <div key={item.id} className="activity-feed-item">
              <div className="activity-feed-icon-wrap">{getActivityIcon(item.type)}</div>
              <div className="activity-feed-content">
                <p className="activity-feed-title">{item.title}</p>
                <span className="activity-feed-time">{item.timeAgo}</span>
              </div>
            </div>
          ))}
        </div>
      </CardBody>
    </Card>
  );
};
