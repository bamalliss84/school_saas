import React, { lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import { ContextSelectionPage } from '../pages/ContextSelectionPage';
import { UnauthorizedPage } from '../pages/UnauthorizedPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { AppShell } from '../components/layout/AppShell';
import { AuthGuard } from './AuthGuard';
import { SchoolAdminGuard } from './SchoolAdminGuard';
import { ContextGuard } from './ContextGuard';
import { ForgotPasswordPage, ResetPasswordPage } from '../pages/PasswordResetPages';
import { PrivacyPage, TermsPage } from '../pages/LegalPages';

// Shell pages are split per route; AppShell wraps the outlet in Suspense.
const DashboardPage = lazy(() => import('../pages/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const SystemStatesShowcasePage = lazy(() => import('../pages/SystemStatesShowcasePage').then((m) => ({ default: m.SystemStatesShowcasePage })));
const ResponsiveSystemShowcasePage = lazy(() => import('../pages/ResponsiveSystemShowcasePage').then((m) => ({ default: m.ResponsiveSystemShowcasePage })));
const ClassesPage = lazy(() => import('../pages/ClassesPage').then((m) => ({ default: m.ClassesPage })));
const SubjectsPage = lazy(() => import('../pages/SubjectsPage').then((m) => ({ default: m.SubjectsPage })));
const AcademicPeriodsPage = lazy(() => import('../pages/AcademicPeriodsPage').then((m) => ({ default: m.AcademicPeriodsPage })));
const StudentsPage = lazy(() => import('../pages/StudentsPage').then((m) => ({ default: m.StudentsPage })));
const TeachersPage = lazy(() => import('../pages/TeachersPage').then((m) => ({ default: m.TeachersPage })));
const ParentsPage = lazy(() => import('../pages/ParentsPage').then((m) => ({ default: m.ParentsPage })));
const ExamsPage = lazy(() => import('../pages/ExamsPage').then((m) => ({ default: m.ExamsPage })));
const OperationsPage = lazy(() => import('../pages/OperationsPage').then((m) => ({ default: m.OperationsPage })));
const FeesPage = lazy(() => import('../pages/FeesPage').then((m) => ({ default: m.FeesPage })));
const SubscriptionPage = lazy(() => import('../pages/SubscriptionPage').then((m) => ({ default: m.SubscriptionPage })));
const PlatformPage = lazy(() => import('../pages/PlatformPage').then((m) => ({ default: m.PlatformPage })));
const ChangePasswordPage = lazy(() => import('../pages/ChangePasswordPage').then((m) => ({ default: m.ChangePasswordPage })));

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />

      {/* Protected Context Selection */}
      <Route
        path="/select-context"
        element={
          <AuthGuard>
            <SchoolAdminGuard>
              <ContextSelectionPage />
            </SchoolAdminGuard>
          </AuthGuard>
        }
      />

      {/* Protected Admin Shell routes */}
      <Route
        element={
          <AuthGuard>
            <SchoolAdminGuard>
              <ContextGuard>
                <AppShell />
              </ContextGuard>
            </SchoolAdminGuard>
          </AuthGuard>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard/*" element={<DashboardPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/system-states" element={<SystemStatesShowcasePage />} />
        <Route path="/responsive-system" element={<ResponsiveSystemShowcasePage />} />

        {/* People routes */}
        <Route path="/students/*" element={<StudentsPage />} />
        <Route path="/students" element={<StudentsPage />} />
        <Route path="/teachers/*" element={<TeachersPage />} />
        <Route path="/teachers" element={<TeachersPage />} />
        <Route path="/parents/*" element={<ParentsPage />} />
        <Route path="/parents" element={<ParentsPage />} />
        <Route path="/people" element={<Navigate to="/students" replace />} />

        {/* Academic routes */}
        <Route path="/academic-periods" element={<AcademicPeriodsPage />} />
        <Route path="/classes/*" element={<ClassesPage />} />
        <Route path="/classes" element={<ClassesPage />} />
        <Route path="/subjects/*" element={<SubjectsPage />} />
        <Route path="/subjects" element={<SubjectsPage />} />
        <Route path="/academic" element={<Navigate to="/classes" replace />} />

        {/* Timetable */}
        <Route path="/timetable/*" element={<OperationsPage module="timetable" />} />

        {/* Attendance */}
        <Route path="/attendance/*" element={<OperationsPage module="attendance" />} />

        {/* Homework */}
        <Route path="/homework/*" element={<OperationsPage module="homework" />} />

        {/* Exams */}
        <Route path="/exams/*" element={<ExamsPage />} />
        <Route path="/exams" element={<ExamsPage />} />

        {/* Communications */}
        <Route path="/messages/*" element={<OperationsPage module="messages" />} />
        <Route path="/announcements/*" element={<OperationsPage module="announcements" />} />
        <Route path="/communications" element={<Navigate to="/messages" replace />} />

        {/* Data Import / Export */}
        <Route path="/data/*" element={<OperationsPage module="data" />} />
        <Route path="/onboarding/*" element={<OperationsPage module="onboarding" />} />

        {/* Reports */}
        <Route path="/reports/*" element={<OperationsPage module="reports" />} />

        {/* Settings */}
        <Route path="/settings/*" element={<OperationsPage module="settings" />} />

        {/* Release 1.1 billing */}
        <Route path="/fees/*" element={<FeesPage />} />
        <Route path="/subscription" element={<SubscriptionPage />} />
        <Route path="/platform" element={<PlatformPage />} />
        <Route path="/account/password" element={<ChangePasswordPage />} />
      </Route>

      {/* 404 Fallback */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};
