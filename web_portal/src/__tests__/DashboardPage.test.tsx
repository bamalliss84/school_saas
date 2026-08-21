import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../pages/DashboardPage';
import * as UseAuthModule from '../context/useAuth';
import { dashboardService, DashboardApiResponse } from '../services/dashboardService';

// Mock dashboardService
vi.mock('../services/dashboardService', () => ({
  dashboardService: {
    getDashboardData: vi.fn(),
  },
}));

const mockDashboardData: DashboardApiResponse = {
  kpis: [
    {
      id: 'total_students',
      title: 'إجمالي الطلاب',
      value: '1,248',
      subtext: 'طالب مسجل نشط',
      trend: { direction: 'neutral', value: 'نشط' },
      iconName: 'users',
      color: 'var(--primary-600)',
      bgColor: 'var(--primary-50)',
      isAvailable: false,
      gapCode: 'GAP-DASH-01',
      gapDescription: 'في انتظار تفعيل الـ CRUD الموحد للطلاب (W2/W5)',
    },
    {
      id: 'total_teachers',
      title: 'إجمالي المعلمين',
      value: '86',
      subtext: 'كادر تدريسي معتمد',
      iconName: 'teachers',
      color: 'var(--indigo-600)',
      bgColor: 'var(--indigo-50)',
      isAvailable: false,
      gapCode: 'GAP-DASH-01',
    },
    {
      id: 'classes_sections',
      title: 'الفصول والشعب',
      value: '42',
      subtext: 'شعبة دراسية مفعلة',
      iconName: 'classes',
      color: 'var(--neutral-700)',
      bgColor: 'var(--neutral-100)',
      isAvailable: false,
    },
    {
      id: 'attendance_rate',
      title: 'حضور الطلاب اليوم',
      value: '91.8%',
      subtext: 'نسبة الحضور التراكمية',
      trend: { direction: 'up', value: '▲ 91.8%' },
      iconName: 'attendance',
      color: 'var(--success-600)',
      bgColor: 'var(--success-50)',
      isAvailable: true,
    },
    {
      id: 'absent_students',
      title: 'غياب الطلاب',
      value: '76',
      subtext: 'طالب غائب اليوم',
      iconName: 'absent',
      color: 'var(--danger-600)',
      bgColor: 'var(--danger-50)',
      isAvailable: true,
    },
    {
      id: 'late_students',
      title: 'المتأخرون',
      value: '18',
      subtext: 'حالة تأخر مرصودة',
      iconName: 'late',
      color: 'var(--warning-600)',
      bgColor: 'var(--warning-50)',
      isAvailable: true,
    },
  ],
  schoolDayFlow: {
    currentPeriod: 6,
    completedPeriods: 18,
    totalPeriods: 42,
    startTime: '07:00',
    currentTime: '10:35',
    endTime: '13:30',
    progressPercent: 55,
    isConfigured: true,
  },
  attendanceBreakdown: {
    studentAttendanceRate: 91.8,
    teacherPresentCount: 39,
    teacherTotalCount: 42,
    presentCount: 1145,
    absentCount: 76,
    lateCount: 18,
    excusedCount: 9,
    pendingCount: 0,
  },
  attentionAlerts: [
    {
      id: 'alert-1',
      severity: 'danger',
      title: '12 طالباً تجاوزوا حد الغياب المسموح (إنذار نهائي)',
      actionLabel: 'مراجعة',
      actionRoute: '/attendance',
    },
    {
      id: 'alert-2',
      severity: 'danger',
      title: '8 طلاب لديهم سجل تأخر متكرر هذا الأسبوع',
      actionLabel: 'مراجعة',
      actionRoute: '/attendance',
    },
    {
      id: 'alert-3',
      severity: 'warning',
      title: '3 شعب لم يُسجل حضورها الصباحي اليوم حتى الآن',
      actionLabel: 'عرض الشعب',
      actionRoute: '/attendance',
    },
    {
      id: 'alert-4',
      severity: 'warning',
      title: '5 كشوف درجات بانتظار الاعتماد الإداري النهائي',
      actionLabel: 'اعتماد النتائج',
      actionRoute: '/exams',
    },
  ],
  domainSummary: {
    homework: {
      activeCount: 24,
      dueTodayCount: 8,
      pendingGradingCount: 14,
      averageSubmissionRate: 84,
    },
    exams: {
      upcomingCount: 3,
      todayCount: 1,
      awaitingApprovalCount: 5,
      averagePassRate: 88,
    },
    communications: {
      urgentMessagesCount: 4,
      activeConversationsCount: 12,
      activeAnnouncementsCount: 6,
      unreadInquiriesCount: 2,
    },
  },
  recentActivities: [
    {
      id: 'act-1',
      title: 'تم اعتماد نتائج اختبار الرياضيات للصف الثالث المتوسط',
      timeAgo: 'منذ 5 دقائق',
      timestamp: new Date().toISOString(),
      type: 'exam',
    },
  ],
  attendanceTrend: [
    { day: 'الإثنين', dayShort: 'Mon', rate: 70, date: '2026-08-16' },
    { day: 'الثلاثاء', dayShort: 'Tue', rate: 78, date: '2026-08-17' },
    { day: 'الأربعاء', dayShort: 'Wed', rate: 75, date: '2026-08-18' },
    { day: 'الخميس', dayShort: 'Thu', rate: 80, date: '2026-08-19' },
    { day: 'الجمعة', dayShort: 'Fri', rate: 68, date: '2026-08-20' },
    { day: 'السبت', dayShort: 'Sat', rate: 74, date: '2026-08-21' },
    { day: 'الأحد', dayShort: 'Sun', rate: 72, date: '2026-08-22' },
  ],
  meta: {
    isAggregateEndpointAvailable: false,
    dataSource: 'aggregate_api_gap',
  },
};

