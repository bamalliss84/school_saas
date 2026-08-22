import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../pages/DashboardPage';
import * as UseAuthModule from '../context/useAuth';
import { AuthContextType } from '../context/authContextDef';
import { dashboardService, DashboardApiResponse } from '../services/dashboardService';

// Mock dashboardService
vi.mock('../services/dashboardService', () => ({
  dashboardService: {
    getDashboardData: vi.fn(),
  },
}));

const mockConsistentDashboardData: DashboardApiResponse = {
  kpis: [
    {
      id: 'total_students',
      title: 'إجمالي الطلاب',
      value: (11).toLocaleString('ar-EG'),
      subtext: 'طالب مسجل نشط',
      trend: { direction: 'neutral', value: 'نشط' },
      iconName: 'users',
      color: 'var(--primary-600)',
      bgColor: 'var(--primary-50)',
      isAvailable: true,
    },
    {
      id: 'total_teachers',
      title: 'إجمالي المعلمين',
      value: '—',
      subtext: 'غير متوفر حالياً',
      iconName: 'teachers',
      color: 'var(--indigo-600)',
      bgColor: 'var(--indigo-50)',
      isAvailable: false,
    },
    {
      id: 'classes_sections',
      title: 'الفصول والشعب',
      value: '—',
      subtext: 'غير متوفر حالياً',
      iconName: 'classes',
      color: 'var(--neutral-700)',
      bgColor: 'var(--neutral-100)',
      isAvailable: false,
    },
    {
      id: 'attendance_rate',
      title: 'حضور الطلاب اليوم',
      value: '90.9%',
      subtext: 'نسبة الحضور التراكمية اليوم',
      trend: { direction: 'up', value: '▲ 90.9%' },
      iconName: 'attendance',
      color: 'var(--success-600)',
      bgColor: 'var(--success-50)',
      isAvailable: true,
    },
    {
      id: 'absent_students',
      title: 'غياب الطلاب',
      value: (1).toLocaleString('ar-EG'),
      subtext: 'طالب غائب اليوم',
      trend: { direction: 'down', value: 'متابعة' },
      iconName: 'absent',
      color: 'var(--danger-600)',
      bgColor: 'var(--danger-50)',
      isAvailable: true,
    },
    {
      id: 'late_students',
      title: 'المتأخرون',
      value: (0).toLocaleString('ar-EG'),
      subtext: 'حالة تأخر مرصودة',
      iconName: 'late',
      color: 'var(--warning-600)',
      bgColor: 'var(--warning-50)',
      isAvailable: true,
    },
  ],
  schoolDayFlow: {
    currentPeriod: 4,
    completedPeriods: 3,
    totalPeriods: 42,
    startTime: '07:00',
    currentTime: '10:35',
    endTime: '13:30',
    progressPercent: 55,
    isConfigured: true,
  },
  attendanceBreakdown: {
    studentAttendanceRate: 90.9,
    teacherPresentCount: 0,
    teacherTotalCount: 0,
    presentCount: 10,
    absentCount: 1,
    lateCount: 0,
    excusedCount: 0,
    pendingCount: 0,
  },
  attentionAlerts: [
    {
      id: 'alert-1',
      severity: 'danger',
      title: '1 طالب غائب اليوم يتطلب المتابعة والتأكيد مع أولياء الأمور',
      actionLabel: 'مراجعة الغياب',
      actionRoute: '/attendance',
    },
  ],
  domainSummary: {
    homework: {
      activeCount: 4,
      dueTodayCount: 1,
      pendingGradingCount: 2,
      averageSubmissionRate: 85,
    },
    exams: {
      upcomingCount: 2,
      todayCount: 0,
      awaitingApprovalCount: 1,
      averagePassRate: 90,
    },
    communications: {
      urgentMessagesCount: 1,
      activeConversationsCount: 1,
      activeAnnouncementsCount: 3,
      unreadInquiriesCount: 0,
    },
  },
  recentActivities: [
    {
      id: 'act-1',
      title: 'تم تسجيل الدخول إلى لوحة الإدارة المدرسية بنجاح',
      timeAgo: 'الآن',
      timestamp: new Date().toISOString(),
      type: 'system',
    },
  ],
  attendanceTrend: [
    { day: 'الإثنين', dayShort: 'Mon', rate: 0, date: '2026-08-16' },
    { day: 'الثلاثاء', dayShort: 'Tue', rate: 0, date: '2026-08-17' },
    { day: 'الأربعاء', dayShort: 'Wed', rate: 0, date: '2026-08-18' },
    { day: 'الخميس', dayShort: 'Thu', rate: 0, date: '2026-08-19' },
    { day: 'الجمعة', dayShort: 'Fri', rate: 0, date: '2026-08-20' },
    { day: 'السبت', dayShort: 'Sat', rate: 0, date: '2026-08-21' },
    { day: 'الأحد', dayShort: 'Sun', rate: 90.9, date: '2026-08-22' },
  ],
  meta: {
    isAggregateEndpointAvailable: false,
  },
};

