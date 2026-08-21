import { createContext } from 'react';
import { User, LoginCredentials, LoginResponse } from '../types/auth';
import { SchoolMembership } from '../types/context';

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  activeMembership: SchoolMembership | null;
  allMemberships: SchoolMembership[];
  isHistorical: boolean;
  isReadOnly: boolean;
  isSchoolAdmin: boolean;
  showContextModal: boolean;
  login: (credentials: LoginCredentials) => Promise<LoginResponse>;
  logout: () => Promise<void>;
  switchContext: (membership: SchoolMembership, makeDefault?: boolean) => Promise<void>;
  refreshContexts: () => Promise<void>;
  setShowContextModal: (show: boolean) => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
