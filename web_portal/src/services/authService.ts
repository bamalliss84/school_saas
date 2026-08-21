import { apiClient, setAuthTokens, setActiveMembershipId } from './apiClient';
import { LoginCredentials, LoginResponse, User } from '../types/auth';

export const authService = {
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const data = await apiClient.post<LoginResponse>('/auth/login/', credentials, {
      skipContext: true,
    });
    setAuthTokens(data.access, data.refresh);
    if (data.default_membership_id) {
      setActiveMembershipId(data.default_membership_id);
    }
    return data;
  },

  logout: async (refreshToken?: string): Promise<void> => {
    const refresh = refreshToken || localStorage.getItem('refresh_token');
    try {
      if (refresh) {
        await apiClient.post('/auth/logout/', { refresh }, { skipContext: true });
      }
    } catch {
      // Ignore logout backend errors and proceed to local clearance
    } finally {
      setAuthTokens(null, null);
      setActiveMembershipId(null);
    }
  },

  getMe: async (): Promise<User> => {
    return apiClient.get<User>('/auth/me/');
  },
};
