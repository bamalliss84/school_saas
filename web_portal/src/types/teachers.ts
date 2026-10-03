import { AcademicYearBrief, SchoolBrief } from './context';

export interface Teacher {
  id: number;
  school: SchoolBrief;
  academic_year: number;
  academic_year_detail: AcademicYearBrief;
  user_id: number | null;
  username: string;
  employee_code: string;
  full_name: string;
  phone: string | null;
  email: string | null;
  specialization: string | null;
  qualification: string | null;
  hire_date: string | null;
  address: string | null;
  photo: string | null;
  is_active: boolean;
  assignments_count: number;
  created_at: string;
}

export interface TeacherInput {
  academic_year?: number;
  full_name: string;
  phone?: string;
  email?: string;
  specialization?: string;
  qualification?: string;
  hire_date?: string | null;
  address?: string;
  is_active?: boolean;
  account_username?: string;
  account_password?: string;
}

export interface TeacherAssignment {
  id: number;
  school: SchoolBrief;
  academic_year: number;
  academic_year_detail: AcademicYearBrief;
  teacher: number;
  teacher_detail: {id:number;full_name:string;employee_code:string;specialization:string|null};
  classroom: number;
  classroom_detail: {id:number;name:string;code:string};
  section: number;
  section_detail: {id:number;name:string;code:string};
  subject: number;
  subject_detail: {id:number;name:string;code:string};
  is_current: boolean;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
}

export interface TeacherAssignmentInput {
  teacher: number;
  classroom: number;
  section: number;
  subject: number;
  is_current: boolean;
  start_date?: string | null;
  end_date?: string | null;
}
