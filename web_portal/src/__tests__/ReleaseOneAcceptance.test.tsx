/**
 * Release 1.0 F1F–F1N Web acceptance tests (docs/RELEASE1_ADMIN_F1F_F1N.md).
 * Each test drives the real OperationsPage against mocked API responses that
 * mirror the backend contracts, and asserts the exact requests sent.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { OperationsPage } from '../pages/OperationsPage';
import { ToastProvider } from '../context/ToastContext';
import { ToastContainer } from '../components/feedback/Toast';
import * as UseAuthModule from '../context/useAuth';
import { AuthContextType } from '../context/authContextDef';
import { apiClient, ApiError } from '../services/apiClient';
import * as csv from '../utils/csv';
import * as excel from '../utils/excel';

vi.mock('../services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/apiClient')>();
  return { ...actual, apiClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() } };
});

vi.mock('../services/academicService', () => ({
  academicService: {
    getClassrooms: vi.fn().mockResolvedValue({ count: 1, next: null, previous: null, results: [{ id: 4, name: 'الصف الأول' }] }),
    getSections: vi.fn().mockResolvedValue({ count: 2, next: null, previous: null, results: [{ id: 6, name: 'أ' }, { id: 7, name: 'ب' }] }),
  },
}));

const auth = (readOnly = false): AuthContextType => ({
  user: { id: 1, username: 'admin', email: '', full_name: 'مدير', role: 'school_admin' },
  activeMembership: {
    membership_id: 10, school: { id: 10, name: 'مدرسة' }, role: 'school_admin',
    academic_year: { id: 5, name: '2026/2027' }, access_mode: readOnly ? 'read_only' : 'read_write',
    status: readOnly ? 'historical' : 'active', is_default: true, is_current_school: !readOnly, can_write: !readOnly,
    start_date: '2026-09-01', end_date: null, last_used_at: null,
    unread_notifications_count: 0, unread_conversations_count: 0,
  },
  allMemberships: [], isLoading: false, isAuthenticated: true, isHistorical: readOnly, isReadOnly: readOnly,
  isSchoolAdmin: true, showContextModal: false, login: vi.fn(), logout: vi.fn(), switchContext: vi.fn(),
  refreshContexts: vi.fn(), setShowContextModal: vi.fn(),
});

type Module = React.ComponentProps<typeof OperationsPage>['module'];
const renderPage = (module: Module) =>
  render(<MemoryRouter><ToastProvider><OperationsPage module={module} /><ToastContainer /></ToastProvider></MemoryRouter>);

const get = vi.mocked(apiClient.get);
const post = vi.mocked(apiClient.post);
const put = vi.mocked(apiClient.put);
const del = vi.mocked(apiClient.delete);
const routes = (table: Record<string, unknown>) =>
  get.mockImplementation(async (url: string) => (url in table ? table[url] : { results: [] }) as never);

const grid = {
  days: [{ value: 0, label: 'Sunday' }, { value: 1, label: 'Monday' }],
  periods: [
    { id: 1, name: 'الأولى', sequence: 1, start_time: '07:00:00', end_time: '07:45:00', kind: 'lesson' },
    { id: 2, name: 'الفسحة', sequence: 2, start_time: '07:45:00', end_time: '08:05:00', kind: 'break' },
  ],
  entries: [{ id: 50, weekday: 0, period: 1, subject: 'الرياضيات', teacher: 'أ. سالم', is_active: true, period_detail: { name: 'الأولى' } }],
};
const options = [{ id: 11, label: 'أ. سالم — الرياضيات' }];

beforeEach(() => {
  vi.clearAllMocks();
  vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(auth());
  routes({});
  post.mockResolvedValue({});
});

describe('F1F timetable', () => {
  beforeEach(() => routes({ '/timetable/grid/': grid, '/timetable/assignment-options/': options }));

  it('renders a days × periods grid with Arabic days and break rows', async () => {
    renderPage('timetable');
    const table = await screen.findByRole('table', { name: 'شبكة الجدول' });
    expect(within(table).getByText('الأحد')).toBeInTheDocument();
    expect(within(table).getByText('الاثنين')).toBeInTheDocument();
    expect(within(table).getByText('استراحة')).toBeInTheDocument();
    expect(within(table).getByText('الرياضيات')).toBeInTheDocument();
  });

  it('validates a new lesson first and shows conflicts without saving', async () => {
    post.mockImplementation(async (url: string) => (url === '/timetable/validate/'
      ? { valid: false, errors: [{ index: 0, code: 'teacher_conflict', weekday: 1, period_id: 1 }], valid_cells: 0 }
      : {}) as never);
    renderPage('timetable');
    await screen.findByRole('option', { name: 'أ. سالم — الرياضيات' });
    const addCard = screen.getByText('إضافة حصة').closest('div') as HTMLElement;
    const [day, period, assignment] = within(addCard).getAllByRole('combobox');
    fireEvent.change(day, { target: { value: '1' } });
    fireEvent.change(period, { target: { value: '1' } });
    fireEvent.change(assignment, { target: { value: '11' } });
    fireEvent.click(screen.getByText('إضافة'));
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('المعلم لديه حصة أخرى في هذه الفترة');
    expect(alert).toHaveTextContent('الاثنين');
    expect(post).toHaveBeenCalledWith('/timetable/validate/', { cells: [expect.objectContaining({ teacher_assignment_id: 11, weekday: 1, period_id: 1 })] });
    expect(post).not.toHaveBeenCalledWith('/timetable/bulk/', expect.anything());
  });

  it('saves a valid lesson through the atomic bulk endpoint', async () => {
    post.mockImplementation(async (url: string) => (url === '/timetable/validate/' ? { valid: true, errors: [], valid_cells: 1 } : {}) as never);
    renderPage('timetable');
    await screen.findByRole('option', { name: 'أ. سالم — الرياضيات' });
    const addCard = screen.getByText('إضافة حصة').closest('div') as HTMLElement;
    const [day, period, assignment] = within(addCard).getAllByRole('combobox');
    fireEvent.change(day, { target: { value: '1' } });
    fireEvent.change(period, { target: { value: '1' } });
    fireEvent.change(assignment, { target: { value: '11' } });
    fireEvent.click(screen.getByText('إضافة'));
    await waitFor(() => expect(post).toHaveBeenCalledWith('/timetable/bulk/', { cells: [expect.objectContaining({ action: 'upsert', weekday: 1 })] }));
  });

  it('replaces an existing lesson atomically through upsert with its id', async () => {
    post.mockImplementation(async (url: string) => (url === '/timetable/validate/' ? { valid: true, errors: [], valid_cells: 1 } : {}) as never);
    routes({ '/timetable/grid/': { ...grid, entries: [{ ...grid.entries[0], teacher_assignment: 11 }] }, '/timetable/assignment-options/': [...options, { id: 12, label: 'أ. منى — العلوم' }] });
    renderPage('timetable');
    fireEvent.click((await screen.findAllByText('استبدال'))[0]);
    expect(screen.getByText('استبدال حصة')).toBeInTheDocument();
    const addCard = screen.getByText('استبدال حصة').closest('div') as HTMLElement;
    fireEvent.change(within(addCard).getAllByRole('combobox')[2], { target: { value: '12' } });
    fireEvent.click(screen.getByText('حفظ الاستبدال'));
    await waitFor(() => expect(post).toHaveBeenCalledWith('/timetable/bulk/', {
      cells: [expect.objectContaining({ id: 50, action: 'upsert', teacher_assignment_id: 12, weekday: 0, period_id: 1 })],
    }));
  });

  it('configures working days and adds a break period', async () => {
    routes({ '/timetable/grid/': grid, '/timetable/assignment-options/': options, '/timetable/config/': { working_days: [0, 1] }, '/timetable/periods/': { results: grid.periods } });
    renderPage('timetable');
    fireEvent.click(await screen.findByText('إعداد الأيام والفترات'));
    const tuesday = await screen.findByLabelText('الثلاثاء');
    fireEvent.click(tuesday);
    fireEvent.click(screen.getByText('حفظ أيام العمل'));
    await waitFor(() => expect(put).toHaveBeenCalledWith('/timetable/config/', { working_days: [0, 1, 2] }));
    fireEvent.change(screen.getByLabelText('اسم الفترة'), { target: { value: 'الصلاة' } });
    fireEvent.change(screen.getByLabelText('الترتيب'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('البداية'), { target: { value: '09:00' } });
    fireEvent.change(screen.getByLabelText('النهاية'), { target: { value: '09:15' } });
    fireEvent.change(screen.getByLabelText('النوع'), { target: { value: 'break' } });
    fireEvent.click(screen.getByText('إضافة فترة'));
    await waitFor(() => expect(post).toHaveBeenCalledWith('/timetable/periods/', {
      name: 'الصلاة', sequence: 3, start_time: '09:00', end_time: '09:15', kind: 'break',
    }));
  });

  it('previews a day copy and only commits after confirmation', async () => {
    post.mockImplementation(async (_url: string, body: unknown) => ((body as { validate_only?: boolean }).validate_only
      ? { valid: true, errors: [], valid_cells: 3 } : { created_or_updated: 3 }) as never);
    renderPage('timetable');
    await screen.findByRole('table', { name: 'شبكة الجدول' });
    fireEvent.change(screen.getByLabelText('من يوم'), { target: { value: '0' } });
    fireEvent.change(screen.getByLabelText('إلى يوم'), { target: { value: '1' } });
    fireEvent.click(screen.getByLabelText('مسح حصص الهدف أولًا'));
    fireEvent.click(screen.getByText('معاينة النسخ'));
    expect(await screen.findByRole('status')).toHaveTextContent('3');
    expect(post).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('تأكيد النسخ'));
    await waitFor(() => expect(post).toHaveBeenLastCalledWith('/timetable/copy-day/', expect.objectContaining({
      source_classroom_id: 4, source_section_id: 6, target_section_id: 6,
      source_weekday: 0, target_weekday: 1, clear_target: true, validate_only: false,
    })));
  });

  it('historical context hides every timetable mutation control', async () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(auth(true));
    renderPage('timetable');
    await screen.findByRole('table', { name: 'شبكة الجدول' });
    for (const text of ['إضافة حصة', 'إعداد الأيام والفترات', 'نسخ الجدول', 'حذف', 'تعطيل']) {
      expect(screen.queryByText(text)).not.toBeInTheDocument();
    }
  });
});

describe('F1G attendance bulk recording', () => {
  const day = { date: '2026-11-12', total_students: 2, recorded: 1, present: 1, absent: 0, late: 0, excused: 0, not_recorded: 1 };
  const records = { results: [{ id: 1, student_enrollment: 100, student: { full_name: 'سارة' }, status: 'present' }] };
  const roster = { results: [
    { id: 1, full_name: 'سارة', student_code: 'S1', current_enrollment: { id: 100, section: { id: 6, name: 'أ' }, classroom: { id: 4, name: 'الصف الأول' } } },
    { id: 2, full_name: 'خالد', student_code: 'S2', current_enrollment: { id: 101, section: { id: 6, name: 'أ' }, classroom: { id: 4, name: 'الصف الأول' } } },
  ] };

  it('records only unrecorded students with a chosen assignment', async () => {
    routes({ '/attendance/': records, '/attendance/daily/': day, '/timetable/assignment-options/': options, '/students/': roster });
    renderPage('attendance');
    await screen.findByRole('option', { name: 'الصف الأول' });
    fireEvent.change(screen.getByLabelText('الصف'), { target: { value: '4' } });
    await screen.findByRole('option', { name: 'أ' });
    await waitFor(() => expect(get).toHaveBeenCalledWith('/timetable/assignment-options/', expect.anything()));
    fireEvent.click(await screen.findByText('تسجيل جماعي لغير المسجلين'));
    const list = await screen.findByRole('list', { name: 'طلاب غير مسجلين' });
    expect(within(list).getByText('خالد')).toBeInTheDocument();
    expect(within(list).queryByText('سارة')).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('حفظ حضور 1 طالب'));
    expect(post).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText('التكليف'), { target: { value: '11' } });
    fireEvent.change(screen.getByLabelText('حالة خالد'), { target: { value: 'absent' } });
    fireEvent.click(screen.getByText('حفظ حضور 1 طالب'));
    await waitFor(() => expect(post).toHaveBeenCalledWith('/attendance/bulk/', {
      teacher_assignment_id: 11, attendance_date: expect.any(String),
      students: [{ student_enrollment_id: 101, status: 'absent' }],
    }));
    expect(get).toHaveBeenCalledWith('/students/', { params: expect.objectContaining({ classroom_id: 4, section_id: 6, is_current: true }) });
  });

  it('hides bulk recording and status editing in historical context', async () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(auth(true));
    routes({ '/attendance/': records, '/attendance/daily/': day });
    renderPage('attendance');
    await screen.findByRole('group', { name: 'ملخص الحضور اليومي' });
    expect(screen.queryByText('تسجيل جماعي لغير المسجلين')).not.toBeInTheDocument();
    expect(screen.queryByRole('combobox', { name: /حالة/ })).not.toBeInTheDocument();
  });
});

describe('F1H homework', () => {
  const homework = { results: [
    { id: 70, title: 'تمارين الكسور', status: 'draft', can_publish: true, can_close: false },
    { id: 71, title: 'قراءة', status: 'published', can_publish: false, can_close: true },
  ] };

  it('publishes, closes and confirms before deleting a draft', async () => {
    routes({ '/homework/': homework });
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValueOnce(false).mockReturnValueOnce(true);
    renderPage('homework');
    fireEvent.click(await screen.findByText('نشر'));
    await waitFor(() => expect(post).toHaveBeenCalledWith('/homework/70/publish/', undefined));
    fireEvent.click(await screen.findByText('إغلاق'));
    await waitFor(() => expect(post).toHaveBeenCalledWith('/homework/71/close/', undefined));
    fireEvent.click(await screen.findByText('حذف'));
    expect(del).not.toHaveBeenCalled();
    fireEvent.click(await screen.findByText('حذف'));
    await waitFor(() => expect(del).toHaveBeenCalledWith('/homework/70/', undefined));
    expect(confirmSpy).toHaveBeenCalledTimes(2);
  });

  it('creates homework through class → section → subject → teacher assignment', async () => {
    routes({ '/homework/': { results: [] }, '/timetable/assignment-options/': [
      { id: 11, teacher: 'أ. سالم', subject: 'الرياضيات', label: 'أ. سالم — الرياضيات' },
      { id: 12, teacher: 'أ. منى', subject: 'العلوم', label: 'أ. منى — العلوم' },
    ] });
    renderPage('homework');
    fireEvent.click(await screen.findByText('إضافة واجب'));
    const title = screen.getByLabelText('عنوان الواجب');
    const last = (name: string) => screen.getAllByLabelText(name).at(-1) as HTMLElement;
    await screen.findAllByRole('option', { name: 'الصف الأول' });
    fireEvent.change(last('الصف'), { target: { value: '4' } });
    await waitFor(() => expect(last('الشعبة')).not.toBeDisabled());
    await waitFor(() => expect(within(last('الشعبة')).getByRole('option', { name: 'أ' })).toBeInTheDocument());
    fireEvent.change(last('الشعبة'), { target: { value: '6' } });
    await waitFor(() => expect(within(last('المادة')).getByRole('option', { name: 'العلوم' })).toBeInTheDocument());
    fireEvent.change(last('المادة'), { target: { value: 'العلوم' } });
    const teacher = last('المعلم');
    expect(within(teacher).queryByText(/أ. سالم/)).not.toBeInTheDocument();
    fireEvent.change(teacher, { target: { value: '12' } });
    fireEvent.change(title, { target: { value: 'تجربة الطفو' } });
    fireEvent.change(screen.getByLabelText('موعد التسليم'), { target: { value: '2026-11-20T10:00' } });
    fireEvent.click(screen.getByText('حفظ كمسودة'));
    await waitFor(() => expect(post).toHaveBeenCalledWith('/homework/', expect.objectContaining({
      teacher_assignment: 12, title: 'تجربة الطفو', due_date: '2026-11-20T10:00',
    })));
    expect(get).toHaveBeenCalledWith('/timetable/assignment-options/', { params: { classroom_id: 4, section_id: 6 } });
  });

  it('lets a historical admin read submissions but not change homework', async () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(auth(true));
    routes({ '/homework/': homework, '/homework/70/student-status/': { students: [{ student_id: 1, full_name: 'سارة', status: 'submitted' }] } });
    renderPage('homework');
    await screen.findByText('تمارين الكسور');
    expect(screen.queryByText('نشر')).not.toBeInTheDocument();
    expect(screen.queryByText('حذف')).not.toBeInTheDocument();
    expect(screen.queryByText('إضافة واجب')).not.toBeInTheDocument();
    fireEvent.click(screen.getAllByText('التسليمات')[0]);
    await waitFor(() => expect(get).toHaveBeenCalledWith('/homework/70/student-status/'));
  });
});

describe('F1I conversations and announcement lifecycle', () => {
  const conversation = { id: 9, conversation_type: 'teacher_parent', subject: 'متابعة', status: 'open', can_close: true, can_reopen: false, can_reply: true };

  it('reads messages, sends a reply and closes the conversation', async () => {
    routes({ '/conversations/': { results: [conversation] }, '/conversations/9/messages/': { results: [{ id: 1, body: 'السلام عليكم', sender: { display_name: 'ولي الأمر' } }] } });
    post.mockImplementation(async (url: string) => (url.endsWith('/close/') ? { ...conversation, status: 'closed', can_close: false, can_reopen: true } : {}) as never);
    renderPage('messages');
    fireEvent.click(await screen.findByText('فتح'));
    expect(await screen.findByText('السلام عليكم')).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText('اكتب الرد'), { target: { value: 'أهلًا' } });
    fireEvent.click(screen.getByText('إرسال'));
    await waitFor(() => expect(post).toHaveBeenCalledWith('/conversations/9/messages/', { body: 'أهلًا' }));
    fireEvent.click(screen.getByText('إغلاق المحادثة'));
    await waitFor(() => expect(post).toHaveBeenCalledWith('/conversations/9/close/'));
    expect(await screen.findByText('إعادة فتح')).toBeInTheDocument();
  });

  it('runs the announcement lifecycle actions', async () => {
    routes({ '/announcements/': { results: [
      { id: 1, title: 'مسودة', status: 'draft', permissions: { can_publish: true } },
    ] } });
    renderPage('announcements');
    fireEvent.click(await screen.findByText('نشر'));
    await waitFor(() => expect(post).toHaveBeenCalledWith('/announcements/1/publish/', undefined));
  });
});

describe('F1M report export', () => {
  it('exports a real multi-line CSV with Arabic group labels', async () => {
    routes({ '/admin/reports/summary/': { filters: {}, students: { total: 3, active: 2 }, attendance: { rate: 90.5 } } });
    const download = vi.spyOn(csv, 'downloadCsv').mockImplementation(() => undefined);
    renderPage('reports');
    fireEvent.click(await screen.findByText('تصدير التقرير'));
    expect(download).toHaveBeenCalledTimes(1);
    const [name, text] = download.mock.calls[0];
    expect(name).toBe('reports.csv');
    const lines = text.split('\r\n');
    expect(lines[0]).toBe('group,metric,value');
    expect(lines).toHaveLength(4);
    expect(text).not.toContain('\\n');
    expect(lines[1]).toBe('الطلاب,الإجمالي,3');
  });
});

describe('F1N settings language and logo', () => {
  const settings = { school: { name: 'مدرسة' }, settings: { language: 'ar', logo_url: null } };

  it('saves language and uploads a logo as multipart', async () => {
    routes({ '/admin/settings/': settings });
    post.mockResolvedValue({ logo_url: 'http://testserver/media/school_logos/a.png' } as never);
    renderPage('settings');
    fireEvent.change(await screen.findByLabelText('اللغة'), { target: { value: 'en' } });
    fireEvent.click(screen.getByText('حفظ الإعدادات'));
    await waitFor(() => expect(vi.mocked(apiClient.patch)).toHaveBeenCalledWith('/admin/settings/', expect.objectContaining({ language: 'en' })));
    const file = new File(['png'], 'logo.png', { type: 'image/png' });
    fireEvent.change(screen.getByLabelText(/رفع شعار/), { target: { files: [file] } });
    await waitFor(() => expect(post).toHaveBeenCalledWith('/admin/settings/logo/', expect.any(FormData)));
    expect((post.mock.calls[0][1] as FormData).get('logo')).toBe(file);
    expect(await screen.findByAltText('شعار المدرسة')).toHaveAttribute('src', 'http://testserver/media/school_logos/a.png');
  });

  it('shows logo upload errors from the server', async () => {
    routes({ '/admin/settings/': settings });
    post.mockRejectedValueOnce(new ApiError(400, 'Upload a valid PNG, JPEG or WEBP image.', { logo: ['Upload a valid PNG, JPEG or WEBP image.'] }));
    renderPage('settings');
    fireEvent.change(await screen.findByLabelText(/رفع شعار/), { target: { files: [new File(['x'], 'logo.svg', { type: 'image/svg+xml' })] } });
    expect(await screen.findByText('Upload a valid PNG, JPEG or WEBP image.')).toBeInTheDocument();
  });

  it('historical context shows the logo read-only', async () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(auth(true));
    routes({ '/admin/settings/': { ...settings, settings: { ...settings.settings, logo_url: 'http://x/logo.png' } } });
    renderPage('settings');
    expect(await screen.findByAltText('شعار المدرسة')).toBeInTheDocument();
    expect(screen.queryByLabelText(/رفع شعار/)).not.toBeInTheDocument();
    expect(screen.getByLabelText('اللغة')).toBeDisabled();
  });
});

describe('F1L Excel import and export', () => {
  const xlsx = (name = 'students.xlsx') => new File(['PK'], name, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  const kindSelect = (container: HTMLElement) => container.querySelector('select') as HTMLSelectElement;

  it('downloads the Excel template and the Excel export for the selected kind', async () => {
    const download = vi.spyOn(excel, 'downloadBlob').mockImplementation(() => undefined);
    const blob = new Blob(['x']);
    get.mockImplementation(async (_url: string, opts?: { responseType?: string }) => (opts?.responseType === 'blob' ? blob : { kind: 'students', rows: [] }) as never);
    renderPage('data');
    fireEvent.click(await screen.findByText('تنزيل قالب Excel'));
    await waitFor(() => expect(download).toHaveBeenCalledWith('students-template.xlsx', blob));
    expect(get).toHaveBeenCalledWith('/admin/data/template/', { params: { kind: 'students' }, responseType: 'blob' });
    fireEvent.click(screen.getByText('تصدير Excel'));
    await waitFor(() => expect(download).toHaveBeenCalledWith('students.xlsx', blob));
    expect(get).toHaveBeenCalledWith('/admin/data/export/', { params: { kind: 'students', output: 'xlsx' }, responseType: 'blob' });
  });

  it('uploads an .xlsx to the parser, previews, then confirms through the existing import', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const rows = [{ full_name: 'سارة أحمد', gender: 'female' }];
    post
      .mockResolvedValueOnce({ kind: 'students', columns: ['full_name', 'gender'], rows })
      .mockResolvedValueOnce({ valid: true, confirmed: false, created: 0, preview_count: 1, errors: [] })
      .mockResolvedValueOnce({ valid: true, confirmed: true, created: 1, ids: [9] });
    renderPage('data');
    const input = await screen.findByLabelText('ملف الاستيراد (Excel أو CSV)');
    fireEvent.change(input, { target: { files: [xlsx()] } });
    await waitFor(() => expect(post).toHaveBeenCalledWith('/admin/data/import/parse/', expect.any(FormData)));
    const form = post.mock.calls[0][1] as FormData;
    expect(form.get('kind')).toBe('students');
    expect((form.get('file') as File).name).toBe('students.xlsx');
    expect(await screen.findByText('سارة أحمد')).toBeInTheDocument();
    fireEvent.click(await screen.findByRole('button', { name: /تأكيد استيراد 1 سجل/ }));
    await waitFor(() => expect(post).toHaveBeenCalledTimes(3));
    expect(post).toHaveBeenNthCalledWith(2, '/admin/data/import/', { kind: 'students', rows, confirm: false });
    expect(post).toHaveBeenNthCalledWith(3, '/admin/data/import/', { kind: 'students', rows, confirm: true });
  });

  it('shows the parser column errors and offers no import', async () => {
    post.mockRejectedValueOnce(new ApiError(400, 'Validation failed.', { columns: ['Unknown column: عمود غريب'] }));
    renderPage('data');
    fireEvent.change(await screen.findByLabelText('ملف الاستيراد (Excel أو CSV)'), { target: { files: [xlsx()] } });
    expect(await screen.findByText(/Unknown column: عمود غريب/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /تأكيد استيراد/ })).not.toBeInTheDocument();
  });

  it('exports operational data with a date range and hides import controls', async () => {
    const download = vi.spyOn(excel, 'downloadBlob').mockImplementation(() => undefined);
    get.mockImplementation(async (_url: string, opts?: { responseType?: string }) => (opts?.responseType === 'blob' ? new Blob(['x']) : { kind: 'attendance', rows: [] }) as never);
    const { container } = renderPage('data');
    await screen.findByText('تصدير Excel');
    fireEvent.change(kindSelect(container), { target: { value: 'attendance' } });
    fireEvent.change(await screen.findByLabelText('من تاريخ'), { target: { value: '2026-11-01' } });
    fireEvent.change(screen.getByLabelText('إلى تاريخ'), { target: { value: '2026-11-12' } });
    await waitFor(() => expect(get).toHaveBeenCalledWith('/admin/data/export/', { params: { kind: 'attendance', date_from: '2026-11-01', date_to: '2026-11-12' } }));
    expect(screen.queryByText('تنزيل قالب Excel')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('ملف الاستيراد (Excel أو CSV)')).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('تصدير Excel'));
    await waitFor(() => expect(download).toHaveBeenCalledWith('attendance.xlsx', expect.any(Blob)));
    expect(get).toHaveBeenCalledWith('/admin/data/export/', {
      params: { kind: 'attendance', date_from: '2026-11-01', date_to: '2026-11-12', output: 'xlsx' }, responseType: 'blob',
    });
  });

  it('lets a historical admin export Excel but not import', async () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(auth(true));
    renderPage('data');
    expect(await screen.findByLabelText('ملف الاستيراد (Excel أو CSV)')).toBeDisabled();
    expect(screen.getByText('تصدير Excel')).toBeEnabled();
  });
});
