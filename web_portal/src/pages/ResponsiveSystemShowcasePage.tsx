import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardSubtitle,
  CardBody,
  Button,
  Input,
  Badge,
  ResponsiveTable,
  ResponsiveFilterBar,
  BreakpointTokenStrip,
} from '../components/ui';
import {
  FileSpreadsheet,
  Download,
  Plus,
  Edit2,
  Trash2,
  Clock,
  Menu,
} from 'lucide-react';
import { useToast } from '../context';

interface DemoStudent {
  id: number;
  national_id: string;
  name: string;
  grade_section: string;
  phone: string;
  status: 'active' | 'absent' | 'late';
}

const mockStudents: DemoStudent[] = [
  { id: 1, national_id: '1029384756', name: 'محمد عبد الله أحمد', grade_section: 'الصف العاشر / 1', phone: '0501234567', status: 'active' },
  { id: 2, national_id: '1092837465', name: 'عمر خالد السعيد', grade_section: 'الصف العاشر / 2', phone: '0509876543', status: 'active' },
  { id: 3, national_id: '1056473829', name: 'سارة يوسف النور', grade_section: 'الصف التاسع / 1', phone: '0551122334', status: 'absent' },
  { id: 4, national_id: '1047586930', name: 'عبد الرحمن فهد المهيدب', grade_section: 'الصف التاسع / 2', phone: '0562233445', status: 'late' },
];

