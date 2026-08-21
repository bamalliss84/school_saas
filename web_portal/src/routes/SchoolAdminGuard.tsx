import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context';
import { LoadingSpinner } from '../components/feedback/LoadingSpinner';

export const SchoolAdminGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isSchoolAdmin, isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return <LoadingSpinner fullPage text="التحقق من صلاحيات المدير..." />;
  }

  if (isAuthenticated && !isSchoolAdmin) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
};
