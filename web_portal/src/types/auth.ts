import { SchoolMembership } from './context';

export type UserRole =
  | 'super_admin'
  | 'school_admin'
  | 'teacher'
  | 'parent'
  | 'student';

export interface User {
  id: number;
  username: string;
  full_name: string;
  email: string;
  phone?: string;
  role: UserRole;
  school?: {
    id: number;
    name: string;
  } | null;
  academic_year?: {
    id: number;
    name: string;
  } | null;
  linked_profile?: {
    teacher_id?: number;
    parent_id?: number;
    student_id?: number;
  } | null;
  active_context?: SchoolMembership | null;
  contexts_count?: number;
  has_multiple_contexts?: boolean;
  legacy_role?: string;
  legacy_school?: number;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
  contexts_count: number;
  has_multiple_contexts: boolean;
  default_membership_id: number | null;
}

export interface RefreshResponse {
  access: string;
  refresh?: string;
}
