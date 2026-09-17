export type ExamStatus = 'draft' | 'published' | 'closed' | 'cancelled';
export type ResultStatus = 'not_graded' | 'present' | 'absent' | 'excused' | 'exempted';
export type ResultWorkflowStatus = 'draft' | 'submitted' | 'approved' | 'rejected';

export interface Exam {
  id: number; school: number; academic_year: number; academic_term: number;
  teacher_assignment: number; exam_type: number; created_by: number | null;
  title: string; exam_date: string; total_marks: string; status: ExamStatus;
  notes: string | null; classroom_id: number; section_id: number; subject_id: number;
  created_at: string;
}

export interface ExamResult {
  id: number; exam: number; exam_title: string; student_enrollment: number;
  student_name: string; student_code: string; subject_name: string; exam_date: string;
  exam_type_id: number; exam_type_name: string; exam_type_code: string;
  total_marks: string; percentage: number | null; academic_term_id: number;
  academic_term_name: string; score: string | null; status: ResultStatus;
  remarks: string | null; workflow_status: ResultWorkflowStatus;
  approval_reason: string | null; graded_by: number | null; graded_at: string | null;
  approved_by: number | null; approved_at: string | null; is_published: boolean;
  published_at: string | null; published_by: number | null; created_at: string;
}

export interface ExamResultLog {
  id: number; exam_result: number; old_score: string | null; new_score: string | null;
  old_status: ResultStatus | null; new_status: ResultStatus | null;
  old_workflow_status: ResultWorkflowStatus | null;
  new_workflow_status: ResultWorkflowStatus | null;
  old_is_published: boolean | null; new_is_published: boolean | null;
  action: 'create' | 'update' | 'submit' | 'approve' | 'reject' | 'reopen' | 'publish' | 'unpublish';
  changed_by: number | null; reason: string | null; changed_at: string;
}

export interface PublicationSummary {
  exam: number; published_count: number; skipped_count: number;
  already_published_count: number; unpublished_count?: number; total_count: number;
  results: ExamResult[];
}
