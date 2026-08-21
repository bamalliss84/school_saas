import { UserRole } from './auth';

export type MembershipStatus = 'active' | 'historical' | 'suspended' | 'ended';
export type ContextAccessMode = 'read_write' | 'read_only' | 'unavailable';

export interface SchoolBrief {
  id: number;
  name: string;
}

export interface AcademicYearBrief {
  id: number;
  name: string;
}

export interface SchoolMembership {
  membership_id: number;
  school: SchoolBrief;
  role: UserRole;
  status: MembershipStatus;
  access_mode: ContextAccessMode;
  is_default: boolean;
  is_current_school: boolean;
  academic_year: AcademicYearBrief | null;
  can_write: boolean;
  start_date: string;
  end_date: string | null;
  last_used_at: string | null;
  unread_notifications_count: number;
  unread_conversations_count: number;
}

export interface ContextListResponse {
  current_context: SchoolMembership | null;
  contexts: SchoolMembership[];
}

export interface DefaultContextRequest {
  membership_id: number;
}
