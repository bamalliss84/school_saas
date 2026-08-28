import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ClassesPage } from '../pages/ClassesPage';
import { SubjectsPage } from '../pages/SubjectsPage';
import { ToastProvider } from '../context/ToastContext';
import * as UseAuthModule from '../context/useAuth';
import { AuthContextType } from '../context/authContextDef';
import { academicService } from '../services/academicService';
import { Classroom, Section, Subject, ClassSubject } from '../types/academic';

// Mock academicService
vi.mock('../services/academicService', () => ({
  academicService: {
    getClassrooms: vi.fn(),
    getClassroom: vi.fn(),
    createClassroom: vi.fn(),
    updateClassroom: vi.fn(),
    deleteClassroom: vi.fn(),
    getSections: vi.fn(),
    getSection: vi.fn(),
    createSection: vi.fn(),
    updateSection: vi.fn(),
    deleteSection: vi.fn(),
    getSubjects: vi.fn(),
    getSubject: vi.fn(),
    createSubject: vi.fn(),
    updateSubject: vi.fn(),
    deleteSubject: vi.fn(),
    getClassSubjects: vi.fn(),
    createClassSubject: vi.fn(),
    updateClassSubject: vi.fn(),
    deleteClassSubject: vi.fn(),
  },
}));

const mockClassrooms: Classroom[] = [
  {
    id: 1,
    school: { id: 10, name: 'مدرسة التفوق' },
    academic_year: 5,
    academic_year_detail: { id: 5, name: '2026-2027' },
    name: 'الصف العاشر',
    code: 'G10',
    is_active: true,
    sections_count: 2,
    students_count: 50,
    created_at: '2026-09-01T08:00:00Z',
  },
  {
    id: 2,
    school: { id: 10, name: 'مدرسة التفوق' },
    academic_year: 5,
    academic_year_detail: { id: 5, name: '2026-2027' },
    name: 'الصف الحادي عشر',
    code: 'G11',
    is_active: true,
    sections_count: 1,
    students_count: 28,
    created_at: '2026-09-01T08:00:00Z',
  },
];

const mockSections: Section[] = [
  {
    id: 101,
    school: { id: 10, name: 'مدرسة التفوق' },
    academic_year: 5,
    academic_year_detail: { id: 5, name: '2026-2027' },
    classroom: 1,
    classroom_detail: { id: 1, name: 'الصف العاشر', code: 'G10' },
    name: 'أ',
    code: '10-A',
    is_active: true,
    students_count: 25,
    created_at: '2026-09-01T08:00:00Z',
  },
  {
    id: 102,
    school: { id: 10, name: 'مدرسة التفوق' },
    academic_year: 5,
    academic_year_detail: { id: 5, name: '2026-2027' },
    classroom: 1,
    classroom_detail: { id: 1, name: 'الصف العاشر', code: 'G10' },
    name: 'ب',
    code: '10-B',
    is_active: true,
    students_count: 25,
    created_at: '2026-09-01T08:00:00Z',
  },
];

const mockSubjects: Subject[] = [
  {
    id: 201,
    school: { id: 10, name: 'مدرسة التفوق' },
    name: 'الرياضيات',
    code: 'MATH',
    is_active: true,
  },
  {
    id: 202,
    school: { id: 10, name: 'مدرسة التفوق' },
    name: 'الفيزياء',
    code: 'PHYS',
    is_active: true,
  },
];

const mockClassSubjects: ClassSubject[] = [
  {
    id: 301,
    school: { id: 10, name: 'مدرسة التفوق' },
    academic_year: 5,
    classroom: 1,
    classroom_detail: { id: 1, name: 'الصف العاشر', code: 'G10' },
    subject: 201,
    subject_detail: { id: 201, name: 'الرياضيات', code: 'MATH' },
    weekly_periods: 5,
  },
];

const activeAuthContext: AuthContextType = {
  user: { id: 1, username: 'admin', email: 'admin@school.com', full_name: 'مدير المدرسة', role: 'school_admin' },
  activeMembership: {
    membership_id: 10,
    school: { id: 10, name: 'مدرسة التفوق' },
    role: 'school_admin',
    academic_year: { id: 5, name: '2026-2027' },
    access_mode: 'read_write',
    status: 'active',
    is_default: true,
    is_current_school: true,
    can_write: true,
    start_date: '2026-09-01',
    end_date: null,
    last_used_at: null,
    unread_notifications_count: 0,
    unread_conversations_count: 0,
  },
  allMemberships: [],
  isLoading: false,
  isAuthenticated: true,
  isHistorical: false,
  isReadOnly: false,
  isSchoolAdmin: true,
  showContextModal: false,
  login: vi.fn(),
  logout: vi.fn(),
  switchContext: vi.fn(),
  refreshContexts: vi.fn(),
  setShowContextModal: vi.fn(),
};

