import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UserPlus,
  GraduationCap,
  ClipboardCheck,
  Megaphone,
  FileSpreadsheet,
  FileDown,
  FileUp,
  UploadCloud,
  Lock,
  Zap,
} from 'lucide-react';
import { useAuth } from '../../context';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface QuickActionItem {
  id: string;
  label: string;
  sublabel: string;
  icon: React.ElementType;
  route: string;
  variant: 'default' | 'excel-green' | 'excel-dark';
  requiresWritable: boolean;
}

export const QuickActionsGrid: React.FC = () => {
  const navigate = useNavigate();
  const { isHistorical, isReadOnly } = useAuth();
  const isLocked = isHistorical || isReadOnly;

  const actions: QuickActionItem[] = [
    {
      id: 'add_student',
      label: 'إضافة طالب',
      sublabel: 'تسجيل جديد',
      icon: UserPlus,
      route: '/students',
      variant: 'default',
      requiresWritable: true,
    },
    {
      id: 'add_teacher',
      label: 'إضافة معلم',
      sublabel: 'ملف وتكليف',
      icon: GraduationCap,
      route: '/teachers',
      variant: 'default',
      requiresWritable: true,
    },
    {
      id: 'review_attendance',
      label: 'مراجعة الحضور',
      sublabel: 'السجل اليومي',
      icon: ClipboardCheck,
      route: '/attendance',
      variant: 'default',
      requiresWritable: false,
    },
    {
      id: 'create_announcement',
      label: 'إنشاء إعلان',
      sublabel: 'نشر وتوجيه',
      icon: Megaphone,
      route: '/announcements',
      variant: 'default',
      requiresWritable: true,
    },
    {
      id: 'create_exam',
      label: 'إنشاء إختبار',
      sublabel: 'جدولة ورصد',
      icon: FileSpreadsheet,
      route: '/exams',
      variant: 'default',
      requiresWritable: true,
    },
    {
      id: 'export_excel',
      label: 'تصدير Excel',
      sublabel: 'سجلات وكشوفات',
      icon: FileDown,
      route: '/data',
      variant: 'excel-green',
      requiresWritable: false,
    },
    {
      id: 'import_students_excel',
      label: 'استيراد Excel',
      sublabel: 'بيانات الطلاب',
      icon: UploadCloud,
      route: '/data',
      variant: 'excel-green',
      requiresWritable: true,
    },
    {
      id: 'import_general_excel',
      label: 'استيراد Excel',
      sublabel: 'المركز العام',
      icon: FileUp,
      route: '/data',
      variant: 'excel-dark',
      requiresWritable: true,
    },
  ];

  return (
    <Card className="dashboard-operational-card">
      <CardHeader style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--primary-50)',
                color: 'var(--primary-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Zap size={16} />
            </div>
            <CardTitle style={{ fontSize: '0.9375rem', fontWeight: 800 }}>إجراءات سريعة</CardTitle>
          </div>

          {isLocked && (
            <Badge variant="warning" icon={<Lock size={11} />}>
              العمليات مقيدة في وضع الأرشيف
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardBody style={{ padding: '0.75rem 1rem' }}>
        <div className="quick-actions-grid">
          {actions.map((action) => {
            const Icon = action.icon;
            const disabled = isLocked && action.requiresWritable;

            return (
              <button
                key={action.id}
                type="button"
                className={`quick-action-tile ${action.variant} ${disabled ? 'disabled' : ''}`}
                disabled={disabled}
                onClick={() => !disabled && navigate(action.route)}
                title={disabled ? 'هذا الإجراء معطل في وضع الأرشيف (Historical Context)' : action.label}
              >
                <div className="quick-action-icon-wrap">
                  <Icon size={18} />
                  {disabled && (
                    <span className="quick-action-lock-badge">
                      <Lock size={10} />
                    </span>
                  )}
                </div>

                <div className="quick-action-text-wrap">
                  <span className="quick-action-label">{action.label}</span>
                  <span className="quick-action-sublabel">{action.sublabel}</span>
                </div>
              </button>
            );
          })}
        </div>
      </CardBody>
    </Card>
  );
};
