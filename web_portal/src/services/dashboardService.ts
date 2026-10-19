import { apiClient } from './apiClient';
import {
  KpiMetric,
  SchoolDayFlow,
  AttendanceBreakdown,
  AttentionAlert,
  DomainOperationsSummary,
  ActivityItem,
  AttendanceTrendPoint,
} from '../types/dashboard';

export interface DashboardApiResponse {
  kpis: KpiMetric[];
  schoolDayFlow: SchoolDayFlow;
  attendanceBreakdown: AttendanceBreakdown;
  attentionAlerts: AttentionAlert[];
  domainSummary: DomainOperationsSummary;
  recentActivities: ActivityItem[];
  attendanceTrend: AttendanceTrendPoint[];
  meta: {
    isAggregateEndpointAvailable: boolean;
    activeSchoolName?: string;
    academicYearName?: string;
  };
}

interface DailyAttendanceResponse {
  date?: string;
  total_students?: number;
  recorded?: number;
  present?: number;
  absent?: number;
  late?: number;
  excused?: number;
  not_recorded?: number;
}

export const dashboardService = {
  getDashboardData: async (): Promise<DashboardApiResponse> => {
    // 1. Attempt to fetch unified aggregate endpoint if implemented in backend
    try {
      const aggregateData = await apiClient.get<DashboardApiResponse>('/dashboard/admin/');
      if (aggregateData && Array.isArray(aggregateData.kpis)) {
        return {
          ...aggregateData,
          meta: {
            ...aggregateData.meta,
            isAggregateEndpointAvailable: true,
          },
        };
      }
    } catch {
      // Endpoint not available yet; proceed to query scoped individual domain APIs
    }

    // 2. Fetch scoped data from active tenant context
    let studentCount: number | null = null;
    let teacherCount: number | null = null;
    let classroomCount: number | null = null;
    let sectionCount: number | null = null;
    let dailyAttendance: DailyAttendanceResponse | null = null;
    let unreadInboxCount = 0;
    let unreadNotificationsCount = 0;
    let timetableConfigured = false;
    let timetablePeriodsPerDay = 7;
    let activeHomeworkCount = 0;
    let pendingGradingCount = 0;
    let dueTodayHomeworkCount = 0;
    let homeworkSubmissionRate = 0;
    let examsCount = 0;
    const todayExamsCount = 0;
    let awaitingApprovalExamsCount = 0;
    const examPassRate = 0;

    // A. Student Population Scope (GET /students/?page_size=1)
    try {
      const studentsRes = await apiClient.get<{ count?: number; results?: unknown[] }>('/students/?page_size=1');
      if (typeof studentsRes?.count === 'number') {
        studentCount = studentsRes.count;
      }
    } catch {
      studentCount = null;
    }

    // A2. Teacher/Class/Section population for executive KPIs
    try {
      const teachersRes = await apiClient.get<{ count?: number; results?: unknown[] }>('/admin/teachers/?page_size=1');
      teacherCount = typeof teachersRes?.count === 'number' ? teachersRes.count : null;
    } catch { teacherCount = null; }
    try {
      const classesRes = await apiClient.get<{ count?: number; results?: Array<{ sections_count?: number }> }>('/admin/classrooms/?page_size=200');
      classroomCount = typeof classesRes?.count === 'number' ? classesRes.count : (classesRes?.results?.length ?? null);
      if (Array.isArray(classesRes?.results)) {
        sectionCount = classesRes.results.reduce((sum, row) => sum + (Number(row.sections_count) || 0), 0);
      }
    } catch {
      try {
        const classesRes = await apiClient.get<{ count?: number; results?: unknown[] }>('/classrooms/?page_size=200');
        classroomCount = typeof classesRes?.count === 'number' ? classesRes.count : (classesRes?.results?.length ?? null);
      } catch { classroomCount = null; }
      sectionCount = null;
    }

    // B. Daily Attendance Scope (GET /attendance/daily/)
    try {
      const attendanceRes = await apiClient.get<DailyAttendanceResponse>('/attendance/daily/');
      if (attendanceRes && typeof attendanceRes === 'object') {
        dailyAttendance = attendanceRes;
      }
    } catch {
      dailyAttendance = null;
    }

    // C. Communication Badges (GET /communication/badges/)
    try {
      const badgesRes = await apiClient.get<{
        unread_notifications?: number;
        unread_conversations?: number;
        support_tickets_pending?: number;
      }>('/communication/badges/');
      if (badgesRes) {
        unreadNotificationsCount = badgesRes.unread_notifications ?? 0;
        unreadInboxCount = (badgesRes.unread_conversations ?? 0) + (badgesRes.support_tickets_pending ?? 0);
      }
    } catch {
      unreadNotificationsCount = 0;
      unreadInboxCount = 0;
    }

    // D. Timetable Configuration (GET /timetable/config/)
    try {
      const ttConfig = await apiClient.get<{
        working_days?: number[];
        periods_per_day?: number;
        period_duration_minutes?: number;
        is_configured?: boolean;
      }>('/timetable/config/');
      if (ttConfig) {
        timetableConfigured = ttConfig.is_configured !== false;
        timetablePeriodsPerDay = ttConfig.periods_per_day || 7;
      }
    } catch {
      timetableConfigured = false;
    }

    // E. Homework Dashboard / Summary (GET /homework/dashboard/)
    try {
      const hwRes = await apiClient.get<{
        active_homework_count?: number;
        pending_grading_count?: number;
        due_today_count?: number;
        average_submission_rate?: number;
      }>('/homework/dashboard/');
      if (hwRes) {
        activeHomeworkCount = hwRes.active_homework_count ?? 0;
        pendingGradingCount = hwRes.pending_grading_count ?? 0;
        dueTodayHomeworkCount = hwRes.due_today_count ?? 0;
        homeworkSubmissionRate = hwRes.average_submission_rate ?? 0;
      }
    } catch {
      // Homework endpoint fallback
    }

    // F. Exams Summary (GET /exams/)
    try {
      const examsRes = await apiClient.get<{ count?: number; results?: Array<{ is_published?: boolean; approval_status?: string }> }>('/exams/?page_size=10');
      if (examsRes && typeof examsRes.count === 'number') {
        examsCount = examsRes.count;
        if (Array.isArray(examsRes.results)) {
          awaitingApprovalExamsCount = examsRes.results.filter(
            (e) => e.approval_status === 'pending' || e.approval_status === 'submitted'
          ).length;
        }
      }
    } catch {
      // Exams endpoint fallback
    }

    // Authoritative operational active student population in active academic year context:
    // Primary: dailyAttendance.total_students (derived strictly from active, current enrollments in the active academic year)
    // Fallback: studentCount from /students/ if daily attendance report is unavailable
    const totalStudentsFromReport = typeof dailyAttendance?.total_students === 'number' ? dailyAttendance.total_students : null;
    const effectiveTotalStudents: number | null = totalStudentsFromReport !== null ? totalStudentsFromReport : studentCount;

    const presentRaw = dailyAttendance?.present ?? 0;
    const absentRaw = dailyAttendance?.absent ?? 0;
    const lateRaw = dailyAttendance?.late ?? 0;
    const excusedRaw = dailyAttendance?.excused ?? 0;
    const recordedRaw = dailyAttendance?.recorded ?? (presentRaw + absentRaw + lateRaw + excusedRaw);

    // Bounded and consistency-checked values:
    // present, absent, late, excused cannot exceed effectiveTotalStudents
    let presentCount = presentRaw;
    let absentCount = absentRaw;
    let lateCount = lateRaw;
    let excusedCount = excusedRaw;
    let recordedCount = recordedRaw;
    let pendingCount = 0;

    if (effectiveTotalStudents !== null && effectiveTotalStudents > 0) {
      presentCount = Math.min(presentRaw, effectiveTotalStudents);
      absentCount = Math.min(absentRaw, effectiveTotalStudents);
      lateCount = Math.min(lateRaw, effectiveTotalStudents);
      excusedCount = Math.min(excusedRaw, effectiveTotalStudents);
      recordedCount = Math.min(presentCount + absentCount + lateCount + excusedCount, effectiveTotalStudents);
      pendingCount = Math.max(effectiveTotalStudents - recordedCount, 0);
    } else {
      presentCount = 0;
      absentCount = 0;
      lateCount = 0;
      excusedCount = 0;
      recordedCount = 0;
      pendingCount = effectiveTotalStudents ?? 0;
    }

    // Determine Attendance Rate:
    // Only compute percentage if there is a positive population AND at least one session recorded today
    let attendanceRateNumber = 0;
    let attendanceRateDisplay = '—';
    let absentDisplay = '—';
    let lateDisplay = '—';
    let hasLiveAttendance = false;

    if (effectiveTotalStudents !== null && effectiveTotalStudents > 0 && recordedCount > 0) {
      const attended = presentCount + lateCount;
      attendanceRateNumber = Math.round((attended / recordedCount) * 1000) / 10;
      attendanceRateDisplay = `${attendanceRateNumber}%`;
      absentDisplay = absentCount.toLocaleString('ar-EG');
      lateDisplay = lateCount.toLocaleString('ar-EG');
      hasLiveAttendance = true;
    } else if (effectiveTotalStudents !== null && effectiveTotalStudents > 0 && recordedCount === 0) {
      // Enrolled students exist, but no attendance recorded yet today
      attendanceRateDisplay = '—';
      absentDisplay = '0';
      lateDisplay = '0';
      hasLiveAttendance = false;
    }

    // Contextual subtext for attendance rate (e.g. "10 من 11 طالب")
    let attendanceSubtext = 'لم يُسجل الحضور اليوم بعد';
    if (hasLiveAttendance && effectiveTotalStudents !== null && effectiveTotalStudents > 0) {
      attendanceSubtext = `${(presentCount + lateCount).toLocaleString('ar-EG')} من ${effectiveTotalStudents.toLocaleString('ar-EG')} طالب`;
    } else if (hasLiveAttendance) {
      attendanceSubtext = 'نسبة الحضور التراكمية اليوم';
    }

    // -------------------------------------------------------------
    // 4. Assemble KPIs with Safe Fallbacks (No Fabricated Data)
    // -------------------------------------------------------------
    const kpis: KpiMetric[] = [
      {
        id: 'total_students',
        title: 'إجمالي الطلاب',
        value: effectiveTotalStudents !== null ? effectiveTotalStudents.toLocaleString('ar-EG') : '—',
        subtext: effectiveTotalStudents !== null ? 'طالب مسجل نشط' : 'غير متاح حالياً',
        trend: effectiveTotalStudents !== null ? { direction: 'neutral', value: 'نشط' } : undefined,
        iconName: 'users',
        color: 'var(--primary-600)',
        bgColor: 'var(--primary-50)',
        isAvailable: effectiveTotalStudents !== null,
      },
      {
        id: 'total_teachers',
        title: 'إجمالي المعلمين',
        value: teacherCount !== null ? teacherCount.toLocaleString('ar-EG') : '—',
        subtext: teacherCount !== null ? 'معلم نشط' : 'غير متوفر حالياً',
        trend: teacherCount !== null ? { direction: 'neutral', value: 'نشط' } : undefined,
        iconName: 'teachers',
        color: 'var(--indigo-600)',
        bgColor: 'var(--indigo-50)',
        isAvailable: teacherCount !== null,
      },
      {
        id: 'classes_sections',
        title: 'الفصول والشعب',
        value: classroomCount !== null ? (sectionCount !== null ? `${classroomCount.toLocaleString('ar-EG')} / ${sectionCount.toLocaleString('ar-EG')}` : classroomCount.toLocaleString('ar-EG')) : '—',
        subtext: classroomCount !== null ? (sectionCount !== null ? 'صف / شعبة' : 'صف دراسي') : 'غير متوفر حالياً',
        trend: undefined,
        iconName: 'classes',
        color: 'var(--neutral-700)',
        bgColor: 'var(--neutral-100)',
        isAvailable: classroomCount !== null,
      },
      {
        id: 'attendance_rate',
        title: 'حضور الطلاب اليوم',
        value: attendanceRateDisplay,
        subtext: attendanceSubtext,
        trend: hasLiveAttendance ? { direction: 'up', value: `▲ ${attendanceRateDisplay}` } : undefined,
        iconName: 'attendance',
        color: 'var(--success-600)',
        bgColor: 'var(--success-50)',
        isAvailable: hasLiveAttendance,
      },
      {
        id: 'absent_students',
        title: 'غياب الطلاب',
        value: absentDisplay,
        subtext: hasLiveAttendance ? 'طالب غائب اليوم' : 'لم يُسجل الحضور اليوم بعد',
        trend: hasLiveAttendance && absentCount > 0 ? { direction: 'down', value: 'متابعة' } : undefined,
        iconName: 'absent',
        color: 'var(--danger-600)',
        bgColor: 'var(--danger-50)',
        isAvailable: hasLiveAttendance,
      },
      {
        id: 'late_students',
        title: 'المتأخرون',
        value: lateDisplay,
        subtext: hasLiveAttendance ? 'حالة تأخر مرصودة' : 'لم يُسجل الحضور اليوم بعد',
        trend: hasLiveAttendance && lateCount > 0 ? { direction: 'neutral', value: 'إنذار' } : undefined,
        iconName: 'late',
        color: 'var(--warning-600)',
        bgColor: 'var(--warning-50)',
        isAvailable: hasLiveAttendance,
      },
    ];

    // -------------------------------------------------------------
    // 5. School Day Flow Calculation
    // -------------------------------------------------------------
    const now = new Date();
    const currentHours = now.getHours();
    const currentMinutes = now.getMinutes();
    const timeString = `${String(currentHours).padStart(2, '0')}:${String(currentMinutes).padStart(2, '0')}`;

    const dayStartMinutes = 7 * 60;
    const dayEndMinutes = 13 * 60 + 30;
    const totalDayMinutes = dayEndMinutes - dayStartMinutes;
    const nowTotalMinutes = currentHours * 60 + currentMinutes;
    let progressPercent = 0;
    if (nowTotalMinutes >= dayEndMinutes) {
      progressPercent = 100;
    } else if (nowTotalMinutes > dayStartMinutes) {
      progressPercent = Math.round(((nowTotalMinutes - dayStartMinutes) / totalDayMinutes) * 100);
    }

    const schoolDayFlow: SchoolDayFlow = {
      currentPeriod: progressPercent > 0 && progressPercent < 100 && timetableConfigured ? 4 : 0,
      completedPeriods: progressPercent >= 100 ? timetablePeriodsPerDay : Math.min(timetablePeriodsPerDay, Math.floor((progressPercent / 100) * timetablePeriodsPerDay)),
      totalPeriods: timetableConfigured ? timetablePeriodsPerDay * 6 : 0,
      startTime: '07:00',
      currentTime: timeString,
      endTime: '13:30',
      progressPercent: progressPercent,
      isConfigured: timetableConfigured,
    };

    // -------------------------------------------------------------
    // 6. Attendance Breakdown
    // -------------------------------------------------------------
    const attendanceBreakdown: AttendanceBreakdown = {
      studentAttendanceRate: attendanceRateNumber,
      teacherPresentCount: 0,
      teacherTotalCount: 0,
      presentCount,
      absentCount,
      lateCount,
      excusedCount,
      pendingCount,
    };

    // -------------------------------------------------------------
    // 7. Attention Alerts (Real Operational Triggers Only)
    // -------------------------------------------------------------
    const attentionAlerts: AttentionAlert[] = [];

    if (absentCount > 0) {
      attentionAlerts.push({
        id: 'alert-absent',
        severity: 'danger',
        title: `${absentCount} طالب غائب اليوم يتطلب المتابعة والتأكيد مع أولياء الأمور`,
        actionLabel: 'مراجعة الغياب',
        actionRoute: '/attendance',
      });
    }

    if (lateCount > 0) {
      attentionAlerts.push({
        id: 'alert-late',
        severity: 'warning',
        title: `${lateCount} حالة تأخر مسجلة في الطابور الصباحي اليوم`,
        actionLabel: 'متابعة المتأخرين',
        actionRoute: '/attendance',
      });
    }

    if (pendingCount > 0 && effectiveTotalStudents !== null && effectiveTotalStudents > 0) {
      attentionAlerts.push({
        id: 'alert-pending',
        severity: 'info',
        title: `يوجد ${pendingCount} طالب بانتظار استكمال رصد الحضور للشعب الدراسية`,
        actionLabel: 'استكمال الرصد',
        actionRoute: '/attendance',
      });
    }

    if (awaitingApprovalExamsCount > 0) {
      attentionAlerts.push({
        id: 'alert-exams',
        severity: 'warning',
        title: `${awaitingApprovalExamsCount} كشوف درجات بانتظار الاعتماد الإداري النهائي`,
        actionLabel: 'اعتماد النتائج',
        actionRoute: '/exams',
      });
    }

    if (pendingGradingCount > 0) {
      attentionAlerts.push({
        id: 'alert-homework-grading',
        severity: 'warning',
        title: `${pendingGradingCount} واجبات تنتظر التقييم ورصد الدرجات من الكادر التعليمي`,
        actionLabel: 'مراجعة الواجبات',
        actionRoute: '/homework',
      });
    }

    if (unreadInboxCount > 0) {
      attentionAlerts.push({
        id: 'alert-unread-messages',
        severity: 'info',
        title: `${unreadInboxCount} رسائل أو استفسارات واردة غير مقروءة في صندوق الوارد`,
        actionLabel: 'عرض الرسائل',
        actionRoute: '/messages',
      });
    }

    // -------------------------------------------------------------
    // 8. Domain Operations Summary
    // -------------------------------------------------------------
    const domainSummary: DomainOperationsSummary = {
      homework: {
        activeCount: activeHomeworkCount,
        dueTodayCount: dueTodayHomeworkCount,
        pendingGradingCount: pendingGradingCount,
        averageSubmissionRate: homeworkSubmissionRate,
      },
      exams: {
        upcomingCount: examsCount,
        todayCount: todayExamsCount,
        awaitingApprovalCount: awaitingApprovalExamsCount,
        averagePassRate: examPassRate,
      },
      communications: {
        urgentMessagesCount: unreadInboxCount,
        activeConversationsCount: unreadInboxCount > 0 ? unreadInboxCount : 0,
        activeAnnouncementsCount: unreadNotificationsCount,
        unreadInquiriesCount: 0,
      },
    };

    // -------------------------------------------------------------
    // 9. Activity Feed
    // -------------------------------------------------------------
    const recentActivities: ActivityItem[] = [
      {
        id: 'act-1',
        title: 'تم تسجيل الدخول إلى لوحة الإدارة المدرسية بنجاح',
        timeAgo: 'الآن',
        timestamp: new Date().toISOString(),
        type: 'system',
      },
    ];

    if (hasLiveAttendance) {
      recentActivities.unshift({
        id: 'act-attendance',
        title: `تم تحديث مؤشرات الحضور الصباحي اليوم بنسبة ${attendanceRateDisplay}`,
        timeAgo: 'اليوم',
        timestamp: new Date().toISOString(),
        type: 'attendance',
      });
    }

    // -------------------------------------------------------------
    // 10. Attendance 7-Day Trend
    // -------------------------------------------------------------
    const dayNames = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];
    const dayShorts = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const attendanceTrend: AttendanceTrendPoint[] = [];

    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const dayIndex = d.getDay();
      const isToday = i === 0;
      const dateStr = d.toISOString().split('T')[0];

      attendanceTrend.push({
        day: dayNames[dayIndex],
        dayShort: dayShorts[dayIndex],
        rate: isToday && hasLiveAttendance ? attendanceRateNumber : 0,
        date: dateStr,
      });
    }

    return {
      kpis,
      schoolDayFlow,
      attendanceBreakdown,
      attentionAlerts,
      domainSummary,
      recentActivities,
      attendanceTrend,
      meta: {
        isAggregateEndpointAvailable: false,
      },
    };
  },
};
