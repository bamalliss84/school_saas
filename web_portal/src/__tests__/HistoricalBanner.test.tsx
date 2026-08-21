import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HistoricalBanner } from '../components/layout/HistoricalBanner';
import * as UseAuthModule from '../context/useAuth';

describe('HistoricalBanner', () => {
  it('renders nothing when active context is NOT historical', () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: true,
      isLoading: false,
      activeMembership: {
        membership_id: 1,
        school: { id: 1, name: 'مدرسة النور الأهلية' },
        role: 'school_admin',
        status: 'active',
        access_mode: 'read_write',
        is_default: true,
        is_current_school: true,
        academic_year: { id: 1, name: '2026-2027' },
        can_write: true,
        start_date: '2026-09-01',
        end_date: null,
        last_used_at: null,
        unread_notifications_count: 0,
        unread_conversations_count: 0,
      },
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

    const { container } = render(<HistoricalBanner />);
    expect(container.firstChild).toBeNull();
  });

  it('renders warning banner when active context is historical (read_only)', () => {
    vi.spyOn(UseAuthModule, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: true,
      isLoading: false,
      activeMembership: {
        membership_id: 2,
        school: { id: 2, name: 'مدرسة الأمل القديمة' },
        role: 'school_admin',
        status: 'historical',
        access_mode: 'read_only',
        is_default: false,
        is_current_school: false,
        academic_year: { id: 2, name: '2024-2025' },
        can_write: false,
        start_date: '2024-09-01',
        end_date: '2025-06-30',
        last_used_at: null,
        unread_notifications_count: 0,
        unread_conversations_count: 0,
      },
      allMemberships: [],
      isHistorical: true,
      isReadOnly: true,
      isSchoolAdmin: true,
      showContextModal: false,
      login: vi.fn(),
      logout: vi.fn(),
      switchContext: vi.fn(),
      refreshContexts: vi.fn(),
      setShowContextModal: vi.fn(),
    });

    render(<HistoricalBanner />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText(/أنت تستعرض عامًا دراسيًا سابقًا — البيانات للعرض فقط/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /تغيير السياق/i })).toBeInTheDocument();
  });
});
