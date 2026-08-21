import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  FileSpreadsheet,
  MessageSquare,
  Activity,
  CheckCircle2,
  Send,
  UserPlus,
  Bell,
  Award,
} from 'lucide-react';
import { DomainOperationsSummary, ActivityItem } from '../../types/dashboard';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

interface PreservedOperationsGridProps {
  summary: DomainOperationsSummary;
  activities: ActivityItem[];
  isLoading?: boolean;
}

export const PreservedOperationsGrid: React.FC<PreservedOperationsGridProps> = ({
  summary,
  activities,
  isLoading,
}) => {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="dashboard-operations-grid">
        {[1, 2, 3, 4].map((idx) => (
          <div key={idx} className="skeleton" style={{ height: '260px', borderRadius: 'var(--radius-xl)' }} />
        ))}
      </div>
    );
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
    <div className="dashboard-operations-grid">
      {/* 1. الواجبات (Homework) */}
      <Card className="dashboard-operational-card">
        <CardHeader style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--primary-50)',
                color: 'var(--primary-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <BookOpen size={16} />
            </div>
            <CardTitle style={{ fontSize: '0.9375rem', fontWeight: 800 }}>الواجبات</CardTitle>
          </div>
          <Badge variant="primary">نشط</Badge>
        </CardHeader>

        <CardBody style={{ padding: '0.875rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div className="ops-metric-list">
            <div className="ops-metric-row">
              <span className="ops-metric-label">واجبات نشطة حالياً</span>
              <strong className="ops-metric-value">{summary.homework.activeCount}</strong>
            </div>
            <div className="ops-metric-row">
              <span className="ops-metric-label">تسليمات اليوم المستحقة</span>
              <strong className="ops-metric-value">{summary.homework.dueTodayCount}</strong>
            </div>
            <div className="ops-metric-row">
              <span className="ops-metric-label">درجات بانتظار التقييم</span>
              <strong className="ops-metric-value text-warning">{summary.homework.pendingGradingCount}</strong>
            </div>
          </div>

          <div style={{ marginTop: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', marginBottom: '0.25rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>متوسط نسبة التسليم</span>
              <strong style={{ color: 'var(--primary-700)' }}>{summary.homework.averageSubmissionRate}%</strong>
            </div>
            <div className="ops-progress-bar">
              <div
                className="ops-progress-fill"
                style={{ width: `${summary.homework.averageSubmissionRate}%`, backgroundColor: 'var(--primary-600)' }}
              />
            </div>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate('/homework')}
            style={{ width: '100%', fontSize: '0.75rem', height: '30px' }}
          >
            <span>عرض الواجبات</span>
          </Button>
        </CardBody>
      </Card>

      {/* 2. الاختبارات والنتائج (Exams & Results) */}
      <Card className="dashboard-operational-card">
        <CardHeader style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--warning-50)',
                color: 'var(--warning-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <FileSpreadsheet size={16} />
            </div>
            <CardTitle style={{ fontSize: '0.9375rem', fontWeight: 800 }}>الاختبارات والنتائج</CardTitle>
          </div>
          <Badge variant="warning">اعتماد</Badge>
        </CardHeader>

        <CardBody style={{ padding: '0.875rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div className="ops-metric-list">
            <div className="ops-metric-row">
              <span className="ops-metric-label">اختبارات قادمة (Upcoming)</span>
              <strong className="ops-metric-value">{summary.exams.upcomingCount}</strong>
            </div>
            <div className="ops-metric-row">
              <span className="ops-metric-label">اختبارات مجدولة اليوم</span>
              <strong className="ops-metric-value">{summary.exams.todayCount}</strong>
            </div>
            <div className="ops-metric-row">
              <span className="ops-metric-label">نتائج بانتظار الاعتماد الإداري</span>
              <strong className="ops-metric-value text-danger">{summary.exams.awaitingApprovalCount}</strong>
            </div>
          </div>

          <div style={{ marginTop: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', marginBottom: '0.25rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>متوسط نسبة النجاح والتفوق</span>
              <strong style={{ color: 'var(--success-700)' }}>{summary.exams.averagePassRate}%</strong>
            </div>
            <div className="ops-progress-bar">
              <div
                className="ops-progress-fill"
                style={{ width: `${summary.exams.averagePassRate}%`, backgroundColor: 'var(--success-600)' }}
              />
            </div>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate('/exams')}
            style={{ width: '100%', fontSize: '0.75rem', height: '30px' }}
          >
            <span>عرض الاختبارات والنتائج</span>
          </Button>
        </CardBody>
      </Card>

      {/* 3. التواصل (Communications) */}
      <Card className="dashboard-operational-card">
        <CardHeader style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--indigo-50)',
                color: 'var(--indigo-600)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <MessageSquare size={16} />
            </div>
            <CardTitle style={{ fontSize: '0.9375rem', fontWeight: 800 }}>التواصل والإشعارات</CardTitle>
          </div>
          <Badge variant="neutral">الوارد</Badge>
        </CardHeader>

        <CardBody style={{ padding: '0.875rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div className="ops-metric-list">
            <div className="ops-metric-row">
              <span className="ops-metric-label">رسائل واردة عاجلة (Inbox)</span>
              <strong className="ops-metric-value text-primary">{summary.communications.urgentMessagesCount}</strong>
            </div>
            <div className="ops-metric-row">
              <span className="ops-metric-label">محادثات نشطة</span>
              <strong className="ops-metric-value">{summary.communications.activeConversationsCount}</strong>
            </div>
            <div className="ops-metric-row">
              <span className="ops-metric-label">إعلانات مدرسية منشورة</span>
              <strong className="ops-metric-value">{summary.communications.activeAnnouncementsCount}</strong>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto' }}>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate('/messages')}
              style={{ flex: 1, fontSize: '0.75rem', height: '30px' }}
            >
              <MessageSquare size={12} />
              <span>عرض الرسائل</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/announcements')}
              style={{ flex: 1, fontSize: '0.75rem', height: '30px' }}
            >
              <Send size={12} />
              <span>إنشاء إعلان</span>
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* 4. آخر النشاطات (Recent Activity Feed) */}
      <Card className="dashboard-operational-card">
        <CardHeader style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--neutral-100)',
                color: 'var(--neutral-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Activity size={16} />
            </div>
            <CardTitle style={{ fontSize: '0.9375rem', fontWeight: 800 }}>آخر النشاطات</CardTitle>
          </div>
          <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>آخر التحديثات</span>
        </CardHeader>

        <CardBody style={{ padding: '0.625rem 0.875rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
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
    </div>
  );
};
