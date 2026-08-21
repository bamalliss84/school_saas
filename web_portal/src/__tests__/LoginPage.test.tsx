import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import * as useAuthModule from '../context/useAuth';

// Mock useAuth
const mockLogin = vi.fn();
const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('LoginPage (W1-D1 Visual Closure & Functionality)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(useAuthModule, 'useAuth').mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      activeMembership: null,
      allMemberships: [],
      isHistorical: false,
      isReadOnly: false,
      isSchoolAdmin: false,
      showContextModal: false,
      login: mockLogin,
      logout: vi.fn(),
      switchContext: vi.fn(),
      refreshContexts: vi.fn(),
      setShowContextModal: vi.fn(),
    });
  });

  it('renders all approved design elements correctly', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // Brand and Headings
    expect(screen.getByText('منصة المدرسة')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'تسجيل الدخول' })).toBeInTheDocument();
    expect(
      screen.getByText('مرحباً بعودتك، أدخل بياناتك للوصول إلى لوحة إدارة المدرسة')
    ).toBeInTheDocument();

    // Inputs & Placeholders
    expect(screen.getByLabelText('اسم المستخدم أو البريد الإلكتروني')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('اسم المستخدم أو البريد')).toBeInTheDocument();
    expect(screen.getByLabelText('كلمة المرور')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('كلمة المرور')).toBeInTheDocument();

    // Submit Button
    expect(screen.getByRole('button', { name: 'تسجيل الدخول' })).toBeInTheDocument();

    // Feature Panel & Diagram
    expect(screen.getByText('إدارة مدرستك من مكان واحد')).toBeInTheDocument();
    expect(
      screen.getByText('الطلاب، المعلمون، الحضور، الجداول، الواجبات والنتائج في نظام موحد.')
    ).toBeInTheDocument();

    // Footer Caption
    expect(screen.getByText('دخول آمن إلى نظام إدارة المدرسة')).toBeInTheDocument();
  });

  it('validates empty inputs and prevents submission', async () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('اسم المستخدم مطلوب')).toBeInTheDocument();
      expect(screen.getByText('كلمة المرور مطلوبة')).toBeInTheDocument();
    });

    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('toggles password visibility when eye icon button is clicked', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const passwordInput = screen.getByPlaceholderText('كلمة المرور') as HTMLInputElement;
    const toggleBtn = screen.getByLabelText('إظهار كلمة المرور');

    expect(passwordInput.type).toBe('password');

    // Click to show password
    fireEvent.click(toggleBtn);
    expect(passwordInput.type).toBe('text');
    expect(screen.getByLabelText('إخفاء كلمة المرور')).toBeInTheDocument();

    // Click to hide password
    fireEvent.click(screen.getByLabelText('إخفاء كلمة المرور'));
    expect(passwordInput.type).toBe('password');
  });

  it('displays authentication error state when login fails', async () => {
    mockLogin.mockRejectedValueOnce({
      message: 'تعذّر تسجيل الدخول، تحقق من بيانات الدخول وحاول مرة أخرى.',
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const usernameInput = screen.getByPlaceholderText('اسم المستخدم أو البريد');
    const passwordInput = screen.getByPlaceholderText('كلمة المرور');
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });

    fireEvent.change(usernameInput, { target: { value: 'admin@school.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText('تعذّر تسجيل الدخول، تحقق من بيانات الدخول وحاول مرة أخرى.')
      ).toBeInTheDocument();
    });
  });

  it('handles successful login and routes to dashboard', async () => {
    mockLogin.mockResolvedValueOnce({
      user: { id: 1, role: 'school_admin' },
      has_multiple_contexts: false,
      default_membership_id: 10,
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const usernameInput = screen.getByPlaceholderText('اسم المستخدم أو البريد');
    const passwordInput = screen.getByPlaceholderText('كلمة المرور');
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });

    fireEvent.change(usernameInput, { target: { value: 'school_admin' } });
    fireEvent.change(passwordInput, { target: { value: 'Secret123!' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'school_admin',
        password: 'Secret123!',
      });
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });
  });

  it('redirects to /unauthorized if logged-in user is not a school_admin or super_admin', async () => {
    mockLogin.mockResolvedValueOnce({
      user: { id: 2, role: 'teacher' },
      has_multiple_contexts: false,
      default_membership_id: 15,
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const usernameInput = screen.getByPlaceholderText('اسم المستخدم أو البريد');
    const passwordInput = screen.getByPlaceholderText('كلمة المرور');
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });

    fireEvent.change(usernameInput, { target: { value: 'teacher1' } });
    fireEvent.change(passwordInput, { target: { value: 'Secret123!' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/unauthorized', { replace: true });
    });
  });

  it('routes to /select-context if user has multiple contexts without a default membership', async () => {
    mockLogin.mockResolvedValueOnce({
      user: { id: 1, role: 'school_admin' },
      has_multiple_contexts: true,
      default_membership_id: null,
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const usernameInput = screen.getByPlaceholderText('اسم المستخدم أو البريد');
    const passwordInput = screen.getByPlaceholderText('كلمة المرور');
    const submitBtn = screen.getByRole('button', { name: 'تسجيل الدخول' });

    fireEvent.change(usernameInput, { target: { value: 'multi_admin' } });
    fireEvent.change(passwordInput, { target: { value: 'Secret123!' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/select-context', { replace: true });
    });
  });
});
