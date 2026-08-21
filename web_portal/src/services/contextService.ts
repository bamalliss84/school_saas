import { apiClient, setActiveMembershipId } from './apiClient';
import { ContextListResponse, SchoolMembership } from '../types/context';

export const contextService = {
  getContexts: async (): Promise<ContextListResponse> => {
    return apiClient.get<ContextListResponse>('/auth/contexts/', {
      skipContext: true,
    });
  },

  getCurrentContext: async (): Promise<SchoolMembership | null> => {
    return apiClient.get<SchoolMembership | null>('/auth/context/');
  },

  setDefaultContext: async (membershipId: number): Promise<SchoolMembership> => {
    const data = await apiClient.post<SchoolMembership>(
      '/auth/context/default/',
      { membership_id: membershipId },
      { skipContext: true }
    );
    setActiveMembershipId(membershipId);
    return data;
  },
};
