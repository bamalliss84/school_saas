import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthContextType } from '../context/authContextDef';
import * as UseAuthModule from '../context/useAuth';
import { ChangePasswordPage } from '../pages/ChangePasswordPage';
import { authService } from '../services/authService';

const logout = vi.fn();

describe('Change password page', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    logout.mockReset();
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({ logout } as unknown as AuthContextType);
  });

  const fill = (current: string, next: string, confirm: string) => {
    fireEvent.change(screen.getByLabelText('كلمة المرور الحالية'), { target: { value: current } });
    fireEvent.change(screen.getByLabelText('كلمة المرور الجديدة'), { target: { value: next } });
    fireEvent.change(screen.getByLabelText('تأكيد كلمة المرور الجديدة'), { target: { value: confirm } });
    fireEvent.click(screen.getByRole('button', { name: 'حفظ' }));
  };

  it('validates locally before calling the server', () => {
    const spy = vi.spyOn(authService, 'changePassword');
    render(<MemoryRouter><ChangePasswordPage /></MemoryRouter>);
    fill('old-pass-1', 'Strong-Pass-1', 'Other-Pass-1');
    expect(screen.getByRole('alert')).toHaveTextContent('غير متطابقتين');
    expect(spy).not.toHaveBeenCalled();
  });

  it('changes the password then asks to sign in again', async () => {
    const spy = vi.spyOn(authService, 'changePassword').mockResolvedValue({ detail: 'ok' });
    render(<MemoryRouter><ChangePasswordPage /></MemoryRouter>);
    fill('old-pass-1', 'Strong-Pass-1', 'Strong-Pass-1');
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('تم تغيير كلمة المرور'));
    expect(spy).toHaveBeenCalledWith('old-pass-1', 'Strong-Pass-1');
    fireEvent.click(screen.getByRole('button', { name: 'تسجيل الدخول من جديد' }));
    expect(logout).toHaveBeenCalled();
  });

  it('shows the server field error', async () => {
    vi.spyOn(authService, 'changePassword').mockRejectedValue({ errors: { current_password: ['كلمة المرور الحالية غير صحيحة'] } });
    render(<MemoryRouter><ChangePasswordPage /></MemoryRouter>);
    fill('wrong', 'Strong-Pass-1', 'Strong-Pass-1');
    expect(await screen.findByRole('alert')).toHaveTextContent('غير صحيحة');
  });
});