export const ResponsiveSystemShowcasePage: React.FC = () => {
  const toast = useToast();
  const [activeBreakpoint, setActiveBreakpoint] = useState<'desktop' | 'laptop' | 'tablet' | 'mobile'>('desktop');
  const [searchValue, setSearchValue] = useState('');
  const [selectedGrade, setSelectedGrade] = useState('');
  const [enableMobileCardView, setEnableMobileCardView] = useState(true);

  const filteredStudents = mockStudents.filter((s) => {
    const matchesSearch = s.name.includes(searchValue) || s.national_id.includes(searchValue);
    const matchesGrade = !selectedGrade || s.grade_section.includes(selectedGrade);
    return matchesSearch && matchesGrade;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', paddingBottom: '3rem' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.375rem' }}>
          دليل النظام المتجاوب (W1-D6 Responsive System)
        </h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          استعراض السلوك التكيفي للأجهزة المختلفة (Desktop, Laptop, Tablet, Mobile) وفق التصميم المعتمد.
        </p>
      </div>

      {/* L. Breakpoint Token Strip */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>L. شريط أبعاد الشاشات وتصنيفات الأجهزة (Breakpoint Token Strip)</CardTitle>
            <CardSubtitle>الأبعاد المعيارية لنظام التجاوب في المنصة</CardSubtitle>
          </div>
        </CardHeader>
        <CardBody>
          <BreakpointTokenStrip
            activeBreakpoint={activeBreakpoint}
            onSelectBreakpoint={setActiveBreakpoint}
          />
        </CardBody>
      </Card>

      {/* A, B, C, D. Viewport & Grid Layout Adaptations */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>A - D. تكيف شبكة بطاقات المؤشرات (KPI Grid Reflow)</CardTitle>
            <CardSubtitle>
              6 أعمدة في Desktop (1440px+) → 3 في Laptop (1024px) → 2 في Tablet (768px) → 1-2 في Mobile (360px)
            </CardSubtitle>
          </div>
        </CardHeader>
        <CardBody>
          <div className="dashboard-kpi-grid">
            <div className="card dashboard-kpi-card" style={{ padding: '0.75rem' }}>
              <span className="dashboard-kpi-title">إجمالي الطلاب</span>
              <div className="dashboard-kpi-value" style={{ color: 'var(--primary-700)' }}>10</div>
              <span className="dashboard-kpi-subtitle">العام الدراسي الحالي</span>
            </div>
            <div className="card dashboard-kpi-card" style={{ padding: '0.75rem' }}>
              <span className="dashboard-kpi-title">المعلمون</span>
              <div className="dashboard-kpi-value">19</div>
              <span className="dashboard-kpi-subtitle">كادر نشط</span>
            </div>
            <div className="card dashboard-kpi-card" style={{ padding: '0.75rem' }}>
              <span className="dashboard-kpi-title">الفصول والشعب</span>
              <div className="dashboard-kpi-value">16</div>
              <span className="dashboard-kpi-subtitle">قيد التشغيل</span>
            </div>
            <div className="card dashboard-kpi-card" style={{ padding: '0.75rem' }}>
              <span className="dashboard-kpi-title">نسبة الحضور</span>
              <div className="dashboard-kpi-value" style={{ color: 'var(--success-700)' }}>94.6%</div>
              <span className="dashboard-kpi-subtitle">اليوم الدراسي</span>
            </div>
            <div className="card dashboard-kpi-card" style={{ padding: '0.75rem' }}>
              <span className="dashboard-kpi-title">الغياب اليوم</span>
              <div className="dashboard-kpi-value" style={{ color: 'var(--danger-700)' }}>0</div>
              <span className="dashboard-kpi-subtitle">بدون عذر</span>
            </div>
            <div className="card dashboard-kpi-card" style={{ padding: '0.75rem' }}>
              <span className="dashboard-kpi-title">التأخر الصباحي</span>
              <div className="dashboard-kpi-value" style={{ color: 'var(--warning-700)' }}>1</div>
              <span className="dashboard-kpi-subtitle">مسجل اليوم</span>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* E. Responsive Data Table Strategy */}
      <Card>
        <CardHeader>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div>
              <CardTitle>E. استراتيجية الجداول المتجاوبة (Responsive Data Table)</CardTitle>
              <CardSubtitle>جدول كامل مع شريط تمرير أفقي على الأجهزة الكبيرة وقوائم بطاقات ذكية على الجوال</CardSubtitle>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEnableMobileCardView(!enableMobileCardView)}
            >
              {enableMobileCardView ? 'تعطيل وضع بطاقات الجوال' : 'تفعيل وضع بطاقات الجوال'}
            </Button>
          </div>
        </CardHeader>
        <CardBody style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* F. Search & Filter Adaptation */}
          <ResponsiveFilterBar
            searchValue={searchValue}
            onSearchChange={setSearchValue}
            searchPlaceholder="بحث باسم الطالب أو رقم الهوية..."
            activeFilterCount={selectedGrade ? 1 : 0}
            onResetFilters={() => {
              setSearchValue('');
              setSelectedGrade('');
            }}
            filtersContent={
              <select
                value={selectedGrade}
                onChange={(e) => setSelectedGrade(e.target.value)}
                className="form-select"
                style={{ height: '36px', fontSize: '0.8125rem', width: 'auto', minWidth: '160px' }}
                aria-label="تصفية حسب الصف"
              >
                <option value="">جميع الصفوف</option>
                <option value="العاشر">الصف العاشر</option>
                <option value="التاسع">الصف التاسع</option>
              </select>
            }
            actionsContent={
              /* G. Excel Actions Across Breakpoints */
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button
                  variant="primary"
                  size="sm"
                  leftIcon={<Plus size={14} />}
                  onClick={() => toast.info('فتح نموذج إضافة طالب جديد')}
                >
                  إضافة طالب
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  leftIcon={<FileSpreadsheet size={14} />}
                  onClick={() => toast.success('جاري تجهيز ملف استيراد الطلاب', 'Excel')}
                >
                  استيراد Excel
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  leftIcon={<Download size={14} />}
                  onClick={() => toast.success('تم تصدير سجلات الطلاب', 'Excel')}
                >
                  تصدير
                </Button>
              </div>
            }
          />

          {/* Table Container */}
          <ResponsiveTable
            columns={[
              { key: 'national_id', header: 'رقم الهوية', width: '130px' },
              { key: 'name', header: 'اسم الطالب', render: (s) => <strong>{s.name}</strong> },
              { key: 'grade_section', header: 'الصف والشعبة' },
              { key: 'phone', header: 'رقم الجوال' },
              {
                key: 'status',
                header: 'الحالة اليوم',
                render: (s) => (
                  <Badge variant={s.status === 'active' ? 'success' : s.status === 'absent' ? 'danger' : 'warning'}>
                    {s.status === 'active' ? 'حاضر' : s.status === 'absent' ? 'غائب' : 'متأخر'}
                  </Badge>
                ),
              },
              {
                key: 'actions',
                header: 'الإجراءات',
                align: 'center',
                render: (s) => (
                  <div style={{ display: 'flex', gap: '0.375rem', justifyContent: 'center' }}>
                    <Button variant="outline" size="sm" onClick={() => toast.info(`تعديل بيانات ${s.name}`)}>
                      <Edit2 size={13} />
                    </Button>
                    <Button variant="danger" size="sm" onClick={() => toast.error(`حذف سجل ${s.name}`)}>
                      <Trash2 size={13} />
                    </Button>
                  </div>
                ),
              },
            ]}
            data={filteredStudents}
            keyExtractor={(s) => s.id}
            enableMobileCardView={enableMobileCardView}
            mobileCardRender={(s) => (
              <>
                <div className="table-mobile-card-row">
                  <span className="table-mobile-card-label">اسم الطالب:</span>
                  <span className="table-mobile-card-value"><strong>{s.name}</strong></span>
                </div>
                <div className="table-mobile-card-row">
                  <span className="table-mobile-card-label">رقم الهوية:</span>
                  <span className="table-mobile-card-value">{s.national_id}</span>
                </div>
                <div className="table-mobile-card-row">
                  <span className="table-mobile-card-label">الصف والشعبة:</span>
                  <span className="table-mobile-card-value">{s.grade_section}</span>
                </div>
                <div className="table-mobile-card-row">
                  <span className="table-mobile-card-label">الحالة اليوم:</span>
                  <Badge variant={s.status === 'active' ? 'success' : s.status === 'absent' ? 'danger' : 'warning'}>
                    {s.status === 'active' ? 'حاضر' : s.status === 'absent' ? 'غائب' : 'متأخر'}
                  </Badge>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <Button variant="outline" size="sm" style={{ flex: 1 }} onClick={() => toast.info(`تعديل بيانات ${s.name}`)}>
                    تعديل
                  </Button>
                  <Button variant="danger" size="sm" onClick={() => toast.error(`حذف ${s.name}`)}>
                    حذف
                  </Button>
                </div>
              </>
            )}
          />
        </CardBody>
      </Card>

      {/* H. Responsive Forms */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>H. النماذج المتجاوبة (Responsive Form Grid)</CardTitle>
            <CardSubtitle>عمودان في الشاشات العريضة وتتحول تلقائياً لعمود واحد كامل العرض على الجوال</CardSubtitle>
          </div>
        </CardHeader>
        <CardBody>
          <form onSubmit={(e) => { e.preventDefault(); toast.success('تم حفظ النموذج بنجاح'); }}>
            <div className="form-responsive-grid">
              <Input label="اسم الطالب الرباعي" placeholder="أدخل اسم الطالب..." defaultValue="محمد عبد الله أحمد" />
              <Input label="رقم الهوية الوطنية / الإقامة" placeholder="10 أرقام..." defaultValue="1029384756" />
              <Input label="الصف الدراسي" defaultValue="الصف العاشر" />
              <Input label="الشعبة" defaultValue="شعبة 1" />
              <Input label="تاريخ الميلاد" type="date" defaultValue="2010-05-14" />
              <Input label="رقم جوال ولي الأمر" placeholder="05xxxxxxxx" defaultValue="0501234567" />
            </div>

            <div className="form-responsive-actions">
              <Button type="button" variant="outline" onClick={() => toast.info('تم إلغاء التعديل')}>
                إلغاء
              </Button>
              <Button type="submit" variant="primary">
                حفظ التغييرات
              </Button>
            </div>
          </form>
        </CardBody>
      </Card>

      {/* J. Historical Read-Only Across Devices */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>J. التنبيه التاريخي المتجاوب (Historical Banner Across Devices)</CardTitle>
            <CardSubtitle>تنبيه ثابت ومتجاوب يوضح وضع القراءة فقط دون حدوث فيض أفقي على الجوال</CardSubtitle>
          </div>
        </CardHeader>
        <CardBody>
          <div
            style={{
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: '#fffbeb',
              border: '1px solid #fde68a',
              color: '#92400e',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '0.75rem',
              flexWrap: 'wrap',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
              <Clock size={18} style={{ flexShrink: 0 }} />
              <div>
                <strong style={{ fontSize: '0.8125rem', display: 'block' }}>
                  أنت تستعرض بيانات عام دراسي سابق — البيانات للقراءة فقط
                </strong>
                <span style={{ fontSize: '0.75rem', color: '#b45309' }}>
                  جميع عمليات التعديل والإضافة معطلة في هذا السياق.
                </span>
              </div>
            </div>
            <Badge variant="warning">قراءة فقط</Badge>
          </div>
        </CardBody>
      </Card>

      {/* K. Navigation Adaptation & Mobile Drawer Trigger */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>K. تكيف القائمة الجانبية (Navigation & Off-Canvas Drawer)</CardTitle>
            <CardSubtitle>القائمة الجانبية تتحول لدرج منبثق جانبي من اليمين (RTL) عند النقر على زر القائمة</CardSubtitle>
          </div>
        </CardHeader>
        <CardBody>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '1rem', lineHeight: 1.5 }}>
            في الشاشات الصغيرة (أقل من 768px)، تختفي القائمة الجانبية تلقائياً لتوفير المساحة، ويظهر زر القائمة
            (Hamburger) في الشريط العلوي لفتح الدرج الجانبي المتجاوب مع طبقة تعتيم خارجية.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <Button
              variant="outline"
              leftIcon={<Menu size={16} />}
              onClick={() => toast.info('يمكنك تجربة الدرج الجانبي بتصغير نافذة المتصفح والنقر على أيقونة القائمة في الشريط العلوي')}
            >
              تعليمات اختبار الدرج الجانبي
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};
