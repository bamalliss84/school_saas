import { SchoolBrief, AcademicYearBrief } from './context';

export interface AcademicYear {
  id: number;
  school: SchoolBrief;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  created_at: string;
}

export interface AcademicYearInput {
  name: string;
  start_date: string;
  end_date: string;
  is_active?: boolean;
}

export type AcademicTermType = 'term_1' | 'term_2' | 'term_3' | 'summer';

export interface AcademicTerm {
  id: number;
  school: SchoolBrief;
  academic_year: number;
  academic_year_detail: AcademicYearBrief;
  name: string;
  term_type: AcademicTermType;
  start_date: string;
  end_date: string;
  is_active: boolean;
  created_at: string;
}

export interface AcademicTermInput {
  academic_year: number;
  name: string;
  term_type: AcademicTermType;
  start_date: string;
  end_date: string;
  is_active?: boolean;
}

export interface Classroom {
  id: number;
  school: SchoolBrief;
  academic_year: number;
  academic_year_detail: AcademicYearBrief;
  name: string;
  code: string;
  is_active: boolean;
  sections_count: number;
  students_count: number;
  created_at: string;
}

export interface ClassroomCreateInput {
  name: string;
  code: string;
  is_active?: boolean;
  academic_year?: number;
}

export interface ClassroomUpdateInput {
  name?: string;
  code?: string;
  is_active?: boolean;
}

export interface Section {
  id: number;
  school: SchoolBrief;
  academic_year: number;
  academic_year_detail: AcademicYearBrief;
  classroom: number;
  classroom_detail: { id: number; name: string; code: string };
  name: string;
  code: string;
  is_active: boolean;
  students_count: number;
  created_at: string;
}

export interface SectionCreateInput {
  classroom: number;
  name: string;
  code: string;
  is_active?: boolean;
}

export interface SectionUpdateInput {
  classroom?: number;
  name?: string;
  code?: string;
  is_active?: boolean;
}

export interface Subject {
  id: number;
  school: SchoolBrief;
  name: string;
  code: string;
  is_active: boolean;
}

export interface SubjectCreateInput {
  name: string;
  code: string;
  is_active?: boolean;
}

export interface SubjectUpdateInput {
  name?: string;
  code?: string;
  is_active?: boolean;
}

export interface ClassSubject {
  id: number;
  school: SchoolBrief;
  academic_year: number;
  classroom: number;
  classroom_detail: { id: number; name: string; code: string };
  subject: number;
  subject_detail: { id: number; name: string; code: string };
  weekly_periods: number;
}

export interface ClassSubjectCreateInput {
  classroom: number;
  subject: number;
  weekly_periods: number;
}

export interface ClassSubjectUpdateInput {
  weekly_periods: number;
}
