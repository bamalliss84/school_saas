import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, ClipboardCheck } from 'lucide-react';
import { AttendanceBreakdown } from '../../types/dashboard';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Button } from '../ui/Button';

interface TodayAttendanceCardProps {
  breakdown: AttendanceBreakdown;
  isLoading?: boolean;
}

export const TodayAttendanceCard: React.FC<TodayAttendanceCardProps> = ({ breakdown, isLoading }) => {
  const navigate = useNavigate();

  if (isLoading) {
    return <div className="skeleton" style={{ height: '220px', borderRadius: 'var(--radius-xl)' }} />;
  }

  const totalRecorded =
    breakdown.presentCount +
    breakdown.absentCount +
    breakdown.lateCount +
    breakdown.excusedCount +
    breakdown.pendingCount;

  const presentPct = totalRecorded > 0 ? (breakdown.presentCount / totalRecorded) * 100 : 91.8;
  const absentPct = totalRecorded > 0 ? (breakdown.absentCount / totalRecorded) * 100 : 6.1;
  const latePct = totalRecorded > 0 ? (breakdown.lateCount / totalRecorded) * 100 : 1.4;
  const excusedPct = totalRecorded > 0 ? (breakdown.excusedCount / totalRecorded) * 100 : 0.7;

  return (
    <Card className="dashboard-operational-card">
      <CardHeader style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--success-50)',
                color: 'var(--success-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ClipboardCheck size={16} />
            </div>
            <CardTitle style={{ fontSize: '0.9375rem', fontWeight: 800 }}>الحضور اليوم</CardTitle>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div className="attendance-teacher-badge" title="حضور الكادر التعليمي اليوم">
              <span className="label">حضور المعلمين اليوم</span>
              <span className="counts">
                <strong className="text-success">{breakdown.teacherPresentCount}</strong> / {breakdown.teacherTotalCount}
              </span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardBody style={{ padding: '0.875rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
        {/* Stacked Attendance Progress Bar */}
        <div>
          <div className="attendance-stacked-bar">
            <div className="bar-segment present" style={{ width: `${presentPct}%` }} title={`حاضر: ${breakdown.presentCount}`} />
            <div className="bar-segment absent" style={{ width: `${absentPct}%` }} title={`غائب: ${breakdown.absentCount}`} />
            <div className="bar-segment late" style={{ width: `${latePct}%` }} title={`متأخر: ${breakdown.lateCount}`} />
            <div className="bar-segment excused" style={{ width: `${excusedPct}%` }} title={`معذور: ${breakdown.excusedCount}`} />
          </div>

          {/* Legend Items Grid */}
          <div className="attendance-legend-grid">
            <div className="legend-item">
              <span className="dot present" />
              <span className="legend-name">حاضر</span>
              <strong className="legend-val">{breakdown.presentCount.toLocaleString('ar-EG')}</strong>
            </div>

            <div className="legend-item">
              <span className="dot absent" />
              <span className="legend-name">غائب</span>
              <strong className="legend-val">{breakdown.absentCount.toLocaleString('ar-EG')}</strong>
            </div>

            <div className="legend-item">
              <span className="dot late" />
              <span className="legend-name">متأخر</span>
              <strong className="legend-val">{breakdown.lateCount.toLocaleString('ar-EG')}</strong>
            </div>

            <div className="legend-item">
              <span className="dot excused" />
              <span className="legend-name">معذور</span>
              <strong className="legend-val">{breakdown.excusedCount.toLocaleString('ar-EG')}</strong>
            </div>

            <div className="legend-item">
              <span className="dot pending" />
              <span className="legend-name">لم يسجل بعد</span>
              <strong className="legend-val">{breakdown.pendingCount}</strong>
            </div>
          </div>
        </div>

        {/* Quick Attendance Action Buttons */}
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto' }}>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate('/attendance')}
            style={{ flex: 1, fontSize: '0.75rem', height: '32px' }}
          >
            <Users size={13} />
            <span>عرض الحضور</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/attendance')}
            style={{ flex: 1, fontSize: '0.75rem', height: '32px' }}
          >
            <span>متابعة غير المسجل</span>
          </Button>
        </div>
      </CardBody>
    </Card>
  );
};
