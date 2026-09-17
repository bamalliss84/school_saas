import { apiClient } from './apiClient';
import { PaginatedResponse } from '../types/api';
import { Exam, ExamResult, ExamResultLog, PublicationSummary } from '../types/exams';

export const examService = {
  getExams: (params?: { academic_year_id?: number; status?: string; page?: number }) =>
    apiClient.get<PaginatedResponse<Exam>>('/exams/', { params }),
  getExam: (id: number) => apiClient.get<Exam>(`/exams/${id}/`),
  getResults: (params?: { exam_id?: number; workflow_status?: string; page?: number }) =>
    apiClient.get<PaginatedResponse<ExamResult>>('/exam-results/', { params }),
  approveResult: (id: number, reason?: string) =>
    apiClient.post<ExamResult>(`/exam-results/${id}/approve/`, { reason }),
  rejectResult: (id: number, reason: string) =>
    apiClient.post<ExamResult>(`/exam-results/${id}/reject/`, { reason }),
  reopenResult: (id: number, reason?: string) =>
    apiClient.post<ExamResult>(`/exam-results/${id}/reopen/`, { reason }),
  publishExam: (id: number, reason?: string) =>
    apiClient.post<PublicationSummary>(`/exams/${id}/publish/`, { reason }),
  unpublishExam: (id: number, reason?: string) =>
    apiClient.post<PublicationSummary>(`/exams/${id}/unpublish/`, { reason }),
  getResultLogs: (id: number) => apiClient.get<ExamResultLog[]>(`/exam-results/${id}/logs/`),
};
