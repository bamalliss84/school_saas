import { apiClient } from './apiClient';
import { PaginatedResponse } from '../types/api';
import { Teacher, TeacherAssignment, TeacherAssignmentInput, TeacherInput } from '../types/teachers';

export const teacherService = {
  getTeachers: (params?:{search?:string;is_active?:boolean}) => apiClient.get<PaginatedResponse<Teacher>>('/teachers/', {params}),
  getTeacher: (id:number) => apiClient.get<Teacher>(`/teachers/${id}/`),
  createTeacher: (data:TeacherInput) => apiClient.post<Teacher>('/teachers/', data),
  updateTeacher: (id:number,data:Partial<TeacherInput>) => apiClient.patch<Teacher>(`/teachers/${id}/`, data),
  getAssignments: (params:{teacher_id:number;all_years?:boolean}) => apiClient.get<PaginatedResponse<TeacherAssignment>>('/teacher-assignments/', {params}),
  createAssignment: (data:TeacherAssignmentInput) => apiClient.post<TeacherAssignment>('/teacher-assignments/', data),
  updateAssignment: (id:number,data:Partial<TeacherAssignmentInput>) => apiClient.patch<TeacherAssignment>(`/teacher-assignments/${id}/`, data),
  deleteAssignment: (id:number) => apiClient.delete<void>(`/teacher-assignments/${id}/`),
};
