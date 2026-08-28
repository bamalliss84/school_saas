import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { ContextSelectorModal } from '../components/feedback/ContextSelectorModal';
import * as UseAuthModule from '../context/useAuth';
import { SchoolMembership } from '../types/context';
import { AuthContextType } from '../context/authContextDef';

const mockSwitchContext = vi.fn();
const mockSetShowContextModal = vi.fn();

const mockActiveMembership: SchoolMembership = {
  membership_id: 101,
  school: { id: 1, name: 'مدرسة النور الأهلية النموذجية' },
  role: 'school_admin',
  status: 'active',
  access_mode: 'read_write',
  is_default: true,
  is_current_school: true,
  academic_year: { id: 1, name: 'العام الدراسي 2026/2027' },
  can_write: true,
  start_date: '2026-09-01',
  end_date: null,
  last_used_at: null,
  unread_notifications_count: 2,
  unread_conversations_count: 1,
};

const mockSecondSchoolMembership: SchoolMembership = {
  membership_id: 102,
  school: { id: 2, name: 'مدرسة الفلاح الثانوية للبنين' },
  role: 'school_admin',
  status: 'active',
  access_mode: 'read_write',
  is_default: false,
  is_current_school: true,
  academic_year: { id: 2, name: 'العام الدراسي 2026/2027' },
  can_write: true,
  start_date: '2026-09-01',
  end_date: null,
  last_used_at: null,
  unread_notifications_count: 0,
  unread_conversations_count: 0,
};

const mockHistoricalMembership: SchoolMembership = {
  membership_id: 103,
  school: { id: 1, name: 'مدرسة النور الأهلية النموذجية' },
  role: 'school_admin',
  status: 'historical',
  access_mode: 'read_only',
  is_default: false,
  is_current_school: false,
  academic_year: { id: 3, name: 'العام الدراسي 2025/2026' },
  can_write: false,
  start_date: '2025-09-01',
  end_date: '2026-06-30',
  last_used_at: null,
  unread_notifications_count: 0,
  unread_conversations_count: 0,
};

const mockSuspendedMembership: SchoolMembership = {
  membership_id: 104,
  school: { id: 4, name: 'مدرسة المستقبل المعلقة' },
  role: 'school_admin',
  status: 'suspended',
  access_mode: 'unavailable',
  is_default: false,
  is_current_school: false,
  academic_year: { id: 4, name: 'العام الدراسي 2026/2027' },
  can_write: false,
  start_date: '2026-09-01',
  end_date: null,
  last_used_at: null,
  unread_notifications_count: 0,
  unread_conversations_count: 0,
};

const mockAuthContextValue: AuthContextType = {
  user: {
    id: 1,
    username: 'admin_test',
    email: 'admin@school.com',
    full_name: 'مدير المدرسة',
    role: 'school_admin',
  },
  activeMembership: mockActiveMembership,
  allMemberships: [
    mockActiveMembership,
    mockSecondSchoolMembership,
    mockHistoricalMembership,
    mockSuspendedMembership,
  ],
  isAuthenticated: true,
  isLoading: false,
  isHistorical: false,
  isReadOnly: false,
  isSchoolAdmin: true,
  showContextModal: true,
  login: vi.fn(),
  logout: vi.fn(),
  switchContext: mockSwitchContext,
  refreshContexts: vi.fn(),
  setShowContextModal: mockSetShowContextModal,
};

