import React, { useCallback, useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { Badge, Button, Card, CardHeader, ResponsiveTable } from '../components/ui';
import { EmptyState, LoadingSpinner } from '../components/feedback';
import { useAuth } from '../context';
import { Kpi } from './FeesPage';
import { useStableToast } from '../hooks/useStableToast';
import {
  billingService,
  formatMoney,
  PAYMENT_METHOD_LABELS,
  SUBSCRIPTION_STATUS_LABELS,
  SUBSCRIPTION_WARNING_TEXT,
  type PaymentMethod,
  type Plan,
  type PlatformInvoice,
  type PlatformSchoolRow,
  type PlatformSummary,
} from '../services/billingService';

type Tab = 'summary' | 'schools' | 'plans' | 'invoices';

const row: React.CSSProperties = { display: 'flex', gap: '.65rem', flexWrap: 'wrap', alignItems: 'end' };
const field: React.CSSProperties = { display: 'grid', gap: '.3rem', fontSize: '.85rem', color: 'var(--text-secondary)' };
const input: React.CSSProperties = {
  minHeight: 38, padding: '.45rem .65rem', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)',
  background: 'var(--surface-primary)', color: 'var(--text-primary)', minWidth: 130,
};
const box: React.CSSProperties = { ...row, padding: '.75rem', background: 'var(--surface-secondary)', borderRadius: 'var(--radius-md)' };

const errorText = (err: unknown): string => {
  const errors = (err as { errors?: Record<string, unknown> })?.errors;
  if (errors) {
    const first = Object.values(errors).flat().find((value) => typeof value === 'string');
    if (typeof first === 'string') return first;
  }
  return err instanceof Error && err.message ? err.message : 'تعذر تنفيذ العملية.';
};

const isoDate = (offsetDays = 0) => {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().slice(0, 10);
};

const STATUS_VARIANT = (status: string | null) =>
  status === 'active' ? 'success' : status === 'trial' ? 'primary' : status === 'past_due' ? 'warning' : status ? 'danger' : 'neutral';

/* ---------- Summary ---------- */
const SummaryTab: React.FC = () => {
  const [data, setData] = useState<PlatformSummary | null>(null);
  useEffect(() => { billingService.platformSummary().then(setData).catch(() => setData(null)); }, []);
  if (!data) return <LoadingSpinner text="تحميل الملخص..." />;
  return (
    <div style={{ display: 'grid', gap: '.75rem', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))' }}>
      <Kpi label="المدارس" value={String(data.schools_total)} hint={`${data.schools_active} نشطة`} />
      <Kpi label="اشتراكات نشطة" value={String(data.subscriptions.active || 0)} hint={`تجريبي ${data.subscriptions.trial || 0}`} />
      <Kpi label="متأخرة السداد" value={String(data.subscriptions.past_due || 0)} tone="var(--warning-700, #b45309)" />
      <Kpi label="بدون اشتراك" value={String(data.schools_without_subscription)} />
      <Kpi label="تنتهي خلال 30 يومًا" value={String(data.expiring_soon)} />
      <Kpi label="المستحق" value={formatMoney(data.outstanding)} />
      <Kpi label="المتأخر" value={formatMoney(data.overdue)} tone="var(--danger-600, #b91c1c)" />
      <Kpi label="محصّل هذا الشهر" value={formatMoney(data.collected_this_month)} />
      <Kpi label="مفوتر هذا العام" value={formatMoney(data.invoiced_this_year)} />
    </div>
  );
};

