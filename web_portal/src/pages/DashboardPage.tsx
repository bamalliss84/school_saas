import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../context';
import { dashboardService, DashboardApiResponse } from '../services/dashboardService';
import { DashboardHeader } from '../components/dashboard/DashboardHeader';
import { DashboardKpiGrid } from '../components/dashboard/DashboardKpiGrid';
import { SchoolDayFlowCard } from '../components/dashboard/SchoolDayFlowCard';
import { TodayAttendanceCard } from '../components/dashboard/TodayAttendanceCard';
import { AttentionAlertsCard } from '../components/dashboard/AttentionAlertsCard';
import { PreservedOperationsGrid } from '../components/dashboard/PreservedOperationsGrid';
import { QuickActionsGrid } from '../components/dashboard/QuickActionsGrid';
import { AttendanceTrendCard } from '../components/dashboard/AttendanceTrendCard';
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
      {/* 1. Header with Breadcrumbs & Context Greeting */}
      <DashboardHeader
        onRefresh={fetchDashboard}
        isLoading={isLoading}
      />

      {/* 2. Historical Context Alert (Section I in Nano Approved Design) */}
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

      {/* 3. Top KPI Metric Cards Grid (6 cards - Nano Board A) */}
      <DashboardKpiGrid metrics={data?.kpis || []} isLoading={isLoading} />

      {/* 4. Primary Operational Grid (Section B & D) */}
      <div className="dashboard-two-col-grid">
        {/* Right Column (in RTL): سير اليوم الدراسي + الحضور اليوم */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
          {data?.schoolDayFlow && (
            <SchoolDayFlowCard flow={data.schoolDayFlow} isLoading={isLoading} />
          )}
          {data?.attendanceBreakdown && (
            <TodayAttendanceCard breakdown={data.attendanceBreakdown} isLoading={isLoading} />
          )}
        </div>

        {/* Left Column (in RTL): يحتاج انتباهك (Attention Alerts) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
          {data?.attentionAlerts && (
            <AttentionAlertsCard alerts={data.attentionAlerts} isLoading={isLoading} />
          )}
        </div>
      </div>

      {/* 5. Preserved Operations & Communications Grid (Section E & F) */}
      {data?.domainSummary && (
        <PreservedOperationsGrid
          summary={data.domainSummary}
          activities={data.recentActivities || []}
          isLoading={isLoading}
        />
      )}

      {/* 6. Bottom Row: Quick Actions (Section G) & Attendance Trend (Section H) */}
      <div className="dashboard-two-col-grid">
        <QuickActionsGrid />
        {data?.attendanceTrend && (
          <AttendanceTrendCard trend={data.attendanceTrend} isLoading={isLoading} />
        )}
      </div>
    </div>
  );
};
