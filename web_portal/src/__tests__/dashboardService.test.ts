import { describe, it, expect, vi, beforeEach } from 'vitest';
import { dashboardService } from '../services/dashboardService';
import { apiClient } from '../services/apiClient';

vi.mock('../services/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('dashboardService - Mathematical Consistency & Safe Fallbacks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('guarantees attendance numbers never exceed total student population and sums consistently', async () => {
    // Mock 11 total students
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url.includes('/dashboard/admin/')) {
        throw new Error('Not implemented');
      }
      if (url.includes('/students/')) {
        return { count: 11, results: [] } as unknown as never;
      }
      if (url.includes('/attendance/daily/')) {
        return {
          date: '2026-08-22',
          total_students: 11,
          recorded: 11,
          present: 10,
          absent: 1,
          late: 0,
          excused: 0,
          not_recorded: 0,
        } as unknown as never;
      }
      if (url.includes('/timetable/config/')) {
        return { is_configured: true, periods_per_day: 7 } as unknown as never;
      }
      if (url.includes('/communication/badges/')) {
        return { unread_notifications: 2, unread_conversations: 1, support_tickets_pending: 0 } as unknown as never;
      }
      return {} as unknown as never;
    });

    const result = await dashboardService.getDashboardData();

    // Verify Total Students KPI
    const totalStudentsKpi = result.kpis.find((k) => k.id === 'total_students');
    expect(totalStudentsKpi?.value).toBe((11).toLocaleString('ar-EG'));

    // Verify Attendance Breakdown
    const { presentCount, absentCount, lateCount, excusedCount, pendingCount } = result.attendanceBreakdown;
    expect(presentCount).toBeLessThanOrEqual(11);
    expect(absentCount).toBeLessThanOrEqual(11);
    expect(lateCount).toBeLessThanOrEqual(11);
    expect(excusedCount).toBeLessThanOrEqual(11);

    // Sum must equal total population exactly
    const sum = presentCount + absentCount + lateCount + excusedCount + pendingCount;
    expect(sum).toBe(11);

    // Attendance Rate KPI
    const rateKpi = result.kpis.find((k) => k.id === 'attendance_rate');
    expect(rateKpi?.value).toBe('90.9%');
  });

  it('renders safe unavailable states (— / غير متاح) when backend endpoints are unavailable without fabricating numbers', async () => {
    // All endpoints reject / fail
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
      if (url.includes('/students/')) {
        return { count: 25, results: [] } as unknown as never;
      }
      if (url.includes('/attendance/daily/')) {
        return {
          date: '2026-08-22',
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
