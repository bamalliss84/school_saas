import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import { ContextSelectionPage } from '../pages/ContextSelectionPage';
import { DashboardPage } from '../pages/DashboardPage';
import { SystemStatesShowcasePage } from '../pages/SystemStatesShowcasePage';
import { ResponsiveSystemShowcasePage } from '../pages/ResponsiveSystemShowcasePage';
import { UnauthorizedPage } from '../pages/UnauthorizedPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { AppShell } from '../components/layout/AppShell';
import { AuthGuard } from './AuthGuard';
import { SchoolAdminGuard } from './SchoolAdminGuard';
import { ContextGuard } from './ContextGuard';
import { ClassesPage } from '../pages/ClassesPage';
import { SubjectsPage } from '../pages/SubjectsPage';
import { AcademicPeriodsPage } from '../pages/AcademicPeriodsPage';
import { StudentsPage } from '../pages/StudentsPage';
import { TeachersPage } from '../pages/TeachersPage';
import { ParentsPage } from '../pages/ParentsPage';
import { ExamsPage } from '../pages/ExamsPage';
import { Card, CardHeader, CardTitle, CardSubtitle, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Sparkles } from 'lucide-react';
import { OperationsPage } from '../pages/OperationsPage';

const ModulePlaceholder: React.FC<{ title: string; phase: string; description: string }> = ({
  title,
  phase,
  description,
}) => (
  <Card>
    <CardHeader>
      <div>
        <CardTitle>{title}</CardTitle>
        <CardSubtitle>{description}</CardSubtitle>
      </div>
      <Badge variant="primary" icon={<Sparkles size={12} />}>{phase}</Badge>
    </CardHeader>
    <CardBody>
      <div
        style={{
          padding: '2.5rem 1.5rem',
          textAlign: 'center',
          backgroundColor: 'var(--neutral-50)',
          borderRadius: 'var(--radius-lg)',
          border: '1px dashed var(--border-strong)',
        }}
      >
        <h4 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          هذه الوحدة مخصصة للتطوير في المرحلة ({phase})
        </h4>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', maxWidth: '520px', margin: '0 auto' }}>
          نظام الأساس (W1) جاهز بالكامل من حيث المصادقة وتحديد سياق المدرسة. سيتم بناء واجهات هذه الوحدة فور اعتماد التصاميم المرئية (Nano Boards) واستكمال المرحلة الحالية.
        </p>
      </div>
    </CardBody>
  </Card>
);

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />

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
      </Route>

      {/* 404 Fallback */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};
