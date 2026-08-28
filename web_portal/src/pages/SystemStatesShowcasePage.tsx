import React, { useState } from 'react';
import {
  EmptyState,
  ServerErrorState,
  OfflineState,
  OfflineBanner,
  UnauthorizedState,
  SessionExpiredModal,
  HistoricalBlockedModal,
  ConfirmationModal,
  ProgressBar,
  ImportExportFeedback,
  SystemFeedbackStrip,
  PageSkeleton,
} from '../components/feedback';
import { Card, CardHeader, CardTitle, CardSubtitle, CardBody } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { useToast } from '../context';

export const SystemStatesShowcasePage: React.FC = () => {
  const toast = useToast();

  // Modals state
  const [showSessionModal, setShowSessionModal] = useState(false);
  const [showHistoricalModal, setShowHistoricalModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  // Import / Progress demo state
  const [importProgress, setImportProgress] = useState(65);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', paddingBottom: '3rem' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.375rem' }}>
          دليل حالات واستجابات النظام (W1-D5 System States & Feedback)
        </h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          لوحة استعراض واجهات حالات النظام، رسائل الخطأ، التنبيهات، وحالات التحميل وفق التصميم المعتمد.
        </p>
      </div>

      {/* L. System Feedback Token Strip */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>L. شريط رموز واستجابات النظام (System Feedback Token Strip)</CardTitle>
            <CardSubtitle>شارات الحالات، التنبيهات، والرموز المعيارية</CardSubtitle>
          </div>
        </CardHeader>
        <CardBody>
          <SystemFeedbackStrip />
        </CardBody>
      </Card>

      {/* I. Toast Notifications */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>I. التنبيهات العائمة (Toast Notifications)</CardTitle>
            <CardSubtitle>إشعارات النجاح، التحذير، الخطأ، والمعلومات</CardSubtitle>
          </div>
        </CardHeader>
        <CardBody>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <Button
              variant="primary"
              size="sm"
              onClick={() => toast.success('تم حفظ التغييرات بنجاح', 'عملية ناجحة')}
            >
              إشعار نجاح (Example 1)
            </Button>
            <Button
              variant="primary"
              size="sm"
              style={{ backgroundColor: 'var(--success-600)' }}
              onClick={() => toast.success('تم استيراد البيانات بنجاح', 'استيراد Excel')}
            >
              إشعار نجاح (Example 2)
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => toast.warning('يرجى التحقق من المدخلات قبل الحفظ', 'تنبيه')}
            >
              إشعار تحذير (Warning)
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => toast.error('تعذر إتمام العملية، يرجى المحاولة لاحقاً', 'خطأ في النظام')}
            >
              إشعار خطأ (Error)
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => toast.info('تم تحديث البيانات من الخادم', 'معلومات')}
            >
              إشعار معلومات (Info)
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* B. Empty States */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        <Card>
          <CardHeader>
            <CardTitle>B1. حالة عدم وجود إعلانات (No Announcements)</CardTitle>
          </CardHeader>
          <CardBody>
            <EmptyState
              variant="announcements"
              onAction={() => toast.info('فتح نموذج إنشاء إعلان جديد')}
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>B2. حالة تصفية فارغة (Filtered List Empty)</CardTitle>
          </CardHeader>
          <CardBody>
            <EmptyState
              variant="filtered"
              onSecondaryAction={() => toast.info('تمت إعادة تعيين الفلاتر')}
            />
          </CardBody>
        </Card>
      </div>

      {/* C & D. Server Error & Offline States */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
        <Card>
          <CardHeader>
            <CardTitle>C. خطأ الخادم (General Load / Server Error)</CardTitle>
          </CardHeader>
          <CardBody>
            <ServerErrorState
              onRetry={() => toast.info('جاري إعادة المحاولة...')}
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>D. انقطاع الاتصال (Connection / Offline State)</CardTitle>
          </CardHeader>
          <CardBody style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <OfflineBanner />
            <OfflineState
              onRetry={() => toast.info('جاري فحص الاتصال بالخادم...')}
            />
          </CardBody>
        </Card>
      </div>

      {/* E. Unauthorized / No Permission */}
      <Card>
        <CardHeader>
          <CardTitle>E. عدم وجود صلاحيات (Unauthorized / No Permission)</CardTitle>
        </CardHeader>
        <CardBody>
          <UnauthorizedState />
        </CardBody>
      </Card>

      {/* H. Form Validation States */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>H. حالات التحقق من النماذج (Form Validation State)</CardTitle>
            <CardSubtitle>الحقول الصحيحة، الخاطئة، ورسائل الخطأ الموضحة</CardSubtitle>
          </div>
        </CardHeader>
        <CardBody>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
            <Input
              label="اسم الطالب (حقل صحيح)"
              defaultValue="محمد عبدالله أحمد"
            />
            <Input
              label="اسم الطالب (مطلوب)"
              error="هذا الحقل مطلوب"
              placeholder="أدخل اسم الطالب..."
            />
            <Input
              label="رقم الجوال (تنسيق خاطئ)"
              defaultValue="05123"
              error="رقم الجوال غير صحيح"
            />
          </div>
        </CardBody>
      </Card>

      {/* K. Import / Export Feedback */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>K. استجابات الاستيراد والتقدم (Import / Export Feedback)</CardTitle>
            <CardSubtitle>أشرطة التقدم، تقارير النجاح، وجداول الأخطاء التفصيلية</CardSubtitle>
          </div>
        </CardHeader>
        <CardBody style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <h5 style={{ fontSize: '0.8125rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
              1. شريط تقدم الاستيراد والمعالجة
            </h5>
            <ProgressBar value={importProgress} label="جاري معالجة السجلات..." />
            <div style={{ marginTop: '0.75rem' }}>
              <ImportExportFeedback
                status="processing"
                progress={importProgress}
                statusText="جاري استيراد ومعالجة بيانات الطلاب..."
              />
            </div>
            <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
              <Button size="sm" variant="outline" onClick={() => setImportProgress(Math.max(10, importProgress - 15))}>
                -15%
              </Button>
              <Button size="sm" variant="outline" onClick={() => setImportProgress(Math.min(100, importProgress + 15))}>
                +15%
              </Button>
            </div>
          </div>

          <div>
            <h5 style={{ fontSize: '0.8125rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
              2. استجابة نجاح الاستيراد الكامل
            </h5>
            <ImportExportFeedback
              status="success"
              successCount={150}
              statusText="تم تجهيز ومعالجة ملف Excel بنجاح"
            />
          </div>

          <div>
            <h5 style={{ fontSize: '0.8125rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
              3. تقرير استيراد جزئي مع وجود أخطاء
            </h5>
            <ImportExportFeedback
              status="partial_error"
              successCount={121}
              errorCount={7}
              errors={[
                { rowNumber: 14, field: 'رقم الهوية', message: 'رقم الهوية مسجل مسبقاً لطالب آخر' },
                { rowNumber: 29, field: 'الصف الدراسي', message: 'الصف المحدد غير موجود في المدرسة' },
                { rowNumber: 43, field: 'رقم الجوال', message: 'صيغة رقم الجوال غير صحيحة' },
              ]}
              onRetry={() => toast.info('جاري إعادة المحاولة بعد التصحيح...')}
            />
          </div>
        </CardBody>
      </Card>

      {/* Modal Triggers (F, G, J) */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>F & G & J. النوافذ المنبثقة للنظام (System Modals)</CardTitle>
            <CardSubtitle>انتهاء الجلسة، الحظر التاريخي، وتأكيد الحذف</CardSubtitle>
          </div>
        </CardHeader>
        <CardBody>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <Button
              variant="outline"
              onClick={() => setShowSessionModal(true)}
            >
              فتح نافذة انتهاء الجلسة (F)
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowHistoricalModal(true)}
            >
              فتح نافذة الحظر التاريخي (G)
            </Button>
            <Button
              variant="danger"
              onClick={() => setShowConfirmModal(true)}
            >
              فتح نافذة تأكيد الحذف (J)
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* A. Skeletons */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>A. هياكل التحميل (Page & Card Skeletons)</CardTitle>
            <CardSubtitle>جاري تحميل البيانات...</CardSubtitle>
          </div>
        </CardHeader>
        <CardBody>
          <PageSkeleton />
        </CardBody>
      </Card>

      {/* Render Modals */}
      <SessionExpiredModal
        isOpen={showSessionModal}
        onClose={() => setShowSessionModal(false)}
      />

      <HistoricalBlockedModal
        isOpen={showHistoricalModal}
        onClose={() => setShowHistoricalModal(false)}
      />

      <ConfirmationModal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        onConfirm={() => {
          setShowConfirmModal(false);
          toast.success('تم حذف السجل بنجاح', 'تأكيد الحذف');
        }}
      />
    </div>
  );
};