/* ---------- Schools ---------- */
const SchoolsTab: React.FC = () => {
  const toast = useStableToast();
  const [warning, setWarning] = useState('');
  const [rows, setRows] = useState<PlatformSchoolRow[] | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscribing, setSubscribing] = useState<PlatformSchoolRow | null>(null);
  const [invoicing, setInvoicing] = useState<PlatformSchoolRow | null>(null);
  const [form, setForm] = useState({ plan: '', status: 'active', start_date: isoDate(), end_date: isoDate(365) });
  const [invoiceForm, setInvoiceForm] = useState({ period_start: isoDate(), period_end: isoDate(364), due_date: isoDate(14) });

  const load = useCallback(() => {
    billingService.platformSchools(warning || undefined).then((res) => setRows(res.results)).catch((err) => toast.error(errorText(err)));
  }, [warning, toast]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { billingService.plans().then(setPlans).catch(() => setPlans([])); }, []);

  const subscribe = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!subscribing) return;
    try {
      await billingService.createSubscription({ school: subscribing.school_id, ...form, plan: Number(form.plan) });
      toast.success('تم حفظ الاشتراك.');
      setSubscribing(null);
      load();
    } catch (err) { toast.error(errorText(err)); }
  };

  const changeStatus = async (school: PlatformSchoolRow, status: string) => {
    if (!school.id) return;
    try {
      await billingService.updateSubscription(school.id, { status });
      toast.success('تم تحديث حالة الاشتراك.');
      load();
    } catch (err) { toast.error(errorText(err)); }
  };

  const issue = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!invoicing?.id) return;
    try {
      const invoice = await billingService.issueInvoice({ subscription_id: invoicing.id, ...invoiceForm });
      toast.success(`تم إصدار الفاتورة ${invoice.number} بمبلغ ${formatMoney(invoice.amount, invoice.currency)}.`);
      setInvoicing(null);
      load();
    } catch (err) { toast.error(errorText(err)); }
  };

  const activePlans = plans.filter((plan) => plan.is_active);

  return (
    <div style={{ display: 'grid', gap: '.85rem' }}>
      <div style={row}>
        <label style={field}>تصفية حسب التنبيه
          <select style={input} value={warning} onChange={(event) => setWarning(event.target.value)}>
            <option value="">الكل</option>
            {Object.keys(SUBSCRIPTION_WARNING_TEXT).map((key) => <option key={key} value={key}>{SUBSCRIPTION_WARNING_TEXT[key].split('.')[0]}</option>)}
          </select>
        </label>
      </div>

      {subscribing && (
        <form style={box} onSubmit={subscribe} aria-label="اشتراك جديد">
          <strong style={{ width: '100%' }}>اشتراك جديد / تجديد: {subscribing.school_name}</strong>
          <label style={field}>الباقة
            <select style={input} required value={form.plan} onChange={(event) => setForm({ ...form, plan: event.target.value })}>
              <option value="">اختر</option>
              {activePlans.map((plan) => <option key={plan.id} value={plan.id}>{plan.name}</option>)}
            </select>
          </label>
          <label style={field}>الحالة
            <select style={input} value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
              <option value="active">نشط</option>
              <option value="trial">تجريبي</option>
            </select>
          </label>
          <label style={field}>البداية<input style={input} type="date" required value={form.start_date} onChange={(event) => setForm({ ...form, start_date: event.target.value })} /></label>
          <label style={field}>النهاية<input style={input} type="date" required value={form.end_date} onChange={(event) => setForm({ ...form, end_date: event.target.value })} /></label>
          <Button type="submit">حفظ</Button>
          <Button type="button" variant="outline" onClick={() => setSubscribing(null)}>إلغاء</Button>
          {subscribing.has_subscription && <small style={{ width: '100%' }}>سيُغلق الاشتراك الحالي ويُحفظ في السجل.</small>}
        </form>
      )}

      {invoicing && (
        <form style={box} onSubmit={issue} aria-label="إصدار فاتورة">
          <strong style={{ width: '100%' }}>فاتورة لـ {invoicing.school_name} ({invoicing.student_count} طالب نشط)</strong>
          <label style={field}>من<input style={input} type="date" required value={invoiceForm.period_start} onChange={(event) => setInvoiceForm({ ...invoiceForm, period_start: event.target.value })} /></label>
          <label style={field}>إلى<input style={input} type="date" required value={invoiceForm.period_end} onChange={(event) => setInvoiceForm({ ...invoiceForm, period_end: event.target.value })} /></label>
          <label style={field}>الاستحقاق<input style={input} type="date" required value={invoiceForm.due_date} onChange={(event) => setInvoiceForm({ ...invoiceForm, due_date: event.target.value })} /></label>
          <Button type="submit">إصدار</Button>
          <Button type="button" variant="outline" onClick={() => setInvoicing(null)}>إلغاء</Button>
        </form>
      )}

      {!rows ? <LoadingSpinner text="تحميل المدارس..." /> : (
        <ResponsiveTable
          data={rows}
          keyExtractor={(item) => item.school_id}
          emptyMessage="لا توجد مدارس مطابقة."
          columns={[
            { key: 'school_name', header: 'المدرسة', render: (s) => <span>{s.school_name}<br /><small>{s.school_code}</small></span> },
            { key: 'plan', header: 'الباقة', render: (s) => s.plan?.name || '—' },
            { key: 'status', header: 'الحالة', render: (s) => <Badge variant={STATUS_VARIANT(s.status)}>{s.status ? SUBSCRIPTION_STATUS_LABELS[s.status] : 'بدون'}</Badge> },
            { key: 'end_date', header: 'النهاية', render: (s) => s.end_date || '—' },
            { key: 'student_count', header: 'الطلاب', render: (s) => `${s.student_count}${s.student_limit ? ` / ${s.student_limit}` : ''}` },
            { key: 'outstanding', header: 'المستحق', render: (s) => formatMoney(s.outstanding, s.currency) },
            { key: 'warning', header: 'تنبيه', render: (s) => s.warning ? <Badge variant="warning">{SUBSCRIPTION_WARNING_TEXT[s.warning]?.split('.')[0] || s.warning}</Badge> : '—' },
            {
              key: 'actions', header: 'إجراءات', render: (s) => (
                <div style={{ display: 'flex', gap: '.35rem', flexWrap: 'wrap' }}>
                  <Button size="sm" onClick={() => { setInvoicing(null); setSubscribing(s); }}>{s.has_subscription ? 'تجديد' : 'اشتراك'}</Button>
                  {s.has_subscription && <Button size="sm" variant="secondary" onClick={() => { setSubscribing(null); setInvoicing(s); }}>فاتورة</Button>}
                  {s.status === 'suspended' && <Button size="sm" variant="outline" onClick={() => changeStatus(s, 'active')}>تفعيل</Button>}
                  {s.status && ['active', 'past_due', 'trial'].includes(s.status) && (
                    <Button size="sm" variant="danger" onClick={() => window.confirm(`إيقاف اشتراك ${s.school_name}؟`) && changeStatus(s, 'suspended')}>إيقاف</Button>
                  )}
                </div>
              ),
            },
          ]}
        />
      )}
    </div>
  );
};

