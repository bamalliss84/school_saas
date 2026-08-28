import { apiClient } from './apiClient';
import { PaginatedResponse } from '../types/api';
import {
  Classroom,
  ClassroomCreateInput,
  ClassroomUpdateInput,
  Section,
  SectionCreateInput,
  SectionUpdateInput,
  Subject,
  SubjectCreateInput,
  SubjectUpdateInput,
  ClassSubject,
  ClassSubjectCreateInput,
  ClassSubjectUpdateInput,
} from '../types/academic';

export const academicService = {
  // Classrooms
  getClassrooms: async (params?: {
    search?: string;
    is_active?: boolean;
    page?: number;
    academic_year_id?: number;
    all_years?: boolean;
  }): Promise<PaginatedResponse<Classroom>> => {
    return apiClient.get<PaginatedResponse<Classroom>>('/classes/', { params });
  },

  getClassroom: async (id: number): Promise<Classroom> => {
    return apiClient.get<Classroom>(`/classes/${id}/`);
  },

  createClassroom: async (data: ClassroomCreateInput): Promise<Classroom> => {
    return apiClient.post<Classroom>('/classes/', data);
  },

  updateClassroom: async (id: number, data: ClassroomUpdateInput): Promise<Classroom> => {
    return apiClient.patch<Classroom>(`/classes/${id}/`, data);
  },

  deleteClassroom: async (id: number): Promise<void> => {
    return apiClient.delete(`/classes/${id}/`);
  },

  // Sections
  getSections: async (params?: {
    classroom_id?: number;
    search?: string;
    is_active?: boolean;
    page?: number;
    academic_year_id?: number;
    all_years?: boolean;
  }): Promise<PaginatedResponse<Section>> => {
    return apiClient.get<PaginatedResponse<Section>>('/sections/', { params });
  },

  getSection: async (id: number): Promise<Section> => {
    return apiClient.get<Section>(`/sections/${id}/`);
  },

  createSection: async (data: SectionCreateInput): Promise<Section> => {
    return apiClient.post<Section>('/sections/', data);
  },

  updateSection: async (id: number, data: SectionUpdateInput): Promise<Section> => {
    return apiClient.patch<Section>(`/sections/${id}/`, data);
  },

  deleteSection: async (id: number): Promise<void> => {
    return apiClient.delete(`/sections/${id}/`);
  },

  // Subjects (School-scoped)
  getSubjects: async (params?: {
    search?: string;
    is_active?: boolean;
    page?: number;
  }): Promise<PaginatedResponse<Subject>> => {
    return apiClient.get<PaginatedResponse<Subject>>('/subjects/', { params });
  },

  getSubject: async (id: number): Promise<Subject> => {
    return apiClient.get<Subject>(`/subjects/${id}/`);
  },

  createSubject: async (data: SubjectCreateInput): Promise<Subject> => {
    return apiClient.post<Subject>('/subjects/', data);
  },

  updateSubject: async (id: number, data: SubjectUpdateInput): Promise<Subject> => {
    return apiClient.patch<Subject>(`/subjects/${id}/`, data);
  },

  deleteSubject: async (id: number): Promise<void> => {
    return apiClient.delete(`/subjects/${id}/`);
  },

  // ClassSubject Curriculum Allocations
  getClassSubjects: async (params?: {
    classroom_id?: number;
    subject_id?: number;
    page?: number;
    academic_year_id?: number;
    all_years?: boolean;
  }): Promise<PaginatedResponse<ClassSubject>> => {
    return apiClient.get<PaginatedResponse<ClassSubject>>('/class-subjects/', { params });
  },

  getClassSubject: async (id: number): Promise<ClassSubject> => {
    return apiClient.get<ClassSubject>(`/class-subjects/${id}/`);
  },

  createClassSubject: async (data: ClassSubjectCreateInput): Promise<ClassSubject> => {
    return apiClient.post<ClassSubject>('/class-subjects/', data);
  },

  updateClassSubject: async (id: number, data: ClassSubjectUpdateInput): Promise<ClassSubject> => {
    return apiClient.patch<ClassSubject>(`/class-subjects/${id}/`, data);
  },

  deleteClassSubject: async (id: number): Promise<void> => {
    return apiClient.delete(`/class-subjects/${id}/`);
  },
};