const defaultAuthContextValue = {
  user: {
    id: 1,
    username: 'admin_ahmed',
    email: 'admin@alnoor.edu.sa',
    first_name: 'أحمد',
    last_name: 'محمد',
    full_name: 'أحمد محمد',
    role: 'school_admin',
    is_active: true,
  },
  activeMembership: {
    membership_id: 10,
    school: { id: 1, name: 'مدرسة النور الأهلية', code: 'NOOR', is_active: true },
    role: 'school_admin',
    role_display: 'مدير المدرسة',
    academic_year: { id: 1, name: 'العام الدراسي 2026/2027', is_active: true },
    access_mode: 'full_access',
    status: 'active',
    is_default: true,
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

describe('DashboardPage (W1-D3 Operational Dashboard)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(dashboardService.getDashboardData).mockResolvedValue(mockDashboardData);
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(defaultAuthContextValue as any);
  });

  it('renders header, greeting banner, and all 6 KPI cards according to approved Nano D3', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    // Check Header & Context Greeting
    expect(await screen.findByText(/أحمد محمد/)).toBeInTheDocument();
    expect(screen.getByText('مدرسة النور الأهلية')).toBeInTheDocument();
    expect(screen.getByText('لوحة التحكم التشغيلية')).toBeInTheDocument();

    // Check All 6 KPI Cards
    expect(screen.getByText('إجمالي الطلاب')).toBeInTheDocument();
    expect(screen.getByText('1,248')).toBeInTheDocument();

    expect(screen.getByText('إجمالي المعلمين')).toBeInTheDocument();
    expect(screen.getByText('86')).toBeInTheDocument();

    expect(screen.getByText('الفصول والشعب')).toBeInTheDocument();
    expect(screen.getAllByText('42').length).toBeGreaterThan(0);

    expect(screen.getByText('حضور الطلاب اليوم')).toBeInTheDocument();
    expect(screen.getByText('91.8%')).toBeInTheDocument();
    expect(screen.getByText('▲ 91.8%')).toBeInTheDocument();

    expect(screen.getByText('غياب الطلاب')).toBeInTheDocument();
    expect(screen.getByText('76')).toBeInTheDocument();

    expect(screen.getByText('المتأخرون')).toBeInTheDocument();
    expect(screen.getAllByText('18').length).toBeGreaterThan(0);
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

  it('renders Section D (الحضور اليوم) and Attention Alerts with action buttons', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('الحضور اليوم')).toBeInTheDocument();
    expect(screen.getByText('حضور المعلمين اليوم')).toBeInTheDocument();
    expect(screen.getByText('حاضر')).toBeInTheDocument();
    expect(screen.getByText('غائب')).toBeInTheDocument();
    expect(screen.getByText('متأخر')).toBeInTheDocument();

    // Attention Alerts
    expect(screen.getByText('يحتاج انتباهك')).toBeInTheDocument();
    expect(screen.getByText(/12 طالباً تجاوزوا حد الغياب/)).toBeInTheDocument();
    expect(screen.getByText(/3 شعب لم يُسجل حضورها/)).toBeInTheDocument();
    expect(screen.getByText('اعتماد النتائج')).toBeInTheDocument();
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
    expect(screen.getByText(/تم اعتماد نتائج اختبار الرياضيات/)).toBeInTheDocument();
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
      activeMembership: {
        ...defaultAuthContextValue.activeMembership,
        status: 'historical',
        access_mode: 'read_only',
      },
    } as any);

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

  it('toggles transparent API Gap report details when clicked', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    const gapToggle = await screen.findByText('تقرير توافق واجهات الـ Backend (W1-D3)');
    expect(gapToggle).toBeInTheDocument();

    // Click to open details
    fireEvent.click(gapToggle);

    expect(await screen.findByText(/شفافية البيانات/)).toBeInTheDocument();
    expect(screen.getAllByText(/GAP-DASH-01/).length).toBeGreaterThan(0);
  });
});