/* ---------- Plans ---------- */
const emptyPlan = { code: '', name: '', base_price: '0', price_per_student: '0', currency: 'YER', billing_period: 'yearly', max_students: '', features: '' };

const PlansTab: React.FC = () => {
  const toast = useStableToast();
  const [plans, setPlans] = useState<Plan[] | null>(null);
  const [form, setForm] = useState(emptyPlan);
  const [open, setOpen] = useState(false);
  const load = useCallback(() => { billingService.plans().then(setPlans).catch((err) => toast.error(errorText(err))); }, [toast]);
  useEffect(() => { load(); }, [load]);

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await billingService.createPlan({
        code: form.code.trim(), name: form.name.trim(), base_price: form.base_price, price_per_student: form.price_per_student,
        currency: form.currency.trim() || 'YER', billing_period: form.billing_period as Plan['billing_period'],
        max_students: form.max_students ? Number(form.max_students) : null,
        features: form.features.split('\n').map((line) => line.trim()).filter(Boolean),
      });
      toast.success('تمت إضافة الباقة.');
      setForm(emptyPlan);
      setOpen(false);
      load();
    } catch (err) { toast.error(errorText(err)); }
  };

  const toggle = async (plan: Plan) => {
    try { await billingService.updatePlan(plan.id, { is_active: !plan.is_active }); load(); } catch (err) { toast.error(errorText(err)); }
  };

  return (
    <div style={{ display: 'grid', gap: '.85rem' }}>
      {!open ? (
        <div><Button leftIcon={<Plus size={14} />} onClick={() => setOpen(true)}>باقة جديدة</Button></div>
      ) : (
        <form style={box} onSubmit={save} aria-label="باقة جديدة">
          <label style={field}>الرمز<input style={input} required maxLength={40} value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} /></label>
          <label style={field}>الاسم<input style={input} required maxLength={120} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
          <label style={field}>السعر الأساسي<input style={input} type="number" min="0" step="0.01" value={form.base_price} onChange={(e) => setForm({ ...form, base_price: e.target.value })} /></label>
          <label style={field}>السعر لكل طالب<input style={input} type="number" min="0" step="0.01" value={form.price_per_student} onChange={(e) => setForm({ ...form, price_per_student: e.target.value })} /></label>
          <label style={field}>العملة<input style={input} maxLength={3} value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value.toUpperCase() })} /></label>
          <label style={field}>الفترة
            <select style={input} value={form.billing_period} onChange={(e) => setForm({ ...form, billing_period: e.target.value })}>
              <option value="monthly">شهري</option><option value="termly">فصلي</option><option value="yearly">سنوي</option>
            </select>
          </label>
          <label style={field}>حد الطلاب<input style={input} type="number" min="1" placeholder="بدون حد" value={form.max_students} onChange={(e) => setForm({ ...form, max_students: e.target.value })} /></label>
          <label style={{ ...field, width: '100%' }}>المزايا (ميزة في كل سطر)
            <textarea style={{ ...input, minHeight: 80 }} value={form.features} onChange={(e) => setForm({ ...form, features: e.target.value })} />
          </label>
          <Button type="submit">حفظ</Button>
          <Button type="button" variant="outline" onClick={() => setOpen(false)}>إلغاء</Button>
        </form>
      )}
      {!plans ? <LoadingSpinner /> : (
        <ResponsiveTable
          data={plans}
          keyExtractor={(item) => item.id}
          emptyMessage="لا توجد باقات بعد."
          columns={[
            { key: 'name', header: 'الباقة', render: (p) => <span>{p.name}<br /><small>{p.code}</small></span> },
            { key: 'base_price', header: 'الأساسي', render: (p) => formatMoney(p.base_price, p.currency) },
            { key: 'price_per_student', header: 'لكل طالب', render: (p) => formatMoney(p.price_per_student, p.currency) },
            { key: 'max_students', header: 'حد الطلاب', render: (p) => p.max_students ?? 'بدون' },
            { key: 'is_active', header: 'الحالة', render: (p) => <Badge variant={p.is_active ? 'success' : 'neutral'}>{p.is_active ? 'متاحة' : 'موقوفة'}</Badge> },
            { key: 'actions', header: 'إجراءات', render: (p) => <Button size="sm" variant="outline" onClick={() => toggle(p)}>{p.is_active ? 'إيقاف' : 'تفعيل'}</Button> },
          ]}
        />
      )}
    </div>
  );
};

