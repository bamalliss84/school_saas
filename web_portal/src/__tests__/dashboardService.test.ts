import { describe, it, expect, vi, beforeEach } from 'vitest';
import { dashboardService } from '../services/dashboardService';
import { apiClient } from '../services/apiClient';

vi.mock('../services/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('dashboardService - Active Current Student KPI & Mathematical Scoping', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('School A: scopes total_students to 10 active current students despite 11 historical enrollments in students API', async () => {
    // School A: unparameterized /students/ returns 11 (due to 1 transferred student from previous year)
    // /attendance/daily/ returns 10 (authoritative active current population)
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url.includes('/dashboard/admin/')) {
        throw new Error('Not implemented');
      }
      if (url.includes('/students/')) {
        return { count: 11, results: [] } as unknown as never;
      }
      if (url.includes('/attendance/daily/')) {
        return {
          date: '2026-08-23',
          total_students: 10,
          recorded: 10,
          present: 9,
          absent: 1,
          late: 0,
          excused: 0,
          not_recorded: 0,
        } as unknown as never;
      }
      return {} as unknown as never;
    });

    const result = await dashboardService.getDashboardData();

    // Verify Total Students KPI is 10, NOT 11
    const totalStudentsKpi = result.kpis.find((k) => k.id === 'total_students');
    expect(totalStudentsKpi?.value).toBe((10).toLocaleString('ar-EG'));
    expect(totalStudentsKpi?.subtext).toBe('طالب مسجل نشط');

    // Verify attendance breakdown bounded to 10
    const { presentCount, absentCount, lateCount, excusedCount, pendingCount } = result.attendanceBreakdown;
    expect(presentCount + absentCount + lateCount + excusedCount + pendingCount).toBe(10);
    expect(presentCount).toBe(9);
    expect(absentCount).toBe(1);

    // Verify contextual subtext
    const rateKpi = result.kpis.find((k) => k.id === 'attendance_rate');
    expect(rateKpi?.subtext).toBe(`${(9).toLocaleString('ar-EG')} من ${(10).toLocaleString('ar-EG')} طالب`);
  });

  it('School B: scopes total_students to 11 active current students', async () => {
    // School B: 11 active current students (including transferred student who is active here)
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url.includes('/dashboard/admin/')) {
        throw new Error('Not implemented');
      }
      if (url.includes('/students/')) {
        return { count: 11, results: [] } as unknown as never;
      }
      if (url.includes('/attendance/daily/')) {
        return {
          date: '2026-08-23',
          total_students: 11,
          recorded: 11,
          present: 10,
          absent: 1,
          late: 0,
          excused: 0,
          not_recorded: 0,
        } as unknown as never;
      }
      return {} as unknown as never;
    });

    const result = await dashboardService.getDashboardData();

    const totalStudentsKpi = result.kpis.find((k) => k.id === 'total_students');
    expect(totalStudentsKpi?.value).toBe((11).toLocaleString('ar-EG'));

    const { presentCount, absentCount, lateCount, excusedCount, pendingCount } = result.attendanceBreakdown;
    expect(presentCount + absentCount + lateCount + excusedCount + pendingCount).toBe(11);
    expect(presentCount).toBe(10);
  });

  it('falls back to /students/ count only when daily attendance endpoint is unavailable', async () => {
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url.includes('/students/')) {
        return { count: 15, results: [] } as unknown as never;
      }
      if (url.includes('/attendance/daily/')) {
        throw new Error('Endpoint not available');
      }
      return {} as unknown as never;
    });

    const result = await dashboardService.getDashboardData();

    const totalStudentsKpi = result.kpis.find((k) => k.id === 'total_students');
    expect(totalStudentsKpi?.value).toBe((15).toLocaleString('ar-EG'));
    expect(totalStudentsKpi?.isAvailable).toBe(true);
  });

  it('renders safe unavailable states (— / غير متاح) when backend endpoints are unavailable without fabricating numbers', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'));

    const result = await dashboardService.getDashboardData();

    // Verify safe KPI values
    const totalStudentsKpi = result.kpis.find((k) => k.id === 'total_students');
    expect(totalStudentsKpi?.value).toBe('—');
    expect(totalStudentsKpi?.subtext).toBe('غير متاح حالياً');
    expect(totalStudentsKpi?.isAvailable).toBe(false);

    const totalTeachersKpi = result.kpis.find((k) => k.id === 'total_teachers');
    expect(totalTeachersKpi?.value).toBe('—');
    expect(totalTeachersKpi?.subtext).toBe('غير متوفر حالياً');
    expect(totalTeachersKpi?.isAvailable).toBe(false);

    const classesKpi = result.kpis.find((k) => k.id === 'classes_sections');
    expect(classesKpi?.value).toBe('—');
    expect(classesKpi?.subtext).toBe('غير متوفر حالياً');
    expect(classesKpi?.isAvailable).toBe(false);

    const attendanceRateKpi = result.kpis.find((k) => k.id === 'attendance_rate');
    expect(attendanceRateKpi?.value).toBe('—');
    expect(attendanceRateKpi?.isAvailable).toBe(false);

    // Verify no fabricated numbers in breakdown
    expect(result.attendanceBreakdown.presentCount).toBe(0);
    expect(result.attendanceBreakdown.absentCount).toBe(0);
    expect(result.attendanceBreakdown.lateCount).toBe(0);
    expect(result.attendanceBreakdown.excusedCount).toBe(0);
    expect(result.attendanceBreakdown.teacherPresentCount).toBe(0);
    expect(result.attendanceBreakdown.teacherTotalCount).toBe(0);
  });

  it('handles unrecorded school day safely when total students exist but no sessions are recorded yet', async () => {
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url.includes('/attendance/daily/')) {
        return {
          date: '2026-08-23',
          total_students: 25,
          recorded: 0,
          present: 0,
          absent: 0,
          late: 0,
          excused: 0,
          not_recorded: 25,
        } as unknown as never;
      }
      return {} as unknown as never;
    });

    const result = await dashboardService.getDashboardData();

    expect(result.attendanceBreakdown.pendingCount).toBe(25);
    expect(result.attendanceBreakdown.presentCount).toBe(0);

    const rateKpi = result.kpis.find((k) => k.id === 'attendance_rate');
    expect(rateKpi?.value).toBe('—');
    expect(rateKpi?.subtext).toBe('لم يُسجل الحضور اليوم بعد');
  });
});
