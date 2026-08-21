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
import { Clock, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { Badge } from '../components/ui/Badge';

export const DashboardPage: React.FC = () => {
  const { isHistorical, isReadOnly } = useAuth();
  const [data, setData] = useState<DashboardApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showGapDetails, setShowGapDetails] = useState<boolean>(false);

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
        isAggregateGap={!data?.meta.isAggregateEndpointAvailable}
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

          {/* Transparent API Gap Note Container */}
          <div className="dashboard-gap-notice-card">
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
              }}
              onClick={() => setShowGapDetails(!showGapDetails)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Info size={15} className="text-primary flex-shrink-0" />
                <span style={{ fontSize: '0.78125rem', fontWeight: 700, color: 'var(--neutral-800)' }}>
                  تقرير توافق واجهات الـ Backend (W1-D3)
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                  {showGapDetails ? 'إخفاء التفاصيل' : 'عرض فجوات الـ API الموثقة'}
                </span>
                {showGapDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </div>
            </div>

            {showGapDetails && (
              <div style={{ marginTop: '0.75rem', paddingTop: '0.625rem', borderTop: '1px dashed var(--border-subtle)', fontSize: '0.71875rem', color: 'var(--neutral-600)', lineHeight: 1.5 }}>
                <p style={{ marginBottom: '0.375rem' }}>
                  <strong>شفافية البيانات:</strong> بناءً على قواعد المشروع الصارمة (عدم اختلاق أرقام وهمية)، يتم تصنيف المقاييس كما يلي:
                </p>
                <ul style={{ paddingRight: '1.25rem', listStyleType: 'disc', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <li>
                    <strong>حقيقي ومباشر (SUPPORTED_NOW):</strong> سجلات الحضور اليومي، إحصائيات الواجبات، كشوف الاختبارات، الإعلانات والتواصل، الجدول المدرسي، وصلاحيات السياق.
                  </li>
                  <li>
                    <strong>فجوة موثقة (GAP-DASH-01):</strong> نقطة تجميع مؤشرات الأداء الموحدة (`/api/v1/dashboard/admin/`) مجدولة للتفعيل في المرحلة <strong>Phase W2</strong> لتجنب تعدد استدعاءات الشبكة.
                  </li>
                </ul>
              </div>
            )}
          </div>
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
