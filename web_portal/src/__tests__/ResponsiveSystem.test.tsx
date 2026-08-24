import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import {
  ResponsiveTable,
  ResponsiveFilterBar,
  BreakpointTokenStrip,
} from '../components/ui';
import { AppShell } from '../components/layout/AppShell';
import { ResponsiveSystemShowcasePage } from '../pages/ResponsiveSystemShowcasePage';
import { ToastProvider } from '../context';
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

describe('W1-D6 Responsive System Test Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue(defaultAuthContextValue);
  });

  describe('E. Responsive Data Table', () => {
    interface TestItem {
      id: number;
      name: string;
      code: string;
    }

    const testData: TestItem[] = [
      { id: 1, name: 'سجل تجريبي 1', code: 'CODE-01' },
      { id: 2, name: 'سجل تجريبي 2', code: 'CODE-02' },
    ];

    it('renders desktop table headers and cells', () => {
      render(
        <ResponsiveTable
          columns={[
            { key: 'code', header: 'الرمز' },
            { key: 'name', header: 'الاسم' },
          ]}
          data={testData}
          keyExtractor={(item) => item.id}
        />
      );

      expect(screen.getByText('الرمز')).toBeInTheDocument();
      expect(screen.getByText('الاسم')).toBeInTheDocument();
      expect(screen.getByText('CODE-01')).toBeInTheDocument();
      expect(screen.getByText('سجل تجريبي 1')).toBeInTheDocument();
    });

    it('renders mobile card list when mobileCardRender is provided', () => {
      render(
        <ResponsiveTable
          columns={[
            { key: 'code', header: 'الرمز' },
            { key: 'name', header: 'الاسم' },
          ]}
          data={testData}
          keyExtractor={(item) => item.id}
          enableMobileCardView={true}
          mobileCardRender={(item) => (
            <div>
              <span>بطاقة الجوال: {item.name}</span>
            </div>
          )}
        />
      );

      expect(screen.getByText('بطاقة الجوال: سجل تجريبي 1')).toBeInTheDocument();
      expect(screen.getByText('بطاقة الجوال: سجل تجريبي 2')).toBeInTheDocument();
    });

    it('renders empty message when data is empty', () => {
      render(
        <ResponsiveTable
          columns={[{ key: 'name', header: 'الاسم' }]}
          data={[]}
          keyExtractor={(item) => (item as TestItem).id}
          emptyMessage="لا توجد عناصر مطابقة"
        />
      );

      expect(screen.getByText('لا توجد عناصر مطابقة')).toBeInTheDocument();
    });
  });

  describe('F. Search & Filter Adaptation', () => {
    it('renders search input, filter count, and triggers search & reset actions', () => {
      const onSearchChange = vi.fn();
      const onResetFilters = vi.fn();

      render(
        <ResponsiveFilterBar
          searchValue="أحمد"
          onSearchChange={onSearchChange}
          activeFilterCount={2}
          onResetFilters={onResetFilters}
          filtersContent={<select data-testid="test-filter"><option>الكل</option></select>}
        />
      );

      const searchInput = screen.getByRole('searchbox');
      expect(searchInput).toHaveValue('أحمد');

      fireEvent.change(searchInput, { target: { value: 'محمد' } });
      expect(onSearchChange).toHaveBeenCalledWith('محمد');

      const resetBtns = screen.getAllByRole('button', { name: /إعادة تعيين/ });
      expect(resetBtns.length).toBeGreaterThanOrEqual(1);
      fireEvent.click(resetBtns[0]);
      expect(onResetFilters).toHaveBeenCalledTimes(1);

      // Mobile filter toggle button
      const filterToggleBtn = screen.getByRole('button', { name: /الفلاتر \(2\)/ });
      expect(filterToggleBtn).toBeInTheDocument();
      fireEvent.click(filterToggleBtn);
    });
  });

  describe('L. Breakpoint Token Strip', () => {
    it('renders all 4 viewport tokens and triggers selection', () => {
      const onSelectBreakpoint = vi.fn();

      render(
        <BreakpointTokenStrip
          activeBreakpoint="tablet"
          onSelectBreakpoint={onSelectBreakpoint}
        />
      );

      expect(screen.getByText('Desktop (1440px+)')).toBeInTheDocument();
      expect(screen.getByText('Laptop (1024–1439px)')).toBeInTheDocument();
      expect(screen.getByText('Tablet (768–1023px)')).toBeInTheDocument();
      expect(screen.getByText('Mobile (360–767px)')).toBeInTheDocument();

      const mobileBtn = screen.getByRole('button', { name: /Mobile \(360–767px\)/ });
      fireEvent.click(mobileBtn);
      expect(onSelectBreakpoint).toHaveBeenCalledWith('mobile');
    });
  });

  describe('K. Mobile Off-Canvas Drawer Navigation', () => {
    it('toggles mobile drawer open and close via Topbar hamburger and backdrop', () => {
      render(
        <MemoryRouter>
          <AppShell />
        </MemoryRouter>
      );

      const hamburgerBtn = screen.getByRole('button', { name: /فتح القائمة الرئيسية/ });
      expect(hamburgerBtn).toBeInTheDocument();

      // Open drawer
      fireEvent.click(hamburgerBtn);

      const sidebar = screen.getByLabelText('القائمة الجانبية');
      expect(sidebar).toHaveClass('mobile-open');

      // Close drawer via close button
      const closeBtn = screen.getByLabelText('إغلاق القائمة الجانبية');
      expect(closeBtn).toBeInTheDocument();
      fireEvent.click(closeBtn);

      expect(sidebar).not.toHaveClass('mobile-open');
    });
  });

  describe('ResponsiveSystemShowcasePage Integration', () => {
    it('renders complete responsive showcase page with table, form, and filters', () => {
      render(
        <ToastProvider>
          <MemoryRouter>
            <ResponsiveSystemShowcasePage />
          </MemoryRouter>
        </ToastProvider>
      );

      expect(screen.getByText(/دليل النظام المتجاوب/)).toBeInTheDocument();
      expect(screen.getByText(/L. شريط أبعاد الشاشات وتصنيفات الأجهزة/)).toBeInTheDocument();
      expect(screen.getByText(/A - D. تكيف شبكة بطاقات المؤشرات/)).toBeInTheDocument();
      expect(screen.getByText(/E. استراتيجية الجداول المتجاوبة/)).toBeInTheDocument();
      expect(screen.getByText(/H. النماذج المتجاوبة/)).toBeInTheDocument();
      expect(screen.getByText(/J. التنبيه التاريخي المتجاوب/)).toBeInTheDocument();
      expect(screen.getByText(/K. تكيف القائمة الجانبية/)).toBeInTheDocument();
    });
  });
});
