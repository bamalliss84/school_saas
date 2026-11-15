import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ForgotPasswordPage, ResetPasswordPage } from '../pages/PasswordResetPages';
import { PrivacyPage, TermsPage } from '../pages/LegalPages';
import { authService } from '../services/authService';

describe('Release 1.0.1 password reset and legal pages', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('requests a reset link and shows the generic server message', async () => {
    const spy = vi.spyOn(authService, 'requestPasswordReset').mockResolvedValue({ detail: 'ستصلك رسالة' });
    render(<MemoryRouter><ForgotPasswordPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText('اسم المستخدم أو البريد الإلكتروني'), { target: { value: ' admin ' } });
    fireEvent.click(screen.getByRole('button', { name: 'إرسال رابط إعادة التعيين' }));
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('ستصلك رسالة'));
    expect(spy).toHaveBeenCalledWith('admin');
  });

  it('requires an identifier before calling the server', () => {
    const spy = vi.spyOn(authService, 'requestPasswordReset');
    render(<MemoryRouter><ForgotPasswordPage /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: 'إرسال رابط إعادة التعيين' }));
    expect(screen.getByRole('alert')).toHaveTextContent('أدخل اسم المستخدم');
    expect(spy).not.toHaveBeenCalled();
  });

  it('submits the new password with uid and token from the link', async () => {
    const spy = vi.spyOn(authService, 'confirmPasswordReset').mockResolvedValue({ detail: 'تم تغيير كلمة المرور' });
    render(<MemoryRouter initialEntries={['/reset-password?uid=MQ&token=abc-123']}><ResetPasswordPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText('كلمة المرور الجديدة'), { target: { value: 'Strong-Pass-1' } });
    fireEvent.change(screen.getByLabelText('تأكيد كلمة المرور'), { target: { value: 'Strong-Pass-1' } });
    fireEvent.click(screen.getByRole('button', { name: 'حفظ كلمة المرور' }));
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('تم تغيير كلمة المرور'));
    expect(spy).toHaveBeenCalledWith('MQ', 'abc-123', 'Strong-Pass-1');
  });

  it('validates mismatch locally and shows server field errors', async () => {
    vi.spyOn(authService, 'confirmPasswordReset').mockRejectedValue({ message: 'x', errors: { token: ['الرابط منتهي'] } });
    render(<MemoryRouter initialEntries={['/reset-password?uid=MQ&token=abc']}><ResetPasswordPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText('كلمة المرور الجديدة'), { target: { value: 'Strong-Pass-1' } });
    fireEvent.change(screen.getByLabelText('تأكيد كلمة المرور'), { target: { value: 'Other-Pass-1' } });
    fireEvent.click(screen.getByRole('button', { name: 'حفظ كلمة المرور' }));
    expect(screen.getByRole('alert')).toHaveTextContent('غير متطابقتين');
    fireEvent.change(screen.getByLabelText('تأكيد كلمة المرور'), { target: { value: 'Strong-Pass-1' } });
    fireEvent.click(screen.getByRole('button', { name: 'حفظ كلمة المرور' }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('الرابط منتهي'));
  });

  it('explains a broken link instead of showing the form', () => {
    render(<MemoryRouter initialEntries={['/reset-password']}><ResetPasswordPage /></MemoryRouter>);
    expect(screen.getByRole('heading', { name: 'رابط غير صالح' })).toBeInTheDocument();
    expect(screen.queryByLabelText('كلمة المرور الجديدة')).not.toBeInTheDocument();
  });

  it('renders the terms and privacy pages', () => {
    render(<MemoryRouter><TermsPage /></MemoryRouter>);
    expect(screen.getByRole('heading', { name: 'شروط الاستخدام' })).toBeInTheDocument();
    render(<MemoryRouter><PrivacyPage /></MemoryRouter>);
    expect(screen.getByRole('heading', { name: 'سياسة الخصوصية' })).toBeInTheDocument();
  });
});
