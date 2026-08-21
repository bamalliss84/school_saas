import React from 'react';
import {
  Users,
  GraduationCap,
  ClipboardCheck,
  FileSpreadsheet,
  Calendar,
  MessageSquare,
  School,
  ShieldCheck,
  Clock,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../context';
import { Card, CardHeader, CardTitle, CardSubtitle, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export const DashboardPlaceholderPage: React.FC = () => {
  const { user, activeMembership, isHistorical, setShowContextModal } = useAuth();

  const metrics = [
    {
      title: 'الطلاب المسجلون',
      value: '—',
      subtext: 'متاح للربط في المرحلة W3',
      icon: Users,
      color: 'var(--primary-600)',
      bgColor: 'var(--primary-50)',
      phase: 'W3/W5',
    },
    {
      title: 'الكادر التعليمي',
      value: '—',
      subtext: 'متاح للربط في المرحلة W3',
      icon: GraduationCap,
      color: 'var(--indigo-600)',
      bgColor: 'var(--indigo-50)',
      phase: 'W3/W5',
    },
    {
      title: 'نسبة حضور اليوم',
      value: '— %',
      subtext: 'سجل الحضور اليومي الفعلي',
      icon: ClipboardCheck,
      color: 'var(--success-600)',
      bgColor: 'var(--success-50)',
      phase: 'W3/W8',
    },
    {
      title: 'نتائج بانتظار الاعتماد',
      value: '—',
      subtext: 'دورة اعتماد الاختبارات',
      icon: FileSpreadsheet,
      color: 'var(--warning-600)',
      bgColor: 'var(--warning-50)',
      phase: 'W3/W10',
    },
  ];

  const modules = [
    {
      title: 'إدارة الجدول المدرسي (Timetable)',
      desc: 'بناء الحصص الأسبوعية، توزيع المعلمين، والتحقق الذري من التعارضات.',
      phase: 'Phase W7',
      status: 'جاهز برمجياً في Backend (Sprint 4.7)',
      icon: Calendar,
    },
    {
      title: 'حضور وغياب الطلاب (Attendance)',
      desc: 'رصد الحضور اليومي، التقارير المجمعة، والتنبيهات المدرسية.',
      phase: 'Phase W8',
      status: 'جاهز برمجياً في Backend (Sprint 2)',
      icon: ClipboardCheck,
    },
    {
      title: 'الاختبارات والنتائج (Exams & Results)',
      desc: 'إدخال الدرجات، الاعتماد الإداري، النشر، وتقارير الكشوفات.',
      phase: 'Phase W10',
      status: 'جاهز برمجياً في Backend (Sprint 3.5)',
      icon: FileSpreadsheet,
    },
    {
      title: 'التواصل والرسائل (Communications)',
      desc: 'الإعلانات الرسمية، بريد المدرسة (Inbox)، والإشعارات الموجهة.',
      phase: 'Phase W11',
      status: 'جاهز برمجياً في Backend (Sprint 4B/4C)',
      icon: MessageSquare,
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {/* Page Header & Breadcrumbs (W1-D2) */}
      <div className="page-header-container">
        <h1 className="page-header-title">الرئيسية</h1>
        <div className="page-header-breadcrumbs">
          <span>الرئيسية</span>
          <span>/</span>
          <span>لوحة التحكم</span>
        </div>
      </div>

      {/* Welcome Banner Card */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.75rem',
          backgroundColor: 'var(--bg-surface)',
          padding: '0.75rem 1rem',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)',
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.02)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, var(--primary-600), var(--primary-800))',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <School size={18} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
              <h2 style={{ fontSize: '0.9375rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                مرحباً بك، {user?.full_name || user?.username || 'أحمد محمد'}
              </h2>
              <Badge variant="primary" icon={<ShieldCheck size={11} />}>
                بوابة إدارة المدرسة
              </Badge>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.0625rem' }}>
              السياق النشط: <strong>{activeMembership?.school?.name || 'مدرسة النور الأهلية'}</strong> •{' '}
              {activeMembership?.academic_year?.name || 'العام الدراسي 2026/2027'}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowContextModal(true)}
            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', height: '28px' }}
          >
            تبديل السياق
          </Button>
        </div>
      </div>

      {/* Historical Warning notice if applicable */}
      {isHistorical && (
        <div
          className="alert alert-warning"
          style={{
            padding: '0.625rem 0.875rem',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.75rem',
          }}
        >
          <Clock size={18} className="flex-shrink-0" />
          <div>
            <strong style={{ display: 'block', fontSize: '0.8125rem', marginBottom: '0.125rem' }}>
              أنت تتصفح بيانات في وضع الأرشيف (Historical Context)
            </strong>
            <span>
              جميع الإجراءات وعمليات التعديل والإدخال معطلة وفقاً لعقد الأمان السحابي. يمكنك قراءة السجلات فقط.
            </span>
          </div>
        </div>
      )}

      {/* KPI Metric Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
          gap: '0.75rem',
        }}
      >
        {metrics.map((m, idx) => {
          const Icon = m.icon;
          return (
            <Card key={idx} hoverable>
              <CardBody style={{ padding: '0.75rem 0.875rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '0.78125rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    {m.title}
                  </span>
                  <div
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: m.bgColor,
                      color: m.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Icon size={14} />
                  </div>
                </div>

                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.25rem 0 0.125rem 0' }}>
                  {m.value}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.6875rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>{m.subtext}</span>
                  <Badge variant="neutral">{m.phase}</Badge>
                </div>
              </CardBody>
            </Card>
          );
        })}
      </div>

      {/* Readiness & Roadmap Status */}
      <Card>
        <CardHeader style={{ padding: '0.75rem 1rem' }}>
          <div>
            <CardTitle style={{ fontSize: '0.9375rem' }}>خارطة طريق وحدات الإدارة المدرسية</CardTitle>
            <CardSubtitle style={{ fontSize: '0.75rem' }}>حالة التكامل البرمجي لوحدات بوابة الويب مع واجهات Backend</CardSubtitle>
          </div>
          <Badge variant="success" icon={<Sparkles size={11} />}>
            W1 Foundation مكتمل
          </Badge>
        </CardHeader>
        <CardBody style={{ padding: '0.75rem 1rem' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '0.625rem',
            }}
          >
            {modules.map((mod, idx) => {
              const Icon = mod.icon;
              return (
                <div
                  key={idx}
                  style={{
                    padding: '0.625rem 0.75rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: 'var(--neutral-50)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.375rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                      <div
                        style={{
                          width: '24px',
                          height: '24px',
                          borderRadius: 'var(--radius-xs)',
                          backgroundColor: 'var(--primary-100)',
                          color: 'var(--primary-700)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                        }}
                      >
                        <Icon size={13} />
                      </div>
                      <span style={{ fontWeight: 700, fontSize: '0.8125rem', color: 'var(--text-primary)' }}>
                        {mod.title}
                      </span>
                    </div>
                    <Badge variant="primary">{mod.phase}</Badge>
                  </div>

                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.35 }}>
                    {mod.desc}
                  </p>

                  <div style={{ marginTop: 'auto', paddingTop: '0.25rem', borderTop: '1px solid var(--border-subtle)', fontSize: '0.6875rem', color: 'var(--success-700)', fontWeight: 600 }}>
                    ✓ {mod.status}
                  </div>
                </div>
              );
            })}
          </div>
        </CardBody>
      </Card>
    </div>
  );
};
