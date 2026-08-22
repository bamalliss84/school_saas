import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../context';
import { dashboardService, DashboardApiResponse } from '../services/dashboardService';
import { DashboardHeader } from '../components/dashboard/DashboardHeader';
import { DashboardKpiGrid } from '../components/dashboard/DashboardKpiGrid';
import { AttentionAlertsCard } from '../components/dashboard/AttentionAlertsCard';
import { SchoolDayFlowCard } from '../components/dashboard/SchoolDayFlowCard';
import { TodayAttendanceCard } from '../components/dashboard/TodayAttendanceCard';
import { AcademicOperationsGrid } from '../components/dashboard/AcademicOperationsGrid';
import { AttendanceTrendCard } from '../components/dashboard/AttendanceTrendCard';
import { QuickActionsGrid } from '../components/dashboard/QuickActionsGrid';
import { RecentActivityCard } from '../components/dashboard/RecentActivityCard';
import { ErrorAlert } from '../components/feedback/ErrorAlert';
import { Clock } from 'lucide-react';
import { Badge } from '../components/ui/Badge';

export const DashboardPage: React.FC = () => {
  const { isHistorical, isReadOnly } = useAuth();
  const [data, setData] = useState<DashboardApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await dashboardService.getDashboardData();
      setData(res);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'فشل في تحميل بيانات لوحة التحكم';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const isLocked = isHistorical || isReadOnly;

  return (
    <div className="dashboard-container" style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
      {/* 1. Section A: Active Context & Page Header */}
      <DashboardHeader
        onRefresh={fetchDashboard}
        isLoading={isLoading}
      />

      {/* Historical Context Alert (Section A / Rule I) */}
      {isLocked && (
        <div
          className="alert alert-warning"
          style={{
            padding: '0.625rem 0.875rem',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem',
            backgroundColor: '#fffbeb',
            border: '1px solid #fde68a',
            color: '#92400e',
          }}
        >
          <Clock size={18} className="flex-shrink-0" />
          <div style={{ flex: 1 }}>
            <strong style={{ display: 'block', fontSize: '0.8125rem', marginBottom: '0.125rem' }}>
              أنت تستعرض عاماً دراسياً سابقاً — البيانات للعرض فقط (Historical Context)
            </strong>
            <span>
              جميع عمليات الإدخال والتعديل معطلة تلقائياً وفقاً لعقد الأمان السحابي. السجلات المعروضة للقراءة فقط.
            </span>
          </div>
          <Badge variant="warning">قراءة فقط</Badge>
        </div>
      )}

      {/* Error State */}
      {error && (
        <ErrorAlert
          message={error}
          onClose={() => setError(null)}
        />
      )}

      {/* 2. Section B: Today's Executive KPIs (6 compact metric cards) */}
      <DashboardKpiGrid metrics={data?.kpis || []} isLoading={isLoading} />

      {/* 3. Section C: "يحتاج انتباهك" (High-Priority Executive Attention Inbox) */}
      {data?.attentionAlerts && (
        <AttentionAlertsCard alerts={data.attentionAlerts} isLoading={isLoading} />
      )}

      {/* 4. Section D: School Day + Today's Attendance (Operational Pair - Side-by-side on desktop) */}
      <div className="dashboard-two-col-grid">
        {data?.schoolDayFlow && (
          <SchoolDayFlowCard flow={data.schoolDayFlow} isLoading={isLoading} />
        )}
        {data?.attendanceBreakdown && (
          <TodayAttendanceCard breakdown={data.attendanceBreakdown} isLoading={isLoading} />
        )}
      </div>

      {/* 5. Section E & F: Academic Operations & Communications (3 Compact Summary Cards) */}
      {data?.domainSummary && (
        <AcademicOperationsGrid
          summary={data.domainSummary}
          isLoading={isLoading}
        />
      )}

      {/* 6. Section G & H: Attendance Trend (7-Day) + Quick Actions (4 Promoted + Secondary Group) */}
      <div className="dashboard-two-col-grid">
        {data?.attendanceTrend && (
          <AttendanceTrendCard trend={data.attendanceTrend} isLoading={isLoading} />
        )}
        <QuickActionsGrid />
      </div>

      {/* 7. Section I: Recent Activity & Secondary Events (Positioned Lower) */}
      {data?.recentActivities && data.recentActivities.length > 0 && (
        <RecentActivityCard activities={data.recentActivities} isLoading={isLoading} />
      )}
    </div>
  );
};
