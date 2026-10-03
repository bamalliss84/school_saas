import { apiClient } from './apiClient';
import { PaginatedResponse } from '../types/api';
import { Enrollment, EnrollmentInput, ManagedEnrollment, Student, StudentInput } from '../types/students';

export const studentService = {
  getStudents: (params?:{search?:string;is_active?:boolean;is_current?:boolean;academic_year_id?:number;classroom_id?:number;section_id?:number}) => apiClient.get<PaginatedResponse<Student>>('/students/', {params}),
  getStudent: (id:number) => apiClient.get<Student>(`/students/${id}/`),
  createStudent: (data:StudentInput) => apiClient.post<Student>('/students/', data),
  updateStudent: (id:number,data:Partial<StudentInput>) => apiClient.patch<Student>(`/students/${id}/`, data),
  getHistory: (id:number) => apiClient.get<PaginatedResponse<Enrollment>>(`/students/${id}/academic-history/`),
  createEnrollment: (studentId:number,data:EnrollmentInput) => apiClient.post<ManagedEnrollment>(`/students/${studentId}/enrollments/`, data),
  updateEnrollment: (studentId:number,id:number,data:Partial<EnrollmentInput>) => apiClient.patch<ManagedEnrollment>(`/students/${studentId}/enrollments/${id}/`, data),
};
