import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ExamsPage } from '../pages/ExamsPage';
import { ToastProvider } from '../context/ToastContext';
import * as UseAuthModule from '../context/useAuth';
import { AuthContextType } from '../context/authContextDef';
import { examService } from '../services/examService';
import { Exam, ExamResult } from '../types/exams';

vi.mock('../services/examService', () => ({
  examService: {
    getExams: vi.fn(),
    getExam: vi.fn(),
    getResults: vi.fn(),
    approveResult: vi.fn(),
    rejectResult: vi.fn(),
    reopenResult: vi.fn(),
    publishExam: vi.fn(),
    unpublishExam: vi.fn(),
    getResultLogs: vi.fn(),
  },
}));

const exam: Exam = {
  id: 7,
  school: 10,
  academic_year: 5,
  academic_term: 2,
  teacher_assignment: 11,
  exam_type: 3,
  created_by: 1,
  title: 'DEMO Unpublished Mathematics Result',
  exam_date: '2026-10-15',
  total_marks: '20.00',
  status: 'draft',
  notes: 'اختبار تجريبي',
  classroom_id: 4,
  section_id: 6,
  subject_id: 8,
  created_at: '2026-10-01T08:00:00Z',
};

const submittedResult: ExamResult = {
  id: 91,
  exam: 7,
  exam_title: exam.title,
  student_enrollment: 42,
  student_name: 'DEMO Student A 03',
  student_code: 'DEMO_NOOR-S00003',
  subject_name: 'الرياضيات',
  exam_date: exam.exam_date,
  exam_type_id: 3,
  exam_type_name: 'اختبار قصير',
  exam_type_code: 'QUIZ',
  total_marks: '20.00',
  percentage: 75,
  academic_term_id: 2,
  academic_term_name: 'الفصل الأول',
  score: '15.00',
  status: 'present',
  remarks: '',
  workflow_status: 'submitted',
  approval_reason: null,
  graded_by: 4,
  graded_at: '2026-10-15T10:00:00Z',
  approved_by: null,
  approved_at: null,
  is_published: false,
  published_at: null,
  published_by: null,
  created_at: '2026-10-15T10:00:00Z',
};

const auth = (membershipId = 10, readOnly = false): AuthContextType => ({
  user: { id: 1, username: 'admin', email: '', full_name: 'مدير المدرسة', role: 'school_admin' },
  activeMembership: {
    membership_id: membershipId,
    school: { id: membershipId, name: `مدرسة ${membershipId}` },
    role: 'school_admin',
    academic_year: { id: 5, name: '2026/2027' },
    access_mode: readOnly ? 'read_only' : 'read_write',
    status: readOnly ? 'historical' : 'active',
    is_default: true,
    is_current_school: !readOnly,
    can_write: !readOnly,
    start_date: '2026-09-01', end_date: null, last_used_at: null,
    unread_notifications_count: 0, unread_conversations_count: 0,
  },
  allMemberships: [], isLoading: false, isAuthenticated: true,
  isHistorical: readOnly, isReadOnly: readOnly, isSchoolAdmin: true,
  showContextModal: false, login: vi.fn(), logout: vi.fn(), switchContext: vi.fn(),
  refreshContexts: vi.fn(), setShowContextModal: vi.fn(),
});

const renderPage = () => render(<MemoryRouter><ToastProvider><ExamsPage /></ToastProvider></MemoryRouter>);

