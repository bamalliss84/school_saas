export type MetricIconType =
  | 'users'
  | 'teachers'
  | 'classes'
  | 'attendance'
  | 'absent'
  | 'late'
  | 'calendar'
  | 'file-text'
  | 'message-square'
  | 'bell'
  | 'upload'
  | 'download';

export interface KpiMetric {
  id: string;
  title: string;
  value: string | number;
  subtext?: string;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    value: string;
    label?: string;
  };
  iconName: MetricIconType;
  color: string;
  bgColor: string;
  isAvailable: boolean;
}

export interface SchoolDayFlow {
  currentPeriod: number;
  completedPeriods: number;
  totalPeriods: number;
  startTime: string;
  currentTime: string;
  endTime: string;
  progressPercent: number;
  isConfigured: boolean;
}

export interface AttendanceBreakdown {
  studentAttendanceRate: number;
  teacherPresentCount: number;
  teacherTotalCount: number;
  presentCount: number;
  absentCount: number;
  lateCount: number;
  excusedCount: number;
  pendingCount: number;
}

export interface AttentionAlert {
  id: string;
  severity: 'danger' | 'warning' | 'info';
  title: string;
  actionLabel: string;
  actionRoute: string;
}

export interface DomainOperationsSummary {
  homework: {
    activeCount: number;
    dueTodayCount: number;
    pendingGradingCount: number;
    averageSubmissionRate: number;
  };
  exams: {
    upcomingCount: number;
    todayCount: number;
    awaitingApprovalCount: number;
    averagePassRate: number;
  };
  communications: {
    urgentMessagesCount: number;
    activeConversationsCount: number;
    activeAnnouncementsCount: number;
    unreadInquiriesCount: number;
  };
}

export interface ActivityItem {
  id: string;
  title: string;
  timeAgo: string;
  timestamp: string;
  type: 'exam' | 'student' | 'announcement' | 'attendance' | 'system';
}

export interface AttendanceTrendPoint {
  day: string;
  dayShort: string;
  rate: number;
  date: string;
}

export interface QuickActionItem {
  id: string;
  label: string;
  sublabel?: string;
  iconName: string;
  route: string;
  variant: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'excel';
  requiresWritable: boolean;
}
