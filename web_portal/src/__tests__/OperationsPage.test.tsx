import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { OperationsPage } from '../pages/OperationsPage';
import { ToastProvider } from '../context/ToastContext';
import * as UseAuthModule from '../context/useAuth';
import { AuthContextType } from '../context/authContextDef';
import { apiClient, ApiError } from '../services/apiClient';
import { academicService } from '../services/academicService';

vi.mock('../services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/apiClient')>();
  return {
    ...actual,
    apiClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() },
  };
});

vi.mock('../services/academicService', () => ({
  academicService: {
    getClassrooms: vi.fn().mockResolvedValue({ count: 0, next: null, previous: null, results: [] }),
    getSections: vi.fn().mockResolvedValue({ count: 0, next: null, previous: null, results: [] }),
  },
}));

const auth = (readOnly = false): AuthContextType => ({
  user: { id: 1, username: 'admin', email: '', full_name: 'مدير المدرسة', role: 'school_admin' },
  activeMembership: {
    membership_id: 10,
    school: { id: 10, name: 'مدرسة 10' },
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

type Module = React.ComponentProps<typeof OperationsPage>['module'];
const renderPage = (module: Module) =>
  render(<MemoryRouter><ToastProvider><OperationsPage module={module} /></ToastProvider></MemoryRouter>);

const get = vi.mocked(apiClient.get);
const post = vi.mocked(apiClient.post);
const patch = vi.mocked(apiClient.patch);

const uploadCsv = (container: HTMLElement, text: string) => {
  const input = container.querySelector('input[type="file"]') as HTMLInputElement;
  fireEvent.change(input, { target: { files: [new File([text], 'students.csv', { type: 'text/csv' })] } });
};

const guardianCsv = 'student_code,full_name,relationship\r\nS1,"Ahmed, Senior",father\r\nS2,Mona,mother\r\n';

describe('Release 1 admin operations page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(auth());
    get.mockResolvedValue({ rows: [] });
  });

  describe('data import', () => {
    it('shows row-level validation errors and never sends a confirming request', async () => {
      const confirmSpy = vi.spyOn(window, 'confirm');
      post.mockRejectedValueOnce(new ApiError(400, 'invalid', [
        { row: 3, errors: { student_code: ['Student was not found in the active school.'] } },
      ] as unknown as Record<string, unknown>));
      const { container } = renderPage('data');
      await screen.findByText('تصدير CSV');
      uploadCsv(container, guardianCsv);
      fireEvent.click(await screen.findByRole('button', { name: /تأكيد استيراد 2 سجل/ }));

      const alert = await screen.findByRole('alert');
      expect(alert).toHaveTextContent('أخطاء التحقق (1)');
      expect(alert).toHaveTextContent('السطر 3: student_code: Student was not found in the active school.');
      expect(post).toHaveBeenCalledTimes(1);
      expect(post.mock.calls[0][1]).toMatchObject({ confirm: false });
      expect(confirmSpy).not.toHaveBeenCalled();
    });

    it('parses quoted CSV, previews, then commits only after explicit confirmation', async () => {
      vi.spyOn(window, 'confirm').mockReturnValue(true);
      post
        .mockResolvedValueOnce({ valid: true, confirmed: false, created: 0, preview_count: 2, errors: [] })
        .mockResolvedValueOnce({ valid: true, confirmed: true, created: 2, ids: [1, 2] });
      const { container } = renderPage('data');
      await screen.findByText('تصدير CSV');
      fireEvent.change(container.querySelector('select') as HTMLSelectElement, { target: { value: 'guardians' } });
      await waitFor(() => expect(get).toHaveBeenCalledWith('/admin/data/export/', { params: { kind: 'guardians' } }));
      await screen.findByText('تصدير CSV');
      uploadCsv(container, guardianCsv);
      fireEvent.click(await screen.findByRole('button', { name: /تأكيد استيراد 2 سجل/ }));

      await waitFor(() => expect(post).toHaveBeenCalledTimes(2));
      const rows = [
        { student_code: 'S1', full_name: 'Ahmed, Senior', relationship: 'father' },
        { student_code: 'S2', full_name: 'Mona', relationship: 'mother' },
      ];
      expect(post).toHaveBeenNthCalledWith(1, '/admin/data/import/', { kind: 'guardians', rows, confirm: false });
      expect(post).toHaveBeenNthCalledWith(2, '/admin/data/import/', { kind: 'guardians', rows, confirm: true });
    });

    it('does not commit when the admin cancels the preview confirmation', async () => {
      vi.spyOn(window, 'confirm').mockReturnValue(false);
      post.mockResolvedValueOnce({ valid: true, confirmed: false, created: 0, preview_count: 2, errors: [] });
      const { container } = renderPage('data');
      await screen.findByText('تصدير CSV');
      uploadCsv(container, guardianCsv);
      fireEvent.click(await screen.findByRole('button', { name: /تأكيد استيراد 2 سجل/ }));
      await waitFor(() => expect(window.confirm).toHaveBeenCalled());
      expect(post).toHaveBeenCalledTimes(1);
    });
  });

  describe('historical read-only context', () => {
    beforeEach(() => {
      vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(auth(true));
    });

    it('disables settings editing and hides save', async () => {
      get.mockResolvedValue({ school: { name: 'مدرسة النور' }, settings: { timezone: 'Asia/Riyadh' } });
      renderPage('settings');
      expect(await screen.findByLabelText('اسم المدرسة')).toBeDisabled();
      expect(screen.queryByText('حفظ الإعدادات')).not.toBeInTheDocument();
      expect(screen.getByText(/وضع القراءة التاريخية/)).toBeInTheDocument();
    });

    it('disables CSV import and hides announcement creation', async () => {
      const view = renderPage('data');
      await screen.findByText('تصدير CSV');
      expect(view.container.querySelector('input[type="file"]')).toBeDisabled();
      view.unmount();
      renderPage('announcements');
      await waitFor(() => expect(get).toHaveBeenCalledWith('/announcements/', expect.anything()));
      expect(screen.queryByText('إضافة إعلان')).not.toBeInTheDocument();
    });
  });

  it('saves school settings in an active context', async () => {
    get.mockResolvedValue({ school: { name: 'مدرسة النور' }, settings: { timezone: 'Asia/Riyadh' } });
    patch.mockResolvedValue({});
    renderPage('settings');
    fireEvent.change(await screen.findByLabelText('اسم المدرسة'), { target: { value: 'مدرسة الأمل' } });
    fireEvent.click(screen.getByText('حفظ الإعدادات'));
    await waitFor(() => expect(patch).toHaveBeenCalledWith('/admin/settings/', expect.objectContaining({
      name: 'مدرسة الأمل', timezone: 'Asia/Riyadh',
    })));
  });

  it('shows onboarding progress with links only for incomplete steps', async () => {
    get.mockResolvedValue({ progress: 50, steps: [
      { key: 'classes', label: 'الصفوف', complete: false },
      { key: 'subjects', label: 'المواد', complete: true },
    ] });
    renderPage('onboarding');
    expect(await screen.findByRole('heading', { name: 'جاهزية المدرسة: 50%' })).toBeInTheDocument();
    const links = screen.getAllByRole('link', { name: 'إكمال الخطوة' });
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveAttribute('href', '/classes');
  });

  it('shows load errors with a working retry', async () => {
    get.mockRejectedValueOnce(new Error('تعذر تحميل التقرير'));
    renderPage('reports');
    expect(await screen.findByText('تعذر تحميل التقرير')).toBeInTheDocument();
    fireEvent.click(screen.getByText('إعادة المحاولة'));
    await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
  });

  describe('F1I announcements audience', () => {
    const openCreate = async () => {
      renderPage('announcements');
      fireEvent.click(await screen.findByText('إضافة إعلان'));
      fireEvent.change(screen.getByPlaceholderText('عنوان الإعلان'), { target: { value: 'اجتماع' } });
      fireEvent.change(screen.getByPlaceholderText('محتوى الإعلان'), { target: { value: 'تفاصيل' } });
    };

    it('requires and sends selected target roles', async () => {
      post.mockResolvedValue({});
      await openCreate();
      fireEvent.change(screen.getByLabelText('الجمهور'), { target: { value: 'roles' } });
      fireEvent.click(screen.getByText('حفظ كمسودة'));
      expect(post).not.toHaveBeenCalled();
      fireEvent.click(screen.getByLabelText('أولياء الأمور'));
      fireEvent.click(screen.getByLabelText('المعلمون'));
      fireEvent.click(screen.getByText('حفظ كمسودة'));
      await waitFor(() => expect(post).toHaveBeenCalledWith('/announcements/', expect.objectContaining({
        audience_type: 'roles', target_roles: ['parent', 'teacher'], classroom: null, section: null, include_parents: false,
      })));
    });

    it('targets a section with its classroom and optional parents', async () => {
      vi.mocked(academicService.getClassrooms).mockResolvedValue({ count: 1, next: null, previous: null, results: [{ id: 4, name: 'الصف الأول' }] } as never);
      vi.mocked(academicService.getSections).mockResolvedValue({ count: 1, next: null, previous: null, results: [{ id: 6, name: 'أ' }] } as never);
      post.mockResolvedValue({});
      await openCreate();
      fireEvent.change(screen.getByLabelText('الجمهور'), { target: { value: 'section' } });
      await screen.findByRole('option', { name: 'الصف الأول' });
      fireEvent.change(screen.getByLabelText('الصف المستهدف'), { target: { value: '4' } });
      await screen.findByRole('option', { name: 'أ' });
      fireEvent.change(screen.getByLabelText('الشعبة المستهدفة'), { target: { value: '6' } });
      fireEvent.click(screen.getByLabelText('تضمين أولياء الأمور'));
      fireEvent.click(screen.getByText('حفظ كمسودة'));
      await waitFor(() => expect(post).toHaveBeenCalledWith('/announcements/', expect.objectContaining({
        audience_type: 'section', classroom: 4, section: 6, target_roles: [], include_parents: true,
      })));
      vi.mocked(academicService.getClassrooms).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
      vi.mocked(academicService.getSections).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
    });

    it('keeps the form open when the backend rejects the announcement', async () => {
      post.mockRejectedValueOnce(new Error('rejected'));
      await openCreate();
      fireEvent.click(screen.getByText('حفظ كمسودة'));
      await waitFor(() => expect(post).toHaveBeenCalled());
      expect(screen.getByPlaceholderText('عنوان الإعلان')).toHaveValue('اجتماع');
    });
  });

  describe('F1I school support workflow', () => {
    const ticket = { id: 31, conversation_type: 'school_support', subject: 'طلب تعديل بيانات', status: 'open', can_close: true, can_reopen: false };
    const openTicket = async (status = 'open') => {
      get.mockImplementation(async (url: string) => (url === '/conversations/' ? { results: [{ ...ticket, status }] } : { results: [] }));
      renderPage('messages');
      fireEvent.click(await screen.findByText('فتح'));
      await screen.findByText(/طلب دعم مدرسي/);
    };

    it('assigns and resolves a support request with a resolution note', async () => {
      post.mockImplementation(async (url: string) => ({ ...ticket, status: url.endsWith('/assign/') ? 'in_progress' : 'resolved' }));
      await openTicket();
      fireEvent.click(screen.getByText('إسناد إليّ'));
      await waitFor(() => expect(post).toHaveBeenCalledWith('/school-inbox/31/assign/', {}));
      fireEvent.change(await screen.findByLabelText('ملاحظة الحل'), { target: { value: 'تم التحديث' } });
      fireEvent.click(screen.getByText('تم الحل'));
      await waitFor(() => expect(post).toHaveBeenCalledWith('/school-inbox/31/status/', { status: 'resolved', resolution_note: 'تم التحديث' }));
    });

    it('hides support actions in historical context', async () => {
      vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(auth(true));
      await openTicket();
      expect(screen.queryByText('إسناد إليّ')).not.toBeInTheDocument();
      expect(screen.queryByText('تم الحل')).not.toBeInTheDocument();
    });
  });

  it('F1G shows the daily attendance summary including not-recorded students', async () => {
    get.mockImplementation(async (url: string) => (url === '/attendance/daily/'
      ? { date: '2026-11-12', total_students: 30, recorded: 26, present: 22, absent: 2, late: 1, excused: 1, not_recorded: 4 }
      : { results: [] }));
    renderPage('attendance');
    const summary = await screen.findByRole('group', { name: 'ملخص الحضور اليومي' });
    expect(summary).toHaveTextContent('غير مسجَّل');
    expect(summary).toHaveTextContent('4');
    expect(get).toHaveBeenCalledWith('/attendance/daily/', expect.objectContaining({ params: expect.objectContaining({ date: expect.any(String) }) }));
  });
});