const defaultAuthContextValue: AuthContextType = {
  user: {
    id: 1,
    username: 'admin_ahmed',
    email: 'admin@alnoor.edu.sa',
    full_name: 'أحمد محمد',
    role: 'school_admin',
  },
  activeMembership: {
    membership_id: 10,
    school: { id: 1, name: 'مدرسة النور الأهلية' },
    role: 'school_admin',
    academic_year: { id: 1, name: 'العام الدراسي 2026/2027' },
    access_mode: 'read_write',
    status: 'active',
    is_default: true,
    is_current_school: true,
    can_write: true,
    start_date: '2026-09-01',
    end_date: null,
    last_used_at: null,
    unread_notifications_count: 3,
    unread_conversations_count: 2,
  },
  allMemberships: [],
  isLoading: false,
  isAuthenticated: true,
  isHistorical: false,
  isReadOnly: false,
  isSchoolAdmin: true,
  showContextModal: false,
  login: vi.fn(),
  logout: vi.fn(),
  switchContext: vi.fn(),
  refreshContexts: vi.fn(),
  setShowContextModal: vi.fn(),
};

describe('DashboardPage (W1-D3 Operational Dashboard Production Closure)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(dashboardService.getDashboardData).mockResolvedValue(mockConsistentDashboardData);
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(defaultAuthContextValue);
  });

  it('renders clean School Admin UI WITHOUT any GAP-DASH-01 or developer diagnostic labels', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    // Wait for content to render
    expect(await screen.findByText(/أحمد محمد/)).toBeInTheDocument();

    // Verify ABSOLUTE ABSENCE of developer diagnostics in School Admin UI
    expect(screen.queryByText(/GAP-DASH/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/W2\/W3 Gap/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/تقرير توافق/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/شفافية البيانات/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/فجوة موثقة/i)).not.toBeInTheDocument();
  });

  it('renders mathematically consistent scoped KPI values and attendance breakdown', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    // Verify Total Students is 11
    expect(await screen.findByText('إجمالي الطلاب')).toBeInTheDocument();
    expect(screen.getByText((11).toLocaleString('ar-EG'))).toBeInTheDocument();

    // Verify Attendance Rate & Consistent Absent / Late counts
    expect(screen.getByText('حضور الطلاب اليوم')).toBeInTheDocument();
    expect(screen.getByText('90.9%')).toBeInTheDocument();
    expect(screen.getByText('▲ 90.9%')).toBeInTheDocument();

    // Verify Absent count is 1 (not 76!)
    expect(screen.getByText('غياب الطلاب')).toBeInTheDocument();
    expect(screen.getAllByText((1).toLocaleString('ar-EG')).length).toBeGreaterThan(0);

    // Verify Unavailable metrics render safe "—" rather than fabricated numbers
    expect(screen.getByText('إجمالي المعلمين')).toBeInTheDocument();
    expect(screen.getByText('الفصول والشعب')).toBeInTheDocument();
    const dashPlaceholders = screen.getAllByText('—');
    expect(dashPlaceholders.length).toBeGreaterThanOrEqual(2);

    // Verify Today Attendance Card numbers: Present = 10, Absent = 1
    expect(screen.getByText('الحضور اليوم')).toBeInTheDocument();
    expect(screen.getByText((10).toLocaleString('ar-EG'))).toBeInTheDocument();
  });

  it('renders Section B (سير اليوم الدراسي) with flow statistics and timeline nodes', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('سير اليوم الدراسي')).toBeInTheDocument();
    expect(screen.getByText('الحصص الحالية')).toBeInTheDocument();
    expect(screen.getByText('الحصص المكتملة')).toBeInTheDocument();
    expect(screen.getByText('الحصص المجدولة')).toBeInTheDocument();

    expect(screen.getByText('بداية اليوم الدراسي')).toBeInTheDocument();
    expect(screen.getByText('07:00')).toBeInTheDocument();
    expect(screen.getByText('10:35')).toBeInTheDocument();
    expect(screen.getByText('13:30')).toBeInTheDocument();

    expect(screen.getByText('عرض الجدول اليومي')).toBeInTheDocument();
    expect(screen.getByText('متابعة الحصص غير المسجلة')).toBeInTheDocument();
  });

  it('renders Preserved Operations grid: Homework, Exams, Communications, and Activity feed', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('الواجبات')).toBeInTheDocument();
    expect(screen.getByText('عرض الواجبات')).toBeInTheDocument();

    expect(screen.getByText('الاختبارات والنتائج')).toBeInTheDocument();
    expect(screen.getByText('عرض الاختبارات والنتائج')).toBeInTheDocument();

    expect(screen.getByText('التواصل والإشعارات')).toBeInTheDocument();
    expect(screen.getByText('عرض الرسائل')).toBeInTheDocument();
    expect(screen.getAllByText('إنشاء إعلان').length).toBeGreaterThan(0);

    expect(screen.getByText('آخر النشاطات')).toBeInTheDocument();
  });

  it('renders Section G Quick Actions Grid and Section H Attendance Trend chart', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('إجراءات سريعة')).toBeInTheDocument();
    expect(screen.getByText('إضافة طالب')).toBeInTheDocument();
    expect(screen.getByText('إضافة معلم')).toBeInTheDocument();
    expect(screen.getByText('مراجعة الحضور')).toBeInTheDocument();
    expect(screen.getByText('تصدير Excel')).toBeInTheDocument();

    // Section H Trend
    expect(screen.getByText('اتجاه الحضور خلال آخر 7 أيام')).toBeInTheDocument();
    expect(screen.getByText('Mon')).toBeInTheDocument();
    expect(screen.getByText('Sun')).toBeInTheDocument();
  });

  it('enforces Historical Context read-only state by disabling mutation buttons (Section I)', async () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
      ...defaultAuthContextValue,
      isHistorical: true,
      isReadOnly: true,
      activeMembership: defaultAuthContextValue.activeMembership
        ? {
            ...defaultAuthContextValue.activeMembership,
            status: 'historical',
            access_mode: 'read_only',
            can_write: false,
          }
        : null,
    });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    // Verify Historical Banner
    expect(await screen.findByText(/أنت تستعرض عاماً دراسياً سابقاً/)).toBeInTheDocument();

    // Verify mutation quick action buttons are disabled
    const addStudentBtn = screen.getByRole('button', { name: /إضافة طالب/ });
    expect(addStudentBtn).toBeDisabled();

    const addTeacherBtn = screen.getByRole('button', { name: /إضافة معلم/ });
    expect(addTeacherBtn).toBeDisabled();

    // Verify non-mutating buttons remain enabled
    const exportExcelBtn = screen.getByRole('button', { name: /تصدير Excel/ });
    expect(exportExcelBtn).not.toBeDisabled();

    const reviewAttendanceBtn = screen.getByRole('button', { name: /مراجعة الحضور/ });
    expect(reviewAttendanceBtn).not.toBeDisabled();
  });

  it('renders safe empty state for attention alerts when no urgent alerts exist', async () => {
    vi.mocked(dashboardService.getDashboardData).mockResolvedValue({
      ...mockConsistentDashboardData,
      attentionAlerts: [],
    });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('لا توجد تنبيهات عاجلة اليوم')).toBeInTheDocument();
    expect(screen.getByText('جميع العمليات التشغيلية تسير بانتظام')).toBeInTheDocument();
  });
});
