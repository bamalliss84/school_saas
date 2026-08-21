import React, { useState, useEffect, useCallback } from 'react';
import { User, LoginCredentials, LoginResponse } from '../types/auth';
import { SchoolMembership, ContextListResponse } from '../types/context';
import { authService } from '../services/authService';
import { contextService } from '../services/contextService';
import {
  setAuthTokens,
  setActiveMembershipId,
  getActiveMembershipId,
  setOnUnauthorized,
  setOnContextRequired,
} from '../services/apiClient';
import { AuthContext } from './authContextDef';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [activeMembership, setActiveMembership] = useState<SchoolMembership | null>(null);
  const [allMemberships, setAllMemberships] = useState<SchoolMembership[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [showContextModal, setShowContextModal] = useState<boolean>(false);

  const isAuthenticated = Boolean(user && localStorage.getItem('access_token'));

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setActiveMembership(null);
      setAllMemberships([]);
      setAuthTokens(null, null);
      setActiveMembershipId(null);
    }
  }, []);

  const loadContextsAndUser = useCallback(async () => {
    try {
      const contextsData: ContextListResponse = await contextService.getContexts();
      setAllMemberships(contextsData.contexts || []);

      const savedMembershipId = getActiveMembershipId();
      let resolved: SchoolMembership | null = null;

      if (savedMembershipId) {
        resolved = contextsData.contexts.find((m) => m.membership_id === savedMembershipId) || null;
      }

      if (!resolved && contextsData.current_context) {
        resolved = contextsData.current_context;
        setActiveMembershipId(resolved.membership_id);
      }

      if (!resolved && contextsData.contexts.length === 1) {
        resolved = contextsData.contexts[0];
        setActiveMembershipId(resolved.membership_id);
      }

      setActiveMembership(resolved);

      const userData = await authService.getMe();
      setUser(userData);

      // If user has multiple active memberships and none is selected, trigger context selection
      const activeContexts = contextsData.contexts.filter((c) => c.status === 'active');
      if (activeContexts.length > 1 && !savedMembershipId && !resolved) {
        setShowContextModal(true);
      }
    } catch {
      await logout();
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    setOnUnauthorized(() => {
      logout();
    });

    setOnContextRequired(() => {
      setShowContextModal(true);
    });

    const token = localStorage.getItem('access_token');
    if (token) {
      loadContextsAndUser();
    } else {
      setIsLoading(false);
    }
  }, [loadContextsAndUser, logout]);

  const login = async (credentials: LoginCredentials): Promise<LoginResponse> => {
    setIsLoading(true);
    try {
      const res = await authService.login(credentials);
      setAuthTokens(res.access, res.refresh);
      setUser(res.user);

      // Load full contexts
      const contextsData = await contextService.getContexts();
      setAllMemberships(contextsData.contexts || []);

      let selectedContext = contextsData.current_context;
      if (!selectedContext && res.default_membership_id) {
        selectedContext = contextsData.contexts.find(
          (m) => m.membership_id === res.default_membership_id
        ) || null;
      }
      if (!selectedContext && contextsData.contexts.length === 1) {
        selectedContext = contextsData.contexts[0];
      }

      if (selectedContext) {
        setActiveMembership(selectedContext);
        setActiveMembershipId(selectedContext.membership_id);
      } else if (res.has_multiple_contexts) {
        setShowContextModal(true);
      }

      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const switchContext = async (membership: SchoolMembership, makeDefault = false) => {
    setActiveMembership(membership);
    setActiveMembershipId(membership.membership_id);

    if (makeDefault && membership.status === 'active') {
      try {
        await contextService.setDefaultContext(membership.membership_id);
      } catch (err) {
        console.error('Failed to set default context:', err);
      }
    }

    // Refresh current user and contexts
    await refreshContexts();
  };

  const refreshContexts = async () => {
    try {
      const contextsData = await contextService.getContexts();
      setAllMemberships(contextsData.contexts || []);

      const currentId = getActiveMembershipId();
      if (currentId) {
        const found = contextsData.contexts.find((m) => m.membership_id === currentId);
        if (found) {
          setActiveMembership(found);
        }
      }
      const updatedUser = await authService.getMe();
      setUser(updatedUser);
    } catch (err) {
      console.error('Error refreshing contexts:', err);
    }
  };

  const isHistorical = Boolean(
    activeMembership?.status === 'historical' ||
    activeMembership?.access_mode === 'read_only'
  );

  const isReadOnly = Boolean(
    isHistorical ||
    activeMembership?.can_write === false
  );

  // Role checks for School Admin
  const isSchoolAdmin = Boolean(
    user?.role === 'school_admin' ||
    user?.role === 'super_admin' ||
    activeMembership?.role === 'school_admin' ||
    activeMembership?.role === 'super_admin'
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        activeMembership,
        allMemberships,
        isHistorical,
        isReadOnly,
        isSchoolAdmin,
        showContextModal,
        login,
        logout,
        switchContext,
        refreshContexts,
        setShowContextModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
