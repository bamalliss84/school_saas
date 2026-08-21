import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthGuard } from '../routes/AuthGuard';
import { SchoolAdminGuard } from '../routes/SchoolAdminGuard';
import * as UseAuthModule from '../context/useAuth';

describe('Route Guards', () => {
  it('AuthGuard redirects unauthenticated users to /login', () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      activeMembership: null,
      allMemberships: [],
      isHistorical: false,
      isReadOnly: false,
      isSchoolAdmin: false,
      showContextModal: false,
      login: vi.fn(),
      logout: vi.fn(),
      switchContext: vi.fn(),
      refreshContexts: vi.fn(),
      setShowContextModal: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/login" element={<div>صفحة تسجيل الدخول</div>} />
          <Route
            path="/dashboard"
            element={
              <AuthGuard>
                <div>لوحة التحكم الخاصة</div>
              </AuthGuard>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('صفحة تسجيل الدخول')).toBeInTheDocument();
    expect(screen.queryByText('لوحة التحكم الخاصة')).toBeNull();
  });

  it('SchoolAdminGuard redirects non-admin users to /unauthorized', () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
      user: {
        id: 5,
        username: 'teacher_user',
        full_name: 'معلم تجريبي',
        email: 't@school.com',
        role: 'teacher',
      },
      isAuthenticated: true,
      isLoading: false,
      activeMembership: null,
      allMemberships: [],
      isHistorical: false,
      isReadOnly: false,
      isSchoolAdmin: false,
      showContextModal: false,
      login: vi.fn(),
      logout: vi.fn(),
      switchContext: vi.fn(),
      refreshContexts: vi.fn(),
      setShowContextModal: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/unauthorized" element={<div>غير مصرح لك بالوصول</div>} />
          <Route
            path="/dashboard"
            element={
              <SchoolAdminGuard>
                <div>لوحة تحكم المدير</div>
              </SchoolAdminGuard>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('غير مصرح لك بالوصول')).toBeInTheDocument();
    expect(screen.queryByText('لوحة تحكم المدير')).toBeNull();
  });

  it('SchoolAdminGuard renders protected content for school_admin', () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
      user: {
        id: 1,
        username: 'admin_user',
        full_name: 'مدير المدرسة',
        email: 'a@school.com',
        role: 'school_admin',
      },
      isAuthenticated: true,
      isLoading: false,
      activeMembership: null,
      allMemberships: [],
      isHistorical: false,
      isReadOnly: false,
      isSchoolAdmin: true,
      showContextModal: false,
      login: vi.fn(),
      logout: vi.fn(),
      switchContext: vi.fn(),
      refreshContexts: vi.fn(),
      setShowContextModal: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/unauthorized" element={<div>غير مصرح لك بالوصول</div>} />
          <Route
            path="/dashboard"
            element={
              <SchoolAdminGuard>
                <div>لوحة تحكم المدير</div>
              </SchoolAdminGuard>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('لوحة تحكم المدير')).toBeInTheDocument();
    expect(screen.queryByText('غير مصرح لك بالوصول')).toBeNull();
  });
});
