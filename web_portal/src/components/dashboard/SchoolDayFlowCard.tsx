import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, Calendar, CheckCircle2, PlayCircle, Layers } from 'lucide-react';
import { SchoolDayFlow } from '../../types/dashboard';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Button } from '../ui/Button';

interface SchoolDayFlowCardProps {
  flow: SchoolDayFlow;
  isLoading?: boolean;
}

export const SchoolDayFlowCard: React.FC<SchoolDayFlowCardProps> = ({ flow, isLoading }) => {
  const navigate = useNavigate();

  if (isLoading) {
    return <div className="skeleton" style={{ height: '220px', borderRadius: 'var(--radius-xl)' }} />;
  }

  return (
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
            <Clock size={16} />
          </div>
          <div>
            <CardTitle style={{ fontSize: '0.9375rem', fontWeight: 800 }}>سير اليوم الدراسي</CardTitle>
          </div>
        </div>
      </CardHeader>

      <CardBody style={{ padding: '0.875rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
        {/* 3 Mini Stats: Current, Completed, Scheduled */}
        <div className="school-flow-stats-row">
          <div className="school-flow-stat-box current">
            <span className="school-flow-stat-label">الحصص الحالية</span>
            <div className="school-flow-stat-val-wrap">
              <PlayCircle size={15} className="text-primary" />
              <span className="school-flow-stat-val">{flow.currentPeriod}</span>
            </div>
          </div>

          <div className="school-flow-stat-box completed">
            <span className="school-flow-stat-label">الحصص المكتملة</span>
            <div className="school-flow-stat-val-wrap">
              <CheckCircle2 size={15} className="text-success" />
              <span className="school-flow-stat-val">{flow.completedPeriods}</span>
            </div>
          </div>

          <div className="school-flow-stat-box scheduled">
            <span className="school-flow-stat-label">الحصص المجدولة</span>
            <div className="school-flow-stat-val-wrap">
              <Layers size={15} className="text-neutral" />
              <span className="school-flow-stat-val">{flow.totalPeriods}</span>
            </div>
          </div>
        </div>

        {/* Timeline Bar */}
        <div className="school-flow-timeline-container">
          <div className="school-flow-timeline-labels">
            <div className="timeline-node">
              <span className="timeline-node-title">بداية اليوم الدراسي</span>
              <span className="timeline-node-time">{flow.startTime}</span>
            </div>

            <div className="timeline-node active">
              <span className="timeline-node-title">الوقت الحالي</span>
              <span className="timeline-node-time active-badge">{flow.currentTime}</span>
            </div>

            <div className="timeline-node">
              <span className="timeline-node-title">نهاية اليوم الدراسي</span>
              <span className="timeline-node-time">{flow.endTime}</span>
            </div>
          </div>

          {/* Progress Track */}
          <div className="school-flow-progress-track">
            <div
              className="school-flow-progress-fill"
              style={{ width: `${Math.min(100, Math.max(0, flow.progressPercent))}%` }}
            />
            <div
              className="school-flow-progress-thumb"
              style={{ right: `${Math.min(98, Math.max(2, flow.progressPercent))}%` }}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="school-flow-actions-row">
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/timetable')}
            style={{ flex: 1, fontSize: '0.75rem', height: '32px' }}
          >
            <Calendar size={14} />
            <span>عرض الجدول اليومي</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/attendance')}
            style={{ flex: 1, fontSize: '0.75rem', height: '32px' }}
          >
            <span>متابعة الحصص غير المسجلة</span>
          </Button>
        </div>
      </CardBody>
    </Card>
  );
};
