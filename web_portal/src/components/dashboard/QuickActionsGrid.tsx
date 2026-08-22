import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UserPlus,
  GraduationCap,
  ClipboardCheck,
  Megaphone,
  FileSpreadsheet,
  FileDown,
  UploadCloud,
  FileUp,
  Lock,
  Zap,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useAuth } from '../../context';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface QuickActionItem {
  id: string;
  label: string;
  sublabel: string;
  icon: React.ElementType;
  route: string;
  variant: 'default' | 'primary' | 'excel-green' | 'excel-dark';
  requiresWritable: boolean;
}

export const QuickActionsGrid: React.FC = () => {
  const navigate = useNavigate();
  const { isHistorical, isReadOnly } = useAuth();
  const isLocked = isHistorical || isReadOnly;
  const [showSecondary, setShowSecondary] = useState<boolean>(false);

  // 4 Promoted Primary High-Frequency Actions (Section 10)
  const primaryActions: QuickActionItem[] = [
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
  ];

  // Secondary Operations (Under "المزيد من الإجراءات")
  const secondaryActions: QuickActionItem[] = [
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
      label: 'استيراد بيانات الطلاب',
      sublabel: 'ملف Excel',
      icon: UploadCloud,
      route: '/data',
      variant: 'excel-green',
      requiresWritable: true,
    },
    {
      id: 'import_general_excel',
      label: 'استيراد المركز العام',
      sublabel: 'بيانات مجمعة',
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
              مقيدة في الأرشيف
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardBody style={{ padding: '0.75rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {/* 4 Promoted Primary Action Tiles (Section 10) */}
        <div className="quick-actions-primary-grid">
          {primaryActions.map((action) => {
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

        {/* Secondary Operations Group (المزيد من الإجراءات) */}
        <div className="quick-actions-secondary-container">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSecondary(!showSecondary)}
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              padding: '0.375rem 0.5rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px dashed var(--border-subtle)',
            }}
          >
            <span style={{ fontWeight: 600 }}>المزيد من الإجراءات والعمليات</span>
            {showSecondary ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </Button>

          {showSecondary && (
            <div className="quick-actions-secondary-grid" style={{ marginTop: '0.5rem' }}>
              {secondaryActions.map((action) => {
                const Icon = action.icon;
                const disabled = isLocked && action.requiresWritable;

                return (
                  <button
                    key={action.id}
                    type="button"
                    className={`quick-action-tile secondary ${action.variant} ${disabled ? 'disabled' : ''}`}
                    disabled={disabled}
                    onClick={() => !disabled && navigate(action.route)}
                    title={disabled ? 'هذا الإجراء معطل في وضع الأرشيف (Historical Context)' : action.label}
                  >
                    <div className="quick-action-icon-wrap">
                      <Icon size={16} />
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
          )}
        </div>
      </CardBody>
    </Card>
  );
};