/* ---------- Invoices ---------- */
const InvoicesTab: React.FC = () => {
  const toast = useStableToast();
  const [status, setStatus] = useState('issued');
  const [items, setItems] = useState<PlatformInvoice[] | null>(null);
  const [paying, setPaying] = useState<PlatformInvoice | null>(null);
  const [payment, setPayment] = useState<{ amount: string; method: PaymentMethod; reference: string }>({ amount: '', method: 'bank_transfer', reference: '' });

  const load = useCallback(() => {
    billingService.platformInvoices({ status: status || undefined }).then((res) => setItems(res.results)).catch((err) => toast.error(errorText(err)));
  }, [status, toast]);
  useEffect(() => { load(); }, [load]);

  const pay = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!paying) return;
    try {
      await billingService.payInvoice(paying.id, payment);
      toast.success('تم تسجيل الدفعة.');
      setPaying(null);
      load();
    } catch (err) { toast.error(errorText(err)); }
  };

  const voidIt = async (invoice: PlatformInvoice) => {
    const reason = window.prompt(`سبب إلغاء الفاتورة ${invoice.number}؟`);
    if (!reason) return;
    try { await billingService.voidInvoice(invoice.id, reason); toast.success('تم إلغاء الفاتورة.'); load(); } catch (err) { toast.error(errorText(err)); }
  };

  return (
    <div style={{ display: 'grid', gap: '.85rem' }}>
      <div style={row}>
        <label style={field}>الحالة
          <select style={input} value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">الكل</option><option value="issued">مستحقة</option><option value="paid">مدفوعة</option><option value="void">ملغاة</option>
          </select>
        </label>
      </div>
      {paying && (
        <form style={box} onSubmit={pay} aria-label="دفعة فاتورة">
          <strong style={{ width: '100%' }}>دفعة للفاتورة {paying.number} — المتبقي {formatMoney(paying.balance, paying.currency)}</strong>
          <label style={field}>المبلغ<input style={input} type="number" min="0.01" step="0.01" required max={paying.balance} value={payment.amount} onChange={(e) => setPayment({ ...payment, amount: e.target.value })} /></label>
          <label style={field}>الطريقة
            <select style={input} value={payment.method} onChange={(e) => setPayment({ ...payment, method: e.target.value as PaymentMethod })}>
              {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label style={field}>المرجع<input style={input} maxLength={120} value={payment.reference} onChange={(e) => setPayment({ ...payment, reference: e.target.value })} /></label>
          <Button type="submit">حفظ</Button>
          <Button type="button" variant="outline" onClick={() => setPaying(null)}>إلغاء</Button>
        </form>
      )}
      {!items ? <LoadingSpinner /> : (
        <ResponsiveTable
          data={items}
          keyExtractor={(item) => item.id}
          emptyMessage="لا توجد فواتير."
          columns={[
            { key: 'number', header: 'الفاتورة' },
            { key: 'school_name', header: 'المدرسة' },
            { key: 'amount', header: 'المبلغ', render: (i) => formatMoney(i.amount, i.currency) },
            { key: 'balance', header: 'المتبقي', render: (i) => formatMoney(i.balance, i.currency) },
            { key: 'due_date', header: 'الاستحقاق' },
            { key: 'status', header: 'الحالة', render: (i) => <Badge variant={i.status === 'paid' ? 'success' : i.status === 'void' ? 'neutral' : 'warning'}>{i.status === 'paid' ? 'مدفوعة' : i.status === 'void' ? 'ملغاة' : 'مستحقة'}</Badge> },
            {
              key: 'actions', header: 'إجراءات', render: (i) => i.status !== 'issued' ? '—' : (
                <div style={{ display: 'flex', gap: '.35rem', flexWrap: 'wrap' }}>
                  <Button size="sm" onClick={() => { setPayment({ amount: i.balance, method: 'bank_transfer', reference: '' }); setPaying(i); }}>دفعة</Button>
                  {Number(i.paid_amount) === 0 && <Button size="sm" variant="danger" onClick={() => voidIt(i)}>إلغاء</Button>}
                </div>
              ),
            },
          ]}
        />
      )}
    </div>
  );
};