describe('W10 Exams and Results page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(auth());
    vi.mocked(examService.getExams).mockResolvedValue({ count: 1, next: null, previous: null, results: [exam] });
    vi.mocked(examService.getResults).mockResolvedValue({ count: 1, next: null, previous: null, results: [submittedResult] });
    vi.mocked(examService.getResultLogs).mockResolvedValue([]);
  });

  it('shows loading then active-context exams and opens the real result roster', async () => {
    let resolve!: (value: { count: number; next: null; previous: null; results: Exam[] }) => void;
    vi.mocked(examService.getExams).mockReturnValue(new Promise((done) => { resolve = done; }));
    renderPage();
    expect(screen.getByText('جاري تحميل الاختبارات...')).toBeInTheDocument();
    resolve({ count: 1, next: null, previous: null, results: [exam] });
    fireEvent.click(await screen.findByText(exam.title));
    expect(await screen.findByText('DEMO Student A 03')).toBeInTheDocument();
    expect(screen.getByText('DEMO_NOOR-S00003')).toBeInTheDocument();
    expect(screen.getByText('15 / 20.00')).toBeInTheDocument();
    expect(screen.getByText('بانتظار الاعتماد')).toBeInTheDocument();
  });

  it('renders empty and error states with retry', async () => {
    vi.mocked(examService.getExams).mockResolvedValueOnce({ count: 0, next: null, previous: null, results: [] });
    const view = renderPage();
    expect(await screen.findByText('لا توجد اختبارات في هذا السياق')).toBeInTheDocument();
    view.unmount();
    vi.clearAllMocks();
    vi.mocked(examService.getExams).mockRejectedValueOnce(new Error('boom'));
    vi.mocked(examService.getExams).mockResolvedValue({ count: 1, next: null, previous: null, results: [exam] });
    renderPage();
    expect(await screen.findByText('تعذر تحميل الاختبارات')).toBeInTheDocument();
    fireEvent.click(screen.getByText('إعادة المحاولة'));
    await waitFor(() => expect(examService.getExams).toHaveBeenCalledTimes(2));
  });

  it('approves a submitted result and updates the row immediately', async () => {
    vi.mocked(examService.approveResult).mockResolvedValue({ ...submittedResult, workflow_status: 'approved' });
    renderPage();
    fireEvent.click(await screen.findByText(exam.title));
    fireEvent.click(await screen.findByRole('button', { name: 'اعتماد' }));
    fireEvent.click(screen.getByRole('button', { name: 'تأكيد الاعتماد' }));
    expect(await screen.findByText('معتمد')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'اعتماد' })).not.toBeInTheDocument();
  });

  it('rejects only with a reason and keeps backend state on failure', async () => {
    vi.mocked(examService.rejectResult).mockRejectedValue(new Error('رفض الخادم'));
    renderPage();
    fireEvent.click(await screen.findByText(exam.title));
    fireEvent.click(await screen.findByRole('button', { name: 'رفض' }));
    expect(screen.getByRole('button', { name: 'تأكيد الرفض' })).toBeDisabled();
    fireEvent.change(screen.getByLabelText('سبب الرفض'), { target: { value: 'مراجعة الدرجة' } });
    fireEvent.click(screen.getByRole('button', { name: 'تأكيد الرفض' }));
    expect(await screen.findByText('بانتظار الاعتماد')).toBeInTheDocument();
  });

  it('hides all mutation controls in historical context', async () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(auth(10, true));
    renderPage();
    fireEvent.click(await screen.findByText(exam.title));
    await screen.findByText('DEMO Student A 03');
    expect(screen.queryByRole('button', { name: 'اعتماد' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'رفض' })).not.toBeInTheDocument();
    expect(screen.getByText('السياق التاريخي للقراءة فقط')).toBeInTheDocument();
  });

  it('clears stale selected records when the active membership changes', async () => {
    const spy = vi.spyOn(UseAuthModule, 'useAuth');
    spy.mockReturnValue(auth(10));
    const view = renderPage();
    fireEvent.click(await screen.findByText(exam.title));
    await screen.findByText('DEMO Student A 03');
    spy.mockReturnValue(auth(20));
    vi.mocked(examService.getExams).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
    view.rerender(<MemoryRouter><ToastProvider><ExamsPage /></ToastProvider></MemoryRouter>);
    expect(await screen.findByText('لا توجد اختبارات في هذا السياق')).toBeInTheDocument();
    expect(screen.queryByText('DEMO Student A 03')).not.toBeInTheDocument();
  });
});
