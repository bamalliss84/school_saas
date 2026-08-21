import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context';
import { LoadingSpinner } from '../components/feedback/LoadingSpinner';

export const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner fullPage text="التحقق من جلسة المستخدم..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