describe('ContextSelectorModal (W1-D4 Active Context Selector)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(mockAuthContextValue);
  });

  it('renders modal with title, context cards, and current active context highlighted', () => {
    render(<ContextSelectorModal />);

    // Header
    expect(screen.getByText('اختيار المدرسة والسياق الأكاديمي')).toBeInTheDocument();
    expect(screen.getByText('حدد سياق المدرسة والعام الدراسي لإدارة العمليات التشغيلية')).toBeInTheDocument();

    // Context cards
    expect(screen.getAllByText('مدرسة النور الأهلية النموذجية').length).toBe(2);
    expect(screen.getByText('مدرسة الفلاح الثانوية للبنين')).toBeInTheDocument();
    expect(screen.getByText('مدرسة المستقبل المعلقة')).toBeInTheDocument();

    // Badges
    expect(screen.getByText('السياق الحالي')).toBeInTheDocument();
    expect(screen.getByText('الافتراضي')).toBeInTheDocument();
    expect(screen.getByText('أرشيف (للقراءة فقط)')).toBeInTheDocument();
    expect(screen.getByText('معلق')).toBeInTheDocument();
  });

  it('allows switching to a different authorized school context (multi-school)', async () => {
    render(<ContextSelectorModal />);

    // Click second school
    const secondSchoolCard = screen.getByText('مدرسة الفلاح الثانوية للبنين');
    await act(async () => {
      fireEvent.click(secondSchoolCard);
    });

    // Confirm button
    const confirmBtn = screen.getByRole('button', { name: 'تأكيد السياق' });
    await act(async () => {
      fireEvent.click(confirmBtn);
    });

    expect(mockSwitchContext).toHaveBeenCalledWith(mockSecondSchoolMembership, false);
  });

  it('allows setting context as default when switching active context', async () => {
    render(<ContextSelectorModal />);

    // Select second school
    const secondSchoolCard = screen.getByText('مدرسة الفلاح الثانوية للبنين');
    await act(async () => {
      fireEvent.click(secondSchoolCard);
    });

    // Check make default checkbox
    const defaultCheckbox = screen.getByLabelText('تعيين هذا السياق كافتراضي عند تسجيل الدخول القادم');
    await act(async () => {
      fireEvent.click(defaultCheckbox);
    });

    // Confirm
    const confirmBtn = screen.getByRole('button', { name: 'تأكيد السياق' });
    await act(async () => {
      fireEvent.click(confirmBtn);
    });

    expect(mockSwitchContext).toHaveBeenCalledWith(mockSecondSchoolMembership, true);
  });

  it('allows switching to a historical context and hides make-default option for archive', async () => {
    render(<ContextSelectorModal />);

    // Click historical year
    const historicalYearText = screen.getByText('العام الدراسي 2025/2026');
    await act(async () => {
      fireEvent.click(historicalYearText);
    });

    // Verify warning note appears
    expect(screen.getByText(/بيانات هذا العام الدراسي للعرض والأرشفة فقط/)).toBeInTheDocument();

    // Verify make default checkbox is NOT shown for historical context
    expect(screen.queryByLabelText('تعيين هذا السياق كافتراضي عند تسجيل الدخول القادم')).not.toBeInTheDocument();

    // Confirm switch to historical
    const confirmBtn = screen.getByRole('button', { name: 'تأكيد السياق' });
    await act(async () => {
      fireEvent.click(confirmBtn);
    });

    expect(mockSwitchContext).toHaveBeenCalledWith(mockHistoricalMembership, false);
  });

  it('blocks selection of suspended or ended contexts', async () => {
    render(<ContextSelectorModal />);

    const suspendedCard = screen.getByText('مدرسة المستقبل المعلقة');
    await act(async () => {
      fireEvent.click(suspendedCard);
    });

    // Confirm button should still trigger switch on the previously selected active membership, or remain safe
    const confirmBtn = screen.getByRole('button', { name: 'تأكيد السياق' });
    await act(async () => {
      fireEvent.click(confirmBtn);
    });

    // Should NOT have called with suspended membership
    expect(mockSwitchContext).not.toHaveBeenCalledWith(mockSuspendedMembership, expect.anything());
  });

  it('filters contexts list in real-time when searching', async () => {
    render(<ContextSelectorModal />);

    const searchInput = screen.getByPlaceholderText('بحث عن مدرسة أو عام دراسي...');
    await act(async () => {
      fireEvent.change(searchInput, { target: { value: 'الفلاح' } });
    });

    expect(screen.getByText('مدرسة الفلاح الثانوية للبنين')).toBeInTheDocument();
    expect(screen.queryByText('مدرسة المستقبل المعلقة')).not.toBeInTheDocument();
  });

  it('displays clean single-context UX when only 1 context is authorized', () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
      ...mockAuthContextValue,
      allMemberships: [mockActiveMembership],
    });

    render(<ContextSelectorModal />);

    expect(screen.getByText('لديك سياق مدرسي واحد متاح لهذا الحساب.')).toBeInTheDocument();
    expect(screen.queryByPlaceholderText('بحث عن مدرسة أو عام دراسي...')).not.toBeInTheDocument();
  });

  it('handles error during context switch and displays clear Arabic alert without corrupting state', async () => {
    mockSwitchContext.mockRejectedValueOnce(new Error('فشل في الاتصال بالخادم'));

    render(<ContextSelectorModal />);

    const secondSchoolCard = screen.getByText('مدرسة الفلاح الثانوية للبنين');
    await act(async () => {
      fireEvent.click(secondSchoolCard);
    });

    const confirmBtn = screen.getByRole('button', { name: 'تأكيد السياق' });
    await act(async () => {
      fireEvent.click(confirmBtn);
    });

    expect(await screen.findByText('فشل في الاتصال بالخادم')).toBeInTheDocument();
    // Modal stays open so user can retry
    expect(mockSetShowContextModal).not.toHaveBeenCalledWith(false);
  });

  it('closes modal when cancel button or X button is clicked', async () => {
    render(<ContextSelectorModal />);

    const cancelBtn = screen.getByRole('button', { name: 'إلغاء' });
    await act(async () => {
      fireEvent.click(cancelBtn);
    });

    expect(mockSetShowContextModal).toHaveBeenCalledWith(false);
  });

  it('does not render when showContextModal is false', () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
      ...mockAuthContextValue,
      showContextModal: false,
    });

    const { container } = render(<ContextSelectorModal />);
    expect(container).toBeEmptyDOMElement();
  });
});