const historicalAuthContext: AuthContextType = {
  ...activeAuthContext,
  isHistorical: true,
  isReadOnly: true,
  activeMembership: {
    ...activeAuthContext.activeMembership!,
    status: 'historical',
    can_write: false,
    access_mode: 'read_only',
  },
};

describe('BE-1 Academic Structure Web UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(activeAuthContext);

    vi.mocked(academicService.getClassrooms).mockResolvedValue({
      count: mockClassrooms.length,
      next: null,
      previous: null,
      results: mockClassrooms,
    });
    vi.mocked(academicService.getSections).mockResolvedValue({
      count: mockSections.length,
      next: null,
      previous: null,
      results: mockSections,
    });
    vi.mocked(academicService.getSubjects).mockResolvedValue({
      count: mockSubjects.length,
      next: null,
      previous: null,
      results: mockSubjects,
    });
    vi.mocked(academicService.getClassSubjects).mockResolvedValue({
      count: mockClassSubjects.length,
      next: null,
      previous: null,
      results: mockClassSubjects,
    });
  });

  describe('ClassesPage', () => {
    it('renders classrooms list and automatically selects the first classroom', async () => {
      render(
        <MemoryRouter>
          <ToastProvider>
            <ClassesPage />
          </ToastProvider>
        </MemoryRouter>
      );

      expect(screen.getByText('الصفوف والشعب')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getAllByText('الصف العاشر').length).toBeGreaterThan(0);
        expect(screen.getByText('الصف الحادي عشر')).toBeInTheDocument();
      });

      // Selected classroom header details
      expect(screen.getByText('شعب الصف الدراسي')).toBeInTheDocument();
      await waitFor(() => {
        expect(screen.getByText('شعبة أ')).toBeInTheDocument();
        expect(screen.getByText('شعبة ب')).toBeInTheDocument();
      });
    });

    it('switches to curriculum tab and displays assigned subjects', async () => {
      render(
        <MemoryRouter>
          <ToastProvider>
            <ClassesPage />
          </ToastProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/المنهج والمواد/)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/المنهج والمواد/));

      await waitFor(() => {
        expect(screen.getByText('المناهج والمواد المخصصة لهذا الصف')).toBeInTheDocument();
        expect(screen.getByText('5 حصص / أسبوع')).toBeInTheDocument();
      });
    });

    it('hides write actions in historical read-only mode', async () => {
      vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(historicalAuthContext);

      render(
        <MemoryRouter>
          <ToastProvider>
            <ClassesPage />
          </ToastProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText('الصف العاشر').length).toBeGreaterThan(0);
      });

      expect(screen.queryByText('إضافة صف دراسي')).not.toBeInTheDocument();
      expect(screen.queryByText('إضافة شعبة')).not.toBeInTheDocument();
    });
  });

  describe('SubjectsPage', () => {
    it('renders school-wide subjects catalog with badges and codes', async () => {
      render(
        <MemoryRouter>
          <ToastProvider>
            <SubjectsPage />
          </ToastProvider>
        </MemoryRouter>
      );

      expect(screen.getByText('المواد الدراسية')).toBeInTheDocument();
      expect(screen.getByText('دليل المدرسة العام')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('الرياضيات')).toBeInTheDocument();
        expect(screen.getByText('الفيزياء')).toBeInTheDocument();
      });
    });

    it('filters subjects by active status', async () => {
      render(
        <MemoryRouter>
          <ToastProvider>
            <SubjectsPage />
          </ToastProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('النشطة فقط')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('النشطة فقط'));

      await waitFor(() => {
        expect(academicService.getSubjects).toHaveBeenCalledWith(
          expect.objectContaining({ is_active: true })
        );
      });
    });

    it('hides create/edit/delete buttons in historical read-only mode', async () => {
      vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(historicalAuthContext);

      render(
        <MemoryRouter>
          <ToastProvider>
            <SubjectsPage />
          </ToastProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('الرياضيات')).toBeInTheDocument();
      });

      expect(screen.queryByText('إضافة مادة دراسية')).not.toBeInTheDocument();
    });
  });
});
