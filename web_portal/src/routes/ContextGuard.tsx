import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context';
import { LoadingSpinner } from '../components/feedback/LoadingSpinner';

export const ContextGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { activeMembership, allMemberships, isLoading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner fullPage text="تحميل سياق المدرسة..." />;
  }

  if (isAuthenticated && allMemberships.length > 1 && !activeMembership && location.pathname !== '/select-context') {
    return <Navigate to="/select-context" replace />;
  }

  return <>{children}</>;
};