export const PlatformPage: React.FC = () => {
  const { user, activeMembership } = useAuth();
  const [tab, setTab] = useState<Tab>('summary');

  if (user?.role !== 'super_admin' || activeMembership) {
    return <EmptyState title="لوحة مالك المنصة" description="هذه اللوحة متاحة لمالك المنصة فقط بدون اختيار مدرسة." />;
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: 'summary', label: 'الملخص' }, { id: 'schools', label: 'المدارس والاشتراكات' },
    { id: 'plans', label: 'الباقات' }, { id: 'invoices', label: 'الفواتير' },
  ];

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <Card>
        <CardHeader>
          <h1 className="card-title">إدارة المنصة والاشتراكات</h1>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '.9rem' }}>الباقات، اشتراكات المدارس، الفواتير والتحصيل اليدوي.</p>
        </CardHeader>
        <div role="tablist" aria-label="أقسام المنصة" style={{ display: 'flex', gap: '.4rem', flexWrap: 'wrap', padding: '0 1rem 1rem' }}>
          {tabs.map((item) => (
            <Button key={item.id} role="tab" aria-selected={tab === item.id} size="sm" variant={tab === item.id ? 'primary' : 'outline'} onClick={() => setTab(item.id)}>{item.label}</Button>
          ))}
        </div>
      </Card>
      <Card>
        <div style={{ padding: '1rem' }} role="tabpanel">
          {tab === 'summary' && <SummaryTab />}
          {tab === 'schools' && <SchoolsTab />}
          {tab === 'plans' && <PlansTab />}
          {tab === 'invoices' && <InvoicesTab />}
        </div>
      </Card>
    </div>
  );
};
