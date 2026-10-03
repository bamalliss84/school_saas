import { PaginatedResponse } from './api';
import { SchoolBrief, AcademicYearBrief } from './context';

export type EnrollmentStatus = 'active'|'transferred'|'graduated'|'withdrawn'|'suspended';
export interface Enrollment { id:number; school:SchoolBrief; academic_year:AcademicYearBrief; classroom:{id:number;name:string;code:string}; section:{id:number;name:string;code:string}; status:EnrollmentStatus; is_current:boolean; start_date:string|null; end_date:string|null; created_at:string; }
export interface ManagedEnrollment { id:number; academic_year:number; academic_year_detail:AcademicYearBrief; classroom:number; classroom_detail:{id:number;name:string;code:string}; section:number; section_detail:{id:number;name:string;code:string}; status:EnrollmentStatus; is_current:boolean; start_date:string|null; end_date:string|null; created_at:string; }
export interface Student { id:number; student_code:string; full_name:string; gender:'male'|'female'; birth_date:string|null; is_active:boolean; created_at:string; school:SchoolBrief; current_enrollment:Enrollment|null; guardians?:Array<{parent_id:number;full_name:string;relationship:string;is_primary:boolean}>; }
export interface StudentInput { full_name:string; gender:'male'|'female'; birth_date?:string|null; is_active?:boolean; }
export interface EnrollmentInput { academic_year:number; classroom:number; section:number; status:EnrollmentStatus; is_current:boolean; start_date?:string|null; end_date?:string|null; }
export type StudentPage = PaginatedResponse<Student>;
