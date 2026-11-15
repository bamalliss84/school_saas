import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ToastContainer } from '../components/feedback/Toast';
import { ToastProvider } from '../context/ToastContext';
import { AuthContextType } from '../context/authContextDef';
import * as UseAuthModule from '../context/useAuth';
import { FeesPage } from '../pages/FeesPage';
import { SubscriptionPage } from '../pages/SubscriptionPage';
import { PlatformPage } from '../pages/PlatformPage';
import { SubscriptionBanner } from '../components/layout/SubscriptionBanner';
import { billingService, type StudentFee } from '../services/billingService';
import { academicService } from '../services/academicService';

vi.mock('../services/billingService', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/billingService')>();
  const fns = Object.fromEntries(Object.keys(actual.billingService).map((key) => [key, vi.fn()]));
  return { ...actual, billingService: fns };
});
vi.mock('../services/academicService', () => ({ academicService: { getClassrooms: vi.fn(), getSections: vi.fn() } }));

const membership = {
  membership_id: 1, school: { id: 1, name: 'School A' }, role: 'school_admin', academic_year: { id: 11, name: '2026' },
  access_mode: 'read_write', status: 'active', is_default: true, is_current_school: true, can_write: true,
  start_date: '', end_date: '', last_used_at: null, unread_notifications_count: 0, unread_conversations_count: 0,
};
const baseAuth = {
  user: { id: 1, username: 'admin', email: '', full_name: 'Admin', role: 'school_admin' },
  activeMembership: membership, allMemberships: [], isLoading: false, isAuthenticated: true, isHistorical: false,
  isReadOnly: false, isSchoolAdmin: true, showContextModal: false, login: vi.fn(), logout: vi.fn(),
  switchContext: vi.fn(), refreshContexts: vi.fn(), setShowContextModal: vi.fn(),
} as unknown as AuthContextType;

const summary = {
  currency: 'YER', total: '150000.00', paid: '50000.00', remaining: '100000.00', overdue: '20000.00',
  overdue_count: 1, fee_count: 3, next_due: null, collected_this_month: '50000.00',
  by_category: [{ id: 1, name: 'رسوم دراسية', currency: 'YER', total: '150000.00', paid: '50000.00', remaining: '100000.00', overdue: '20000.00', overdue_count: 1, fee_count: 3, next_due: null }],
};
const fee: StudentFee = {
  id: 7, student: 10, student_name: 'ليان أحمد', student_code: 'A-S1', category: 1, category_name: 'رسوم دراسية',
  title: 'الفصل الأول', amount: '50000.00', discount: '0.00', net_amount: '50000.00', paid_amount: '0.00',
  balance: '50000.00', currency: 'YER', due_date: '2026-12-01', status: 'open', payment_state: 'unpaid',
  cancel_reason: '', installment_number: 1, installment_count: 2,
};
const category = { id: 1, name: 'رسوم دراسية', description: '', is_active: true };
const paged = <T,>(results: T[]) => ({ count: results.length, next: null, previous: null, results });

const wrap = (node: React.ReactNode) => render(
  <MemoryRouter><ToastProvider>{node}<ToastContainer /></ToastProvider></MemoryRouter>,
);

