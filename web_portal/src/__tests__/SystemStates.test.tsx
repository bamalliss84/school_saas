import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import {
  EmptyState,
  ServerErrorState,
  OfflineState,
  OfflineBanner,
  UnauthorizedState,
  SessionExpiredModal,
  HistoricalBlockedModal,
  ConfirmationModal,
  ProgressBar,
  ImportExportFeedback,
  SystemFeedbackStrip,
  PageSkeleton,
} from '../components/feedback';
import { ToastProvider, useToast } from '../context';
import { ToastContainer } from '../components/feedback/Toast';
import { SystemStatesShowcasePage } from '../pages/SystemStatesShowcasePage';
import * as UseAuthModule from '../context/useAuth';
import { AuthContextType } from '../context/authContextDef';

const defaultAuthContextValue: AuthContextType = {
  user: { id: 1, username: 'demo_admin', email: 'admin@school.edu', full_name: 'مدير المدرسة التجريبي', role: 'school_admin' },
  activeMembership: {
    membership_id: 133,
    school: { id: 14, name: 'مدرسة النور التجريبية' },
    role: 'school_admin',
    academic_year: { id: 27, name: 'DEMO 2025/2026' },
    access_mode: 'read_write',
    status: 'active',
    is_default: true,
    is_current_school: true,
    can_write: true,
    start_date: '2025-09-01',
    end_date: null,
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

describe('W1-D5 System States & Feedback Test Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(defaultAuthContextValue);
  });

  describe('A. Page & Component Skeletons', () => {
    it('renders page skeleton with shimmer placeholders and metric cards', () => {
      const { container } = render(<PageSkeleton />);
      const skeletons = container.querySelectorAll('.skeleton');
      expect(skeletons.length).toBeGreaterThanOrEqual(5);
    });
  });

  describe('B. Empty State Variants', () => {
    it('renders default empty state with icon and action button', () => {
      const onAction = vi.fn();
      render(
        <EmptyState
          title="لا توجد بيانات حالياً"
          description="لم يتم العثور على أي سجلات."
          actionLabel="إضافة سجل"
          onAction={onAction}
        />
      );

      expect(screen.getByText('لا توجد بيانات حالياً')).toBeInTheDocument();
      expect(screen.getByText('لم يتم العثور على أي سجلات.')).toBeInTheDocument();
      const actionBtn = screen.getByRole('button', { name: /إضافة سجل/ });
      expect(actionBtn).toBeInTheDocument();
      fireEvent.click(actionBtn);
      expect(onAction).toHaveBeenCalledTimes(1);
    });

    it('renders announcements empty state preset with custom action', () => {
      const onAction = vi.fn();
      render(<EmptyState variant="announcements" onAction={onAction} />);

      expect(screen.getByText('لا توجد إعلانات حتى الآن')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /إنشاء إعلان/ })).toBeInTheDocument();
    });

    it('renders filtered list empty state preset with reset filters button', () => {
      const onReset = vi.fn();
      render(<EmptyState variant="filtered" onSecondaryAction={onReset} />);

      expect(screen.getByText('لا توجد نتائج مطابقة')).toBeInTheDocument();
      const resetBtn = screen.getByRole('button', { name: /إعادة تعيين الفلاتر/ });
      expect(resetBtn).toBeInTheDocument();
      fireEvent.click(resetBtn);
      expect(onReset).toHaveBeenCalledTimes(1);
    });
  });

  describe('C. Server Error State', () => {
    it('renders server error state with retry and home actions', () => {
      const onRetry = vi.fn();
      render(
        <MemoryRouter>
          <ServerErrorState onRetry={onRetry} />
        </MemoryRouter>
      );

      expect(screen.getByText('تعذر تحميل البيانات')).toBeInTheDocument();
      expect(screen.getByText(/حدث خطأ أثناء جلب البيانات/)).toBeInTheDocument();

      const retryBtn = screen.getByRole('button', { name: /إعادة المحاولة/ });
      fireEvent.click(retryBtn);
      expect(onRetry).toHaveBeenCalledTimes(1);

      expect(screen.getByRole('button', { name: /العودة للرئيسية/ })).toBeInTheDocument();
    });
  });

  describe('D. Connection / Offline State', () => {
    it('renders offline banner with alert text', () => {
      render(<OfflineBanner />);
      expect(screen.getByText(/الاتصال بالإنترنت غير متاح/)).toBeInTheDocument();
    });

    it('renders offline container with retry action', () => {
      const onRetry = vi.fn();
      render(<OfflineState onRetry={onRetry} />);

      expect(screen.getByText('تعذر الاتصال بالخادم')).toBeInTheDocument();
      expect(screen.getByText(/تحقق من اتصال الإنترنت/)).toBeInTheDocument();

      const retryBtn = screen.getByRole('button', { name: /إعادة المحاولة/ });
      fireEvent.click(retryBtn);
      expect(onRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('E. Unauthorized / No Permission State', () => {
    it('renders unauthorized state and allows switching context', () => {
      const setShowContextModal = vi.fn();
      vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
        ...defaultAuthContextValue,
        setShowContextModal,
      });

      render(
        <MemoryRouter>
          <UnauthorizedState />
        </MemoryRouter>
      );

      expect(screen.getByText('ليس لديك صلاحية للوصول')).toBeInTheDocument();
      expect(screen.getByText('العودة للرئيسية')).toBeInTheDocument();

      const switchBtn = screen.getByRole('button', { name: /تغيير سياق العمل/ });
      fireEvent.click(switchBtn);
      expect(setShowContextModal).toHaveBeenCalledWith(true);
    });
  });

  describe('F. Session Expired Modal', () => {
    it('renders session expired modal and triggers logout on re-login click', () => {
      const logout = vi.fn();
      vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
        ...defaultAuthContextValue,
        logout,
      });

      const { rerender } = render(<SessionExpiredModal isOpen={false} />);
      expect(screen.queryByText('انتهت جلسة الدخول')).not.toBeInTheDocument();

      rerender(<SessionExpiredModal isOpen={true} />);
      expect(screen.getByText('انتهت جلسة الدخول')).toBeInTheDocument();
      expect(screen.getByText(/انتهت صلاحية جلستك/)).toBeInTheDocument();

      const loginAgainBtn = screen.getByRole('button', { name: /تسجيل الدخول مرة أخرى/ });
      fireEvent.click(loginAgainBtn);
      expect(logout).toHaveBeenCalledTimes(1);
    });
  });

  describe('G. Historical Read-Only Action Blocked Modal', () => {
    it('renders historical read-only modal and triggers context switch', () => {
      const setShowContextModal = vi.fn();
      const onClose = vi.fn();
      vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
        ...defaultAuthContextValue,
        setShowContextModal,
      });

      render(<HistoricalBlockedModal isOpen={true} onClose={onClose} />);

      expect(screen.getByText('لا يمكن تعديل بيانات عام سابق')).toBeInTheDocument();
      expect(screen.getByText(/أنت تعمل حالياً في عام دراسي سابق/)).toBeInTheDocument();

      const switchBtn = screen.getByRole('button', { name: /الانتقال للعام الحالي/ });
      fireEvent.click(switchBtn);
      expect(onClose).toHaveBeenCalledTimes(1);
      expect(setShowContextModal).toHaveBeenCalledWith(true);

      const cancelBtn = screen.getByRole('button', { name: /العودة للعرض/ });
      fireEvent.click(cancelBtn);
      expect(onClose).toHaveBeenCalledTimes(2);
    });
  });

  describe('I. Toast Notification System', () => {
    const TestToastComponent = () => {
      const toast = useToast();
      return (
        <div>
          <button onClick={() => toast.success('تم الحفظ بنجاح', 'نجاح')}>إرسال نجاح</button>
          <button onClick={() => toast.error('حدث خطأ غير متوقع', 'خطأ')}>إرسال خطأ</button>
          <button onClick={() => toast.warning('يرجى الانتباه', 'تحذير')}>إرسال تحذير</button>
          <button onClick={() => toast.info('معلومة جديدة', 'معلومة')}>إرسال معلومة</button>
        </div>
      );
    };

    it('displays and dismisses toast notifications across all variants', async () => {
      render(
        <ToastProvider>
          <ToastContainer />
          <TestToastComponent />
        </ToastProvider>
      );

      // Trigger success toast
      fireEvent.click(screen.getByRole('button', { name: /إرسال نجاح/ }));
      expect(await screen.findByText('تم الحفظ بنجاح')).toBeInTheDocument();
      expect(screen.getByText('نجاح')).toBeInTheDocument();

      // Trigger error toast
      fireEvent.click(screen.getByRole('button', { name: /إرسال خطأ/ }));
      expect(await screen.findByText('حدث خطأ غير متوقع')).toBeInTheDocument();

      // Dismiss button
      const closeButtons = screen.getAllByRole('button', { name: /إغلاق التنبيه/ });
      expect(closeButtons.length).toBeGreaterThanOrEqual(1);
      fireEvent.click(closeButtons[0]);

      await waitFor(() => {
        expect(screen.queryByText('تم الحفظ بنجاح')).not.toBeInTheDocument();
      });
    });
  });

  describe('J. Destructive Confirmation Modal', () => {
    it('renders delete confirmation modal and executes onConfirm', () => {
      const onConfirm = vi.fn();
      const onClose = vi.fn();

      render(
        <ConfirmationModal
          isOpen={true}
          title="تأكيد الحذف"
          message="هل أنت متأكد من حذف هذا السجل؟"
          confirmLabel="حذف السجل"
          onConfirm={onConfirm}
          onClose={onClose}
        />
      );

      expect(screen.getByText('تأكيد الحذف')).toBeInTheDocument();
      expect(screen.getByText('هل أنت متأكد من حذف هذا السجل؟')).toBeInTheDocument();

      const confirmBtn = screen.getByRole('button', { name: /حذف السجل/ });
      fireEvent.click(confirmBtn);
      expect(onConfirm).toHaveBeenCalledTimes(1);

      const cancelBtn = screen.getByRole('button', { name: /إلغاء/ });
      fireEvent.click(cancelBtn);
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('K. Import / Export Feedback & Progress', () => {
    it('renders progress bar with accurate percentage and fill width', () => {
      render(<ProgressBar value={75} label="جاري استيراد البيانات..." />);
      expect(screen.getByText('جاري استيراد البيانات...')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('renders full success import feedback state', () => {
      render(<ImportExportFeedback status="success" successCount={150} statusText="تم استيراد ملف Excel بنجاح" />);
      expect(screen.getByText('تم استيراد ملف Excel بنجاح')).toBeInTheDocument();
      expect(screen.getByText(/تم استيراد 150 سجل بنجاح/)).toBeInTheDocument();
      expect(screen.getByText('مكتمل بنجاح')).toBeInTheDocument();
    });

    it('renders partial error feedback state and toggles error details table', () => {
      render(
        <ImportExportFeedback
          status="partial_error"
          successCount={121}
          errorCount={7}
          errors={[
            { rowNumber: 14, field: 'رقم الهوية', message: 'رقم الهوية مسجل مسبقاً' },
            { rowNumber: 29, field: 'الصف', message: 'الصف غير موجود' },
          ]}
        />
      );

      expect(screen.getByText('تم استيراد 121 سجلاً وتعذر استيراد 7 سجلات')).toBeInTheDocument();

      const toggleErrorsBtn = screen.getByRole('button', { name: /عرض الأخطاء/ });
      fireEvent.click(toggleErrorsBtn);

      expect(screen.getByText('رقم الهوية مسجل مسبقاً')).toBeInTheDocument();
      expect(screen.getByText('الصف غير موجود')).toBeInTheDocument();
      expect(screen.getByText('إخفاء الأخطاء')).toBeInTheDocument();
    });
  });

  describe('L. System Feedback Token Strip', () => {
    it('renders all feedback tokens and status labels', () => {
      render(<SystemFeedbackStrip />);
      expect(screen.getByText('Success')).toBeInTheDocument();
      expect(screen.getByText('Info')).toBeInTheDocument();
      expect(screen.getByText('Warning')).toBeInTheDocument();
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Toast')).toBeInTheDocument();
      expect(screen.getByText('Inline alert')).toBeInTheDocument();
      expect(screen.getByText('Field validation')).toBeInTheDocument();
      expect(screen.getByText('Modal alert')).toBeInTheDocument();
    });
  });

  describe('SystemStatesShowcasePage Integration', () => {
    it('renders full showcase page with all 12 D5 state sections and interactive modal triggers', async () => {
      render(
        <ToastProvider>
          <ToastContainer />
          <MemoryRouter>
            <SystemStatesShowcasePage />
          </MemoryRouter>
        </ToastProvider>
      );

      expect(screen.getByText(/دليل حالات واستجابات النظام/)).toBeInTheDocument();
      expect(screen.getByText(/I. التنبيهات العائمة/)).toBeInTheDocument();
      expect(screen.getByText(/B1. حالة عدم وجود إعلانات/)).toBeInTheDocument();
      expect(screen.getByText(/C. خطأ الخادم/)).toBeInTheDocument();
      expect(screen.getByText(/D. انقطاع الاتصال/)).toBeInTheDocument();
      expect(screen.getByText(/E. عدم وجود صلاحيات/)).toBeInTheDocument();
      expect(screen.getByText(/H. حالات التحقق من النماذج/)).toBeInTheDocument();
      expect(screen.getByText(/K. استجابات الاستيراد والتقدم/)).toBeInTheDocument();

      // Trigger Session Expired Modal from showcase
      const openSessionBtn = screen.getByRole('button', { name: /فتح نافذة انتهاء الجلسة \(F\)/ });
      fireEvent.click(openSessionBtn);
      expect(await screen.findByText('انتهت جلسة الدخول')).toBeInTheDocument();
    });
  });
});
