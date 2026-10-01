import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { AcademicPeriodsPage } from '../pages/AcademicPeriodsPage';
import { ToastProvider } from '../context/ToastContext';
import * as UseAuthModule from '../context/useAuth';
import { academicService } from '../services/academicService';
import { AuthContextType } from '../context/authContextDef';


vi.mock('../services/academicService', () => ({
  academicService: {
    getAcademicYears: vi.fn(),
    createAcademicYear: vi.fn(),
    updateAcademicYear: vi.fn(),
    getAcademicTerms: vi.fn(),
    createAcademicTerm: vi.fn(),
    updateAcademicTerm: vi.fn(),
  },
}));

const authContext: AuthContextType = {
  user: { id: 1, username: 'admin', email: '', full_name: 'Admin', role: 'school_admin' },
  activeMembership: {
    membership_id: 1,
    school: { id: 1, name: 'School A' },
    role: 'school_admin',
    academic_year: { id: 10, name: '2026-2027' },
    access_mode: 'read_write',
    status: 'active',
    is_default: true,
    is_current_school: true,
    can_write: true,
    start_date: '',
    end_date: '',
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

const year = {
  id: 10,
  school: { id: 1, name: 'School A' },
  name: '2026-2027',
  start_date: '2026-09-01',
  end_date: '2027-06-30',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
};

const term = {
  id: 20,
  school: { id: 1, name: 'School A' },
  academic_year: 10,
  academic_year_detail: { id: 10, name: '2026-2027' },
  name: 'الفصل الأول',
  term_type: 'term_1' as const,
  start_date: '2026-09-01',
  end_date: '2026-12-15',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
};

describe('AcademicPeriodsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(authContext);
    vi.mocked(academicService.getAcademicYears).mockResolvedValue({
      count: 1, next: null, previous: null, results: [year],
    });
    vi.mocked(academicService.getAcademicTerms).mockResolvedValue({
      count: 1, next: null, previous: null, results: [term],
    });
  });

  it('lists academic years and terms for the selected year', async () => {
    render(
      <MemoryRouter>
        <ToastProvider><AcademicPeriodsPage /></ToastProvider>
      </MemoryRouter>,
    );

    expect(screen.getByText('السنوات والفصول الدراسية')).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText('2026-2027').length).toBeGreaterThan(0));
    await waitFor(() => expect(screen.getAllByText('الفصل الأول').length).toBeGreaterThan(0));
    expect(academicService.getAcademicTerms).toHaveBeenCalledWith({ academic_year_id: 10 });
    expect(screen.getByText(/لا يعني تعطيل الفصل استبعاده/)).toBeInTheDocument();
  });

  it('offers create and edit actions in a writable context', async () => {
    render(
      <MemoryRouter>
        <ToastProvider><AcademicPeriodsPage /></ToastProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText('إضافة سنة دراسية')).toBeInTheDocument());
    expect(screen.getByText('إضافة فصل دراسي')).toBeInTheDocument();
    expect(screen.getAllByLabelText('تعديل').length).toBeGreaterThan(0);
  });

  it('hides all write actions in a historical context', async () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
      ...authContext,
      isHistorical: true,
      isReadOnly: true,
      activeMembership: {
        ...authContext.activeMembership!,
        status: 'historical',
        access_mode: 'read_only',
        can_write: false,
      },
    });

    render(
      <MemoryRouter>
        <ToastProvider><AcademicPeriodsPage /></ToastProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getAllByText('2026-2027').length).toBeGreaterThan(0));
    expect(screen.queryByText('إضافة سنة دراسية')).not.toBeInTheDocument();
    expect(screen.queryByText('إضافة فصل دراسي')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('تعديل')).not.toBeInTheDocument();
  });
});
