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
import { ExamsPage } from '../pages/ExamsPage';
import { Card, CardHeader, CardTitle, CardSubtitle, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Sparkles } from 'lucide-react';

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
        <Route
          path="/students/*"
          element={
            <ModulePlaceholder
              title="إدارة الطلاب (Students Management)"
              phase="Phase W5"
              description="سجلات الطلاب، التسجيل الأكاديمي، الفصول، وأولياء الأمور."
            />
          }
        />
        <Route
          path="/students"
          element={
            <ModulePlaceholder
              title="إدارة الطلاب (Students Management)"
              phase="Phase W5"
              description="سجلات الطلاب، التسجيل الأكاديمي، الفصول، وأولياء الأمور."
            />
          }
        />
        <Route
          path="/teachers/*"
          element={
            <ModulePlaceholder
              title="إدارة المعلمين (Teachers Management)"
              phase="Phase W5"
              description="ملفات المعلمين، التكليفات الأكاديمية، والأنصبة التدريسية."
            />
          }
        />
        <Route
          path="/teachers"
          element={
            <ModulePlaceholder
              title="إدارة المعلمين (Teachers Management)"
              phase="Phase W5"
              description="ملفات المعلمين، التكليفات الأكاديمية، والأنصبة التدريسية."
            />
          }
        />
        <Route path="/people" element={<Navigate to="/students" replace />} />

        {/* Academic routes */}
        <Route path="/academic-periods" element={<AcademicPeriodsPage />} />
        <Route path="/classes/*" element={<ClassesPage />} />
        <Route path="/classes" element={<ClassesPage />} />
        <Route path="/subjects/*" element={<SubjectsPage />} />
        <Route path="/subjects" element={<SubjectsPage />} />
        <Route path="/academic" element={<Navigate to="/classes" replace />} />

        {/* Timetable */}
        <Route
          path="/timetable/*"
          element={
            <ModulePlaceholder
              title="الجدول المدرسي (Timetable Admin)"
              phase="Phase W7"
              description="شبكة الحصص، التوزيع الأسبوعي، والتحقق الذري من التعارضات."
            />
          }
        />
        <Route
          path="/timetable"
          element={
            <ModulePlaceholder
              title="الجدول المدرسي (Timetable Admin)"
              phase="Phase W7"
              description="شبكة الحصص، التوزيع الأسبوعي، والتحقق الذري من التعارضات."
            />
          }
        />

        {/* Attendance */}
        <Route
          path="/attendance/*"
          element={
            <ModulePlaceholder
              title="الحضور والغياب (Daily Attendance)"
              phase="Phase W8"
              description="متابعة الحضور اليومي، رصد الغياب والتأخر، والتقارير المجمعة."
            />
          }
        />
        <Route
          path="/attendance"
          element={
            <ModulePlaceholder
              title="الحضور والغياب (Daily Attendance)"
              phase="Phase W8"
              description="متابعة الحضور اليومي، رصد الغياب والتأخر، والتقارير المجمعة."
            />
          }
        />

        {/* Homework */}
        <Route
          path="/homework/*"
          element={
            <ModulePlaceholder
              title="الواجبات المدرسية (Homework Management)"
              phase="Phase W9"
              description="متابعة الواجبات المنشورة، تسليمات الطلاب، ورصد الدرجات."
            />
          }
        />
        <Route
          path="/homework"
          element={
            <ModulePlaceholder
              title="الواجبات المدرسية (Homework Management)"
              phase="Phase W9"
              description="متابعة الواجبات المنشورة، تسليمات الطلاب، ورصد الدرجات."
            />
          }
        />

        {/* Exams */}
        <Route path="/exams/*" element={<ExamsPage />} />
        <Route path="/exams" element={<ExamsPage />} />

        {/* Communications */}
        <Route
          path="/messages/*"
          element={
            <ModulePlaceholder
              title="الرسائل والمحادثات (Messages)"
              phase="Phase W11"
              description="بريد الدعم (School Inbox)، والمحادثات الثنائية المباشرة."
            />
          }
        />
        <Route
          path="/messages"
          element={
            <ModulePlaceholder
              title="الرسائل والمحادثات (Messages)"
              phase="Phase W11"
              description="بريد الدعم (School Inbox)، والمحادثات الثنائية المباشرة."
            />
          }
        />
        <Route
          path="/announcements/*"
          element={
            <ModulePlaceholder
              title="الإعلانات والإشعارات (Announcements & Notifications)"
              phase="Phase W11"
              description="الإعلانات المدرسية الرسمية والتنبيهات الموجهة."
            />
          }
        />
        <Route
          path="/announcements"
          element={
            <ModulePlaceholder
              title="الإعلانات والإشعارات (Announcements & Notifications)"
              phase="Phase W11"
              description="الإعلانات المدرسية الرسمية والتنبيهات الموجهة."
            />
          }
        />
        <Route path="/communications" element={<Navigate to="/messages" replace />} />

        {/* Data Import / Export */}
        <Route
          path="/data/*"
          element={
            <ModulePlaceholder
              title="مركز البيانات والاستيراد (Import / Export Center)"
              phase="Phase W6"
              description="استيراد وتصدير بيانات الطلاب، الكوادر، والنتائج عبر ملفات Excel المعتمدة."
            />
          }
        />
        <Route
          path="/data"
          element={
            <ModulePlaceholder
              title="مركز البيانات والاستيراد (Import / Export Center)"
              phase="Phase W6"
              description="استيراد وتصدير بيانات الطلاب، الكوادر، والنتائج عبر ملفات Excel المعتمدة."
            />
          }
        />

        {/* Reports */}
        <Route
          path="/reports/*"
          element={
            <ModulePlaceholder
              title="التقارير والإحصائيات (Reports & Analytics)"
              phase="Phase W12"
              description="تقارير الأداء الأكاديمي، الحضور، عبء المعلمين، وتصدير PDF/Excel."
            />
          }
        />
        <Route
          path="/reports"
          element={
            <ModulePlaceholder
              title="التقارير والإحصائيات (Reports & Analytics)"
              phase="Phase W12"
              description="تقارير الأداء الأكاديمي، الحضور، عبء المعلمين، وتصدير PDF/Excel."
            />
          }
        />

        {/* Settings */}
        <Route
          path="/settings/*"
          element={
            <ModulePlaceholder
              title="إعدادات المدرسة والهوية (Settings & Branding)"
              phase="Phase W14"
              description="ملف المدرسة، الشعار، الألوان الرئيسية، والإعدادات الأكاديمية."
            />
          }
        />
        <Route
          path="/settings"
          element={
            <ModulePlaceholder
              title="إعدادات المدرسة والهوية (Settings & Branding)"
              phase="Phase W14"
              description="ملف المدرسة، الشعار، الألوان الرئيسية، والإعدادات الأكاديمية."
            />
          }
        />
      </Route>

      {/* 404 Fallback */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};
