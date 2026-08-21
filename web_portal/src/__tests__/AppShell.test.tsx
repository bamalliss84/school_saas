import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import * as UseAuthModule from '../context/useAuth';

const mockLogout = vi.fn();
const mockSetShowContextModal = vi.fn();

describe('W1-D2 Main Application Shell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
      user: {
        id: 1,
        username: 'admin',
        email: 'admin@school.com',
        full_name: 'أحمد محمد',
        role: 'school_admin',
      },
      isAuthenticated: true,
      isLoading: false,
      activeMembership: {
        membership_id: 1,
        school: { id: 1, name: 'مدرسة النور الأهلية' },
        role: 'school_admin',
        status: 'active',
        access_mode: 'read_write',
        is_default: true,
        is_current_school: true,
        academic_year: { id: 1, name: '2026/2027' },
        can_write: true,
        start_date: '2026-09-01',
        end_date: null,
        last_used_at: null,
        unread_notifications_count: 3,
        unread_conversations_count: 2,
      },
      allMemberships: [],
      isHistorical: false,
      isReadOnly: false,
      isSchoolAdmin: true,
      showContextModal: false,
      login: vi.fn(),
      logout: mockLogout,
      switchContext: vi.fn(),
      refreshContexts: vi.fn(),
      setShowContextModal: mockSetShowContextModal,
    });
  });

  it('renders Sidebar with brand, school info, and navigation items', () => {
    render(
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>
    );

    // Brand and School Context in Sidebar
    expect(screen.getByText('منصة المدرسة')).toBeInTheDocument();
    expect(screen.getAllByText('مدرسة النور الأهلية').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/2026\/2027/).length).toBeGreaterThan(0);

    // Navigation links
    expect(screen.getByText('الرئيسية')).toBeInTheDocument();
    expect(screen.getByText('الطلاب')).toBeInTheDocument();
    expect(screen.getByText('المعلمون')).toBeInTheDocument();
    expect(screen.getByText('الفصول والشعب')).toBeInTheDocument();
    expect(screen.getByText('المواد الدراسية')).toBeInTheDocument();
    expect(screen.getByText('الجداول')).toBeInTheDocument();
    expect(screen.getByText('الحضور والانصراف')).toBeInTheDocument();
    expect(screen.getByText('الواجبات')).toBeInTheDocument();
    expect(screen.getByText('الاختبارات والنتائج')).toBeInTheDocument();
    expect(screen.getByText('الرسائل')).toBeInTheDocument();
    expect(screen.getByText('الإعلانات والإشعارات')).toBeInTheDocument();
    expect(screen.getByText('التقارير')).toBeInTheDocument();
    expect(screen.getByText('الاستيراد والتصدير')).toBeInTheDocument();
    expect(screen.getByText('الإعدادات')).toBeInTheDocument();
  });

  it('toggles Sidebar collapse when collapse button is clicked', () => {
    render(
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>
    );

    const collapseBtn = screen.getByRole('button', { name: /طي القائمة/i });
    expect(collapseBtn).toBeInTheDocument();

    // Click collapse
    fireEvent.click(collapseBtn);
    expect(screen.getByRole('button', { name: /توسيع القائمة/i })).toBeInTheDocument();

    // Click expand
    fireEvent.click(screen.getByRole('button', { name: /توسيع القائمة/i }));
    expect(screen.getByRole('button', { name: /طي القائمة/i })).toBeInTheDocument();
  });

  it('renders Topbar with context switch trigger, search input, badges, and user profile', () => {
    render(
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>
    );

    // Context switch button
    const contextBtn = screen.getByRole('button', { name: /تغيير سياق المدرسة/i });
    expect(contextBtn).toBeInTheDocument();
    fireEvent.click(contextBtn);
    expect(mockSetShowContextModal).toHaveBeenCalledWith(true);

    // Search bar
    expect(screen.getByRole('search')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('ابحث...')).toBeInTheDocument();

    // Notification / Message badges
    expect(screen.getByRole('button', { name: /المحادثات والرسائل/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /الإشعارات/i })).toBeInTheDocument();

    // User name and role in Topbar
    expect(screen.getByText('أحمد محمد')).toBeInTheDocument();
    expect(screen.getByText('مدير المدرسة')).toBeInTheDocument();
  });

  it('opens user menu and triggers logout when clicked', () => {
    render(
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>
    );

    const userMenuBtn = screen.getByRole('button', { name: /قائمة المستخدم/i });
    fireEvent.click(userMenuBtn);

    expect(screen.getByRole('menuitem', { name: /الملف الشخصي/i })).toBeInTheDocument();
    const logoutItem = screen.getByRole('menuitem', { name: /تسجيل الخروج/i });
    expect(logoutItem).toBeInTheDocument();

    fireEvent.click(logoutItem);
    expect(mockLogout).toHaveBeenCalled();
  });

  describe('Exclusive Active Navigation State Verification', () => {
    it('activates ONLY Students when on /students, and Teachers is NOT active', () => {
      render(
        <MemoryRouter initialEntries={['/students']}>
          <AppShell />
        </MemoryRouter>
      );

      const studentsLink = screen.getByRole('link', { name: /الطلاب/i });
      const teachersLink = screen.getByRole('link', { name: /المعلمون/i });
      const dashboardLink = screen.getByRole('link', { name: /الرئيسية/i });

      expect(studentsLink).toHaveClass('active');
      expect(teachersLink).not.toHaveClass('active');
      expect(dashboardLink).not.toHaveClass('active');
    });

    it('activates ONLY Students when on nested subroute /students/123/profile', () => {
      render(
        <MemoryRouter initialEntries={['/students/123/profile']}>
          <AppShell />
        </MemoryRouter>
      );

      const studentsLink = screen.getByRole('link', { name: /الطلاب/i });
      const teachersLink = screen.getByRole('link', { name: /المعلمون/i });

      expect(studentsLink).toHaveClass('active');
      expect(teachersLink).not.toHaveClass('active');
    });

    it('activates ONLY Teachers when on /teachers, and Students is NOT active', () => {
      render(
        <MemoryRouter initialEntries={['/teachers']}>
          <AppShell />
        </MemoryRouter>
      );

      const studentsLink = screen.getByRole('link', { name: /الطلاب/i });
      const teachersLink = screen.getByRole('link', { name: /المعلمون/i });

      expect(teachersLink).toHaveClass('active');
      expect(studentsLink).not.toHaveClass('active');
    });

    it('activates ONLY Timetable when on /timetable', () => {
      render(
        <MemoryRouter initialEntries={['/timetable']}>
          <AppShell />
        </MemoryRouter>
      );

      const timetableLink = screen.getByRole('link', { name: /الجداول/i });
      const attendanceLink = screen.getByRole('link', { name: /الحضور والانصراف/i });

      expect(timetableLink).toHaveClass('active');
      expect(attendanceLink).not.toHaveClass('active');
    });

    it('activates ONLY Classes when on /classes, and Subjects is NOT active', () => {
      render(
        <MemoryRouter initialEntries={['/classes']}>
          <AppShell />
        </MemoryRouter>
      );

      const classesLink = screen.getByRole('link', { name: /الفصول والشعب/i });
      const subjectsLink = screen.getByRole('link', { name: /المواد الدراسية/i });

      expect(classesLink).toHaveClass('active');
      expect(subjectsLink).not.toHaveClass('active');
    });

    it('activates ONLY Dashboard when on /dashboard', () => {
      render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <AppShell />
        </MemoryRouter>
      );

      const dashboardLink = screen.getByRole('link', { name: /الرئيسية/i });
      const studentsLink = screen.getByRole('link', { name: /الطلاب/i });

      expect(dashboardLink).toHaveClass('active');
      expect(studentsLink).not.toHaveClass('active');
    });
  });
});