describe('Release 1.1 fees (school admin)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(baseAuth);
    vi.mocked(billingService.categories).mockResolvedValue([category]);
    vi.mocked(billingService.feeSummary).mockResolvedValue(summary);
    vi.mocked(billingService.fees).mockResolvedValue({ ...paged([fee]), summary });
    vi.mocked(academicService.getClassrooms).mockResolvedValue(paged([{ id: 3, name: 'الأول' }]) as never);
    vi.mocked(academicService.getSections).mockResolvedValue(paged([]) as never);
  });

  it('shows the collection overview', async () => {
    wrap(<FeesPage />);
    expect(await screen.findByText('إجمالي المستحق')).toBeInTheDocument();
    expect(screen.getAllByText(/150,000|١٥٠/).length).toBeGreaterThan(0);
    expect(screen.getByText('1 قسط متأخر')).toBeInTheDocument();
  });

  it('records a manual payment and shows the receipt number', async () => {
    vi.mocked(billingService.recordPayment).mockResolvedValue({
      id: 1, student_fee: 7, student_id: 10, student_name: 'ليان أحمد', fee_title: 'الفصل الأول', amount: '20000.00',
      currency: 'YER', method: 'cash', reference: '', paid_on: '2026-11-15', receipt_number: 'R2026-000001', is_void: false, void_reason: '',
    });
    wrap(<FeesPage />);
    fireEvent.click(await screen.findByRole('tab', { name: 'رسوم الطلاب' }));
    fireEvent.click(await screen.findByRole('button', { name: 'دفعة' }));
    const form = screen.getByRole('form', { name: 'تسجيل دفعة' });
    fireEvent.change(form.querySelector('input[type="number"]') as HTMLInputElement, { target: { value: '20000' } });
    fireEvent.click(screen.getByRole('button', { name: 'حفظ الدفعة' }));
    await waitFor(() => expect(screen.getByText(/R2026-000001/)).toBeInTheDocument());
    expect(billingService.recordPayment).toHaveBeenCalledWith(7, expect.objectContaining({ amount: '20000', method: 'cash' }));
  });

  it('previews before issuing and only creates on confirmation', async () => {
    const preview = {
      confirmed: false, student_count: 3, installment_count: 1, amount_per_student: '50000.00', discount_per_student: '0.00',
      total_net: '150000.00', students: [{ id: 10, full_name: 'ليان أحمد', classroom: 'الأول', section: 'أ' }],
    };
    vi.mocked(billingService.issueFees)
      .mockResolvedValueOnce(preview)
      .mockResolvedValueOnce({ ...preview, confirmed: true, created: 3 });
    wrap(<FeesPage />);
    fireEvent.click(await screen.findByRole('tab', { name: 'إصدار رسوم' }));
    fireEvent.change(await screen.findByPlaceholderText('مثال: رسوم الفصل الأول'), { target: { value: 'الفصل الأول' } });
    const amount = screen.getByRole('form', { name: 'إصدار رسوم' }).querySelector('input[type="number"]') as HTMLInputElement;
    fireEvent.change(amount, { target: { value: '50000' } });
    fireEvent.click(screen.getByRole('button', { name: 'معاينة' }));
    expect(await screen.findByText(/سيتم إصدار الرسوم لعدد 3 طالب/)).toBeInTheDocument();
    expect(billingService.issueFees).toHaveBeenLastCalledWith(expect.objectContaining({ confirm: false, scope: 'school', amount: '50000' }));
    fireEvent.click(screen.getByRole('button', { name: 'تأكيد الإصدار' }));
    await waitFor(() => expect(billingService.issueFees).toHaveBeenLastCalledWith(expect.objectContaining({ confirm: true })));
    expect(await screen.findByText(/تم إصدار 3 سجل رسوم/)).toBeInTheDocument();
  });

  it('hides write actions in a historical read-only context', async () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({ ...baseAuth, isReadOnly: true, isHistorical: true });
    wrap(<FeesPage />);
    expect(screen.queryByRole('tab', { name: 'إصدار رسوم' })).not.toBeInTheDocument();
    fireEvent.click(await screen.findByRole('tab', { name: 'رسوم الطلاب' }));
    expect(await screen.findByText('ليان أحمد')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'دفعة' })).not.toBeInTheDocument();
  });
});

describe('Release 1.1 subscriptions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(baseAuth);
  });

  const status = {
    has_subscription: true, status: 'past_due', warning: 'past_due',
    plan: { id: 1, code: 'standard', name: 'القياسية', billing_period: 'yearly', features: ['الحضور', 'الرسوم'] },
    start_date: '2026-01-01', end_date: '2026-12-31', days_left: 46, student_count: 120, student_limit: 500,
    price_per_student: '5000.00', currency: 'YER', outstanding: '115000.00', invoices: [],
  };

  it('school admin sees plan, warning and features read-only', async () => {
    vi.mocked(billingService.subscription).mockResolvedValue(status);
    wrap(<SubscriptionPage />);
    expect(await screen.findByText('القياسية')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('مبلغ متأخر');
    expect(screen.getByText('الرسوم')).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('banner warns school admins but stays quiet without a warning', async () => {
    vi.mocked(billingService.subscription).mockResolvedValueOnce(status);
    const { unmount } = wrap(<SubscriptionBanner />);
    expect(await screen.findByRole('status')).toHaveTextContent('مبلغ متأخر');
    unmount();
    vi.mocked(billingService.subscription).mockResolvedValueOnce({ ...status, warning: null });
    wrap(<SubscriptionBanner />);
    await waitFor(() => expect(billingService.subscription).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('banner does not query for teachers', () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({ ...baseAuth, activeMembership: { ...membership, role: 'teacher' } } as unknown as AuthContextType);
    wrap(<SubscriptionBanner />);
    expect(billingService.subscription).not.toHaveBeenCalled();
  });

  it('platform page is only for the owner without a school context', async () => {
    wrap(<PlatformPage />);
    expect(screen.getByText(/متاحة لمالك المنصة فقط/)).toBeInTheDocument();
    expect(billingService.platformSummary).not.toHaveBeenCalled();
  });

  it('platform owner sees the summary KPIs', async () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
      ...baseAuth, user: { ...baseAuth.user!, role: 'super_admin' }, activeMembership: null,
    } as unknown as AuthContextType);
    vi.mocked(billingService.platformSummary).mockResolvedValue({
      schools_total: 4, schools_active: 3, subscriptions: { active: 2, past_due: 1 }, schools_without_subscription: 1,
      expiring_soon: 1, outstanding: '115000.00', overdue: '115000.00', collected_this_month: '0.00', invoiced_this_year: '115000.00',
    });
    wrap(<PlatformPage />);
    expect(await screen.findByText('متأخرة السداد')).toBeInTheDocument();
    expect(screen.getByText('3 نشطة')).toBeInTheDocument();
  });
});
