import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../context';
import { authService } from '../services/authService';
import { contextService } from '../services/contextService';

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('provides initial unauthenticated state', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.activeMembership).toBeNull();
    expect(result.current.isHistorical).toBe(false);
    expect(result.current.isSchoolAdmin).toBe(false);
  });

  it('identifies school_admin as authorized for portal', async () => {
    const mockUser = {
      id: 1,
      username: 'admin_test',
      full_name: 'مدير المدرسة',
      email: 'admin@school.com',
      role: 'school_admin' as const,
    };

    const mockMembership = {
      membership_id: 10,
      school: { id: 1, name: 'مدرسة النور' },
      role: 'school_admin' as const,
      status: 'active' as const,
      access_mode: 'read_write' as const,
      is_default: true,
      is_current_school: true,
      academic_year: { id: 1, name: '2026-2027' },
      can_write: true,
      start_date: '2026-09-01',
      end_date: null,
      last_used_at: null,
      unread_notifications_count: 0,
      unread_conversations_count: 0,
    };

    vi.spyOn(authService, 'login').mockResolvedValue({
      access: 'mock-access',
      refresh: 'mock-refresh',
      user: mockUser,
      contexts_count: 1,
      has_multiple_contexts: false,
      default_membership_id: 10,
    });

    vi.spyOn(contextService, 'getContexts').mockResolvedValue({
      current_context: mockMembership,
      contexts: [mockMembership],
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({ username: 'admin_test', password: 'password' });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.role).toBe('school_admin');
    expect(result.current.isSchoolAdmin).toBe(true);
    expect(result.current.isHistorical).toBe(false);
    expect(result.current.isReadOnly).toBe(false);
  });

  it('correctly marks historical memberships as isHistorical and isReadOnly', async () => {
    const mockUser = {
      id: 2,
      username: 'admin_historical',
      full_name: 'مدير مدرسة أرشيف',
      email: 'admin@school.com',
      role: 'school_admin' as const,
    };

    const mockHistoricalMembership = {
      membership_id: 15,
      school: { id: 2, name: 'مدرسة الأمل السابقة' },
      role: 'school_admin' as const,
      status: 'historical' as const,
      access_mode: 'read_only' as const,
      is_default: false,
      is_current_school: false,
      academic_year: { id: 2, name: '2025-2026' },
      can_write: false,
      start_date: '2025-09-01',
      end_date: '2026-06-30',
      last_used_at: null,
      unread_notifications_count: 0,
      unread_conversations_count: 0,
    };

    vi.spyOn(authService, 'login').mockResolvedValue({
      access: 'mock-access',
      refresh: 'mock-refresh',
      user: mockUser,
      contexts_count: 1,
      has_multiple_contexts: false,
      default_membership_id: 15,
    });

    vi.spyOn(contextService, 'getContexts').mockResolvedValue({
      current_context: mockHistoricalMembership,
      contexts: [mockHistoricalMembership],
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({ username: 'admin_historical', password: 'password' });
    });

    expect(result.current.isHistorical).toBe(true);
    expect(result.current.isReadOnly).toBe(true);
  });

  it('blocks non-admin roles from isSchoolAdmin flag', async () => {
    const mockTeacher = {
      id: 3,
      username: 'teacher_test',
      full_name: 'المعلم أحمد',
      email: 'teacher@school.com',
      role: 'teacher' as const,
    };

    const mockTeacherMembership = {
      membership_id: 20,
      school: { id: 1, name: 'مدرسة النور' },
      role: 'teacher' as const,
      status: 'active' as const,
      access_mode: 'read_write' as const,
      is_default: true,
      is_current_school: true,
      academic_year: { id: 1, name: '2026-2027' },
      can_write: true,
      start_date: '2026-09-01',
      end_date: null,
      last_used_at: null,
      unread_notifications_count: 0,
      unread_conversations_count: 0,
    };

    vi.spyOn(authService, 'login').mockResolvedValue({
      access: 'mock-access',
      refresh: 'mock-refresh',
      user: mockTeacher,
      contexts_count: 1,
      has_multiple_contexts: false,
      default_membership_id: 20,
    });

    vi.spyOn(contextService, 'getContexts').mockResolvedValue({
      current_context: mockTeacherMembership,
      contexts: [mockTeacherMembership],
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({ username: 'teacher_test', password: 'password' });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.isSchoolAdmin).toBe(false);
  });
});
