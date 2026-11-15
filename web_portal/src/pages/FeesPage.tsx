import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Plus, Receipt, Trash2, Wallet } from 'lucide-react';
import { Badge, Button, Card, CardHeader, CardTitle, ResponsiveTable } from '../components/ui';
import { EmptyState, LoadingSpinner } from '../components/feedback';
import { useAuth } from '../context';
import { useStableToast } from '../hooks/useStableToast';
import { academicService } from '../services/academicService';
import {
  billingService,
  formatMoney,
  PAYMENT_METHOD_LABELS,
  PAYMENT_STATE_LABELS,
  type FeeCategory,
  type FeePayment,
  type FeeSummary,
  type IssuePayload,
  type IssueResult,
  type PaymentMethod,
  type PaymentState,
  type StudentFee,
} from '../services/billingService';

type Tab = 'overview' | 'fees' | 'issue' | 'payments' | 'categories';

const TABS: Array<{ id: Tab; label: string }> = [
  { id: 'overview', label: 'نظرة عامة' },
  { id: 'fees', label: 'رسوم الطلاب' },
  { id: 'issue', label: 'إصدار رسوم' },
  { id: 'payments', label: 'الدفعات والإيصالات' },
  { id: 'categories', label: 'بنود الرسوم' },
];

const panel: React.CSSProperties = { padding: '1rem', display: 'grid', gap: '.85rem' };
const row: React.CSSProperties = { display: 'flex', gap: '.65rem', flexWrap: 'wrap', alignItems: 'end' };
const field: React.CSSProperties = { display: 'grid', gap: '.3rem', fontSize: '.85rem', color: 'var(--text-secondary)' };
const input: React.CSSProperties = {
  minHeight: 38, padding: '.45rem .65rem', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)',
  background: 'var(--surface-primary)', color: 'var(--text-primary)', minWidth: 140,
};
const kpiGrid: React.CSSProperties = { display: 'grid', gap: '.75rem', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))' };
const kpiCard: React.CSSProperties = {
  padding: '.9rem 1rem', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)',
  background: 'var(--surface-primary)', display: 'grid', gap: '.25rem',
};

const STATE_VARIANT: Record<PaymentState, 'success' | 'warning' | 'danger' | 'neutral' | 'primary'> = {
  paid: 'success', partial: 'primary', unpaid: 'neutral', overdue: 'danger', cancelled: 'neutral',
};

const errorText = (err: unknown): string => {
  if (err && typeof err === 'object') {
    const errors = (err as { errors?: Record<string, unknown> }).errors;
    if (errors) {
      const first = Object.values(errors).flat().find((value) => typeof value === 'string');
      if (typeof first === 'string') return first;
    }
    if (err instanceof Error && err.message) return err.message;
  }
  return 'تعذر تنفيذ العملية.';
};

const today = () => new Date().toISOString().slice(0, 10);

export const Kpi: React.FC<{ label: string; value: string; tone?: string; hint?: string }> = ({ label, value, tone, hint }) => (
  <div style={kpiCard}>
    <span style={{ fontSize: '.8rem', color: 'var(--text-secondary)' }}>{label}</span>
    <strong style={{ fontSize: '1.25rem', color: tone || 'var(--text-primary)' }}>{value}</strong>
    {hint && <span style={{ fontSize: '.75rem', color: 'var(--text-tertiary, var(--text-secondary))' }}>{hint}</span>}
  </div>
);

export const StateBadge: React.FC<{ state: PaymentState }> = ({ state }) => (
  <Badge variant={STATE_VARIANT[state]}>{PAYMENT_STATE_LABELS[state]}</Badge>
);

/* ---------------- Overview ---------------- */
const Overview: React.FC = () => {
  const [summary, setSummary] = useState<FeeSummary | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    billingService.feeSummary().then(setSummary).catch(() => setFailed(true));
  }, []);
  if (failed) return <EmptyState title="تعذر تحميل الملخص" description="حاول مرة أخرى لاحقًا." />;
  if (!summary) return <LoadingSpinner text="تحميل الملخص..." />;
  const currency = summary.currency;
  if (!summary.fee_count) {
    return <EmptyState title="لا توجد رسوم بعد" description="ابدأ بإضافة بند رسوم ثم أصدر الرسوم للطلاب." />;
  }
  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <div style={kpiGrid}>
        <Kpi label="إجمالي المستحق" value={formatMoney(summary.total, currency)} />
        <Kpi label="المحصّل" value={formatMoney(summary.paid, currency)} tone="var(--success-600, #15803d)" />
        <Kpi label="المتبقي" value={formatMoney(summary.remaining, currency)} />
        <Kpi label="المتأخر" value={formatMoney(summary.overdue, currency)} tone="var(--danger-600, #b91c1c)"
          hint={`${summary.overdue_count} قسط متأخر`} />
        <Kpi label="محصّل هذا الشهر" value={formatMoney(summary.collected_this_month, currency)} />
      </div>
      {summary.by_category && summary.by_category.length > 0 && (
        <ResponsiveTable
          data={summary.by_category}
          keyExtractor={(item) => item.id}
          columns={[
            { key: 'name', header: 'البند' },
            { key: 'total', header: 'المستحق', render: (item) => formatMoney(item.total, currency) },
            { key: 'paid', header: 'المحصّل', render: (item) => formatMoney(item.paid, currency) },
            { key: 'remaining', header: 'المتبقي', render: (item) => formatMoney(item.remaining, currency) },
            { key: 'overdue', header: 'المتأخر', render: (item) => formatMoney(item.overdue, currency) },
          ]}
        />
      )}
    </div>
  );
};

/* ---------------- Fees list + payment ---------------- */
const PaymentForm: React.FC<{ fee: StudentFee; onDone: () => void; onCancel: () => void }> = ({ fee, onDone, onCancel }) => {
  const toast = useStableToast();
  const [amount, setAmount] = useState(fee.balance);
  const [method, setMethod] = useState<PaymentMethod>('cash');
  const [paidOn, setPaidOn] = useState(today());
  const [reference, setReference] = useState('');
  const [saving, setSaving] = useState(false);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      const payment = await billingService.recordPayment(fee.id, { amount, method, paid_on: paidOn, reference });
      toast.success(`تم تسجيل الدفعة. رقم الإيصال ${payment.receipt_number}`);
      onDone();
    } catch (err) {
      toast.error(errorText(err));
    } finally {
      setSaving(false);
    }
  };
  return (
    <form onSubmit={submit} aria-label="تسجيل دفعة" style={{ ...row, padding: '.75rem', background: 'var(--surface-secondary)', borderRadius: 'var(--radius-md)' }}>
      <strong style={{ width: '100%' }}>تسجيل دفعة: {fee.student_name} — {fee.title} (المتبقي {formatMoney(fee.balance, fee.currency)})</strong>
      <label style={field}>المبلغ
        <input style={input} type="number" min="0.01" step="0.01" max={fee.balance} required value={amount}
          onChange={(event) => setAmount(event.target.value)} />
      </label>
      <label style={field}>طريقة الدفع
        <select style={input} value={method} onChange={(event) => setMethod(event.target.value as PaymentMethod)}>
          {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </label>
      <label style={field}>تاريخ الدفع
        <input style={input} type="date" max={today()} value={paidOn} onChange={(event) => setPaidOn(event.target.value)} />
      </label>
      <label style={field}>المرجع (اختياري)
        <input style={input} value={reference} maxLength={120} onChange={(event) => setReference(event.target.value)} />
      </label>
      <Button type="submit" isLoading={saving}>حفظ الدفعة</Button>
      <Button type="button" variant="outline" onClick={onCancel}>إلغاء</Button>
    </form>
  );
};

const FeesList: React.FC<{ readOnly: boolean; categories: FeeCategory[] }> = ({ readOnly, categories }) => {
  const toast = useStableToast();
  const [filters, setFilters] = useState({ search: '', state: '', category: '' });
  const [page, setPage] = useState(1);
  const [data, setData] = useState<{ count: number; results: StudentFee[]; summary: FeeSummary } | null>(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState<StudentFee | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    billingService.fees({ ...filters, page })
      .then(setData)
      .catch((err) => toast.error(errorText(err)))
      .finally(() => setLoading(false));
  }, [filters, page, toast]);

  useEffect(() => { load(); }, [load]);

  const cancel = async (fee: StudentFee) => {
    const reason = window.prompt('سبب إلغاء الرسوم؟');
    if (!reason) return;
    try {
      await billingService.cancelFee(fee.id, reason);
      toast.success('تم إلغاء الرسوم.');
      load();
    } catch (err) {
      toast.error(errorText(err));
    }
  };

  const pages = data ? Math.max(1, Math.ceil(data.count / 25)) : 1;
  const currency = data?.summary.currency;

  return (
    <div style={{ display: 'grid', gap: '.85rem' }}>
      <div style={row} role="search">
        <label style={field}>بحث
          <input style={input} placeholder="اسم الطالب أو رقمه أو البند" value={filters.search}
            onChange={(event) => { setPage(1); setFilters({ ...filters, search: event.target.value }); }} />
        </label>
        <label style={field}>الحالة
          <select style={input} value={filters.state} onChange={(event) => { setPage(1); setFilters({ ...filters, state: event.target.value }); }}>
            <option value="">الكل</option>
            {Object.entries(PAYMENT_STATE_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label style={field}>البند
          <select style={input} value={filters.category} onChange={(event) => { setPage(1); setFilters({ ...filters, category: event.target.value }); }}>
            <option value="">الكل</option>
            {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
          </select>
        </label>
      </div>
      {data && (
        <div style={kpiGrid}>
          <Kpi label="المستحق (حسب الفلتر)" value={formatMoney(data.summary.total, currency)} />
          <Kpi label="المحصّل" value={formatMoney(data.summary.paid, currency)} />
          <Kpi label="المتبقي" value={formatMoney(data.summary.remaining, currency)} />
          <Kpi label="المتأخر" value={formatMoney(data.summary.overdue, currency)} />
        </div>
      )}
      {paying && <PaymentForm fee={paying} onCancel={() => setPaying(null)} onDone={() => { setPaying(null); load(); }} />}
      {loading && !data ? <LoadingSpinner text="تحميل الرسوم..." /> : (
        <ResponsiveTable
          data={data?.results || []}
          keyExtractor={(item) => item.id}
          emptyMessage="لا توجد رسوم مطابقة."
          columns={[
            { key: 'student_name', header: 'الطالب', render: (fee) => <span>{fee.student_name}<br /><small>{fee.student_code}</small></span> },
            { key: 'title', header: 'البند', render: (fee) => <span>{fee.title}{fee.installment_count > 1 && <small> (قسط {fee.installment_number}/{fee.installment_count})</small>}</span> },
            { key: 'net_amount', header: 'الصافي', render: (fee) => formatMoney(fee.net_amount, fee.currency) },
            { key: 'paid_amount', header: 'المدفوع', render: (fee) => formatMoney(fee.paid_amount, fee.currency) },
            { key: 'balance', header: 'المتبقي', render: (fee) => formatMoney(fee.balance, fee.currency) },
            { key: 'due_date', header: 'الاستحقاق' },
            { key: 'payment_state', header: 'الحالة', render: (fee) => <StateBadge state={fee.payment_state} /> },
            {
              key: 'actions', header: 'إجراءات', render: (fee) => readOnly || fee.status === 'cancelled' ? '—' : (
                <div style={{ display: 'flex', gap: '.35rem', flexWrap: 'wrap' }}>
                  {Number(fee.balance) > 0 && <Button size="sm" leftIcon={<Wallet size={14} />} onClick={() => setPaying(fee)}>دفعة</Button>}
                  {Number(fee.paid_amount) === 0 && <Button size="sm" variant="outline" leftIcon={<Trash2 size={14} />} onClick={() => cancel(fee)}>إلغاء</Button>}
                </div>
              ),
            },
          ]}
        />
      )}
      {pages > 1 && (
        <div style={{ ...row, justifyContent: 'center' }}>
          <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage(page - 1)}>السابق</Button>
          <span>صفحة {page} من {pages}</span>
          <Button size="sm" variant="outline" disabled={page >= pages} onClick={() => setPage(page + 1)}>التالي</Button>
        </div>
      )}
    </div>
  );
};

/* ---------------- Issue ---------------- */
interface Option { id: number; name: string }

const IssueForm: React.FC<{ categories: FeeCategory[]; onIssued: () => void }> = ({ categories, onIssued }) => {
  const toast = useStableToast();
  const active = categories.filter((category) => category.is_active);
  const [categoryId, setCategoryId] = useState<number | ''>(active[0]?.id ?? '');
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [discount, setDiscount] = useState('0');
  const [dueDate, setDueDate] = useState(today());
  const [useInstallments, setUseInstallments] = useState(false);
  const [installments, setInstallments] = useState<Array<{ amount: string; due_date: string }>>([
    { amount: '', due_date: today() }, { amount: '', due_date: today() },
  ]);
  const [scope, setScope] = useState<IssuePayload['scope']>('school');
  const [classrooms, setClassrooms] = useState<Option[]>([]);
  const [sections, setSections] = useState<Option[]>([]);
  const [classroomId, setClassroomId] = useState<number | ''>('');
  const [sectionId, setSectionId] = useState<number | ''>('');
  const [preview, setPreview] = useState<IssueResult | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    academicService.getClassrooms({ is_active: true }).then((res) => setClassrooms(res.results)).catch(() => setClassrooms([]));
  }, []);
  useEffect(() => {
    if (!classroomId) { setSections([]); return; }
    academicService.getSections({ classroom_id: Number(classroomId), is_active: true })
      .then((res) => setSections(res.results)).catch(() => setSections([]));
  }, [classroomId]);

  const installmentTotal = useMemo(
    () => installments.reduce((sum, item) => sum + (Number(item.amount) || 0), 0), [installments],
  );

  const payload = (confirm: boolean): IssuePayload | null => {
    if (!categoryId) { toast.error('اختر بند الرسوم.'); return null; }
    const body: IssuePayload = { category_id: Number(categoryId), title: title.trim(), amount, discount: discount || '0', scope, confirm };
    if (useInstallments) body.installments = installments;
    else body.due_date = dueDate;
    if (scope === 'classroom' || scope === 'section') {
      if (!classroomId) { toast.error('اختر الصف.'); return null; }
      body.classroom_id = Number(classroomId);
    }
    if (scope === 'section') {
      if (!sectionId) { toast.error('اختر الشعبة.'); return null; }
      body.section_id = Number(sectionId);
    }
    return body;
  };

  const run = async (confirm: boolean) => {
    const body = payload(confirm);
    if (!body) return;
    setBusy(true);
    try {
      const result = await billingService.issueFees(body);
      if (confirm) {
        toast.success(`تم إصدار ${result.created ?? 0} سجل رسوم لعدد ${result.student_count} طالب.`);
        setPreview(null);
        setTitle('');
        setAmount('');
        onIssued();
      } else {
        setPreview(result);
      }
    } catch (err) {
      toast.error(errorText(err));
    } finally {
      setBusy(false);
    }
  };

  if (!active.length) {
    return <EmptyState title="لا توجد بنود رسوم" description="أضف بندًا من تبويب «بنود الرسوم» أولًا (مثل: رسوم دراسية، نقل)." />;
  }

  return (
    <form style={{ display: 'grid', gap: '1rem' }} onSubmit={(event) => { event.preventDefault(); run(false); }} aria-label="إصدار رسوم">
      <div style={row}>
        <label style={field}>البند
          <select style={input} value={categoryId} onChange={(event) => { setPreview(null); setCategoryId(Number(event.target.value)); }}>
            {active.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
          </select>
        </label>
        <label style={{ ...field, flex: 1 }}>العنوان
          <input style={input} required maxLength={180} placeholder="مثال: رسوم الفصل الأول" value={title}
            onChange={(event) => { setPreview(null); setTitle(event.target.value); }} />
        </label>
        <label style={field}>المبلغ لكل طالب
          <input style={input} type="number" min="0.01" step="0.01" required value={amount}
            onChange={(event) => { setPreview(null); setAmount(event.target.value); }} />
        </label>
        <label style={field}>الخصم لكل طالب
          <input style={input} type="number" min="0" step="0.01" value={discount}
            onChange={(event) => { setPreview(null); setDiscount(event.target.value); }} />
        </label>
      </div>

      <div style={row}>
        <label style={{ ...field, flexDirection: 'row', display: 'flex', alignItems: 'center', gap: '.4rem' }}>
          <input type="checkbox" checked={useInstallments} onChange={(event) => { setPreview(null); setUseInstallments(event.target.checked); }} />
          تقسيط المبلغ على دفعات
        </label>
        {!useInstallments && (
          <label style={field}>تاريخ الاستحقاق
            <input style={input} type="date" required value={dueDate} onChange={(event) => { setPreview(null); setDueDate(event.target.value); }} />
          </label>
        )}
      </div>

      {useInstallments && (
        <div style={{ display: 'grid', gap: '.5rem' }}>
          {installments.map((item, index) => (
            <div key={index} style={row}>
              <span style={{ minWidth: 70 }}>القسط {index + 1}</span>
              <input aria-label={`مبلغ القسط ${index + 1}`} style={input} type="number" min="0.01" step="0.01" required value={item.amount}
                onChange={(event) => { setPreview(null); setInstallments(installments.map((it, i) => i === index ? { ...it, amount: event.target.value } : it)); }} />
              <input aria-label={`تاريخ القسط ${index + 1}`} style={input} type="date" required value={item.due_date}
                onChange={(event) => { setPreview(null); setInstallments(installments.map((it, i) => i === index ? { ...it, due_date: event.target.value } : it)); }} />
              {installments.length > 2 && (
                <Button type="button" size="sm" variant="outline" onClick={() => setInstallments(installments.filter((_, i) => i !== index))}>حذف</Button>
              )}
            </div>
          ))}
          <div style={row}>
            {installments.length < 12 && (
              <Button type="button" size="sm" variant="secondary" leftIcon={<Plus size={14} />}
                onClick={() => setInstallments([...installments, { amount: '', due_date: today() }])}>إضافة قسط</Button>
            )}
            <span style={{ color: Math.abs(installmentTotal - Number(amount || 0)) < 0.005 ? 'var(--text-secondary)' : 'var(--danger-600, #b91c1c)' }}>
              مجموع الأقساط {formatMoney(installmentTotal)} من {formatMoney(amount || 0)}
            </span>
          </div>
        </div>
      )}

      <div style={row}>
        <label style={field}>الطلاب المستهدفون
          <select style={input} value={scope} onChange={(event) => { setPreview(null); setScope(event.target.value as IssuePayload['scope']); }}>
            <option value="school">كل طلاب المدرسة</option>
            <option value="classroom">صف محدد</option>
            <option value="section">شعبة محددة</option>
          </select>
        </label>
        {(scope === 'classroom' || scope === 'section') && (
          <label style={field}>الصف
            <select style={input} value={classroomId} onChange={(event) => { setPreview(null); setSectionId(''); setClassroomId(Number(event.target.value) || ''); }}>
              <option value="">اختر</option>
              {classrooms.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
        )}
        {scope === 'section' && (
          <label style={field}>الشعبة
            <select style={input} value={sectionId} onChange={(event) => { setPreview(null); setSectionId(Number(event.target.value) || ''); }}>
              <option value="">اختر</option>
              {sections.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
        )}
        <Button type="submit" variant="secondary" isLoading={busy && !preview}>معاينة</Button>
      </div>

      {preview && (
        <div role="region" aria-label="معاينة الإصدار" style={{ ...panel, border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)' }}>
          <strong>سيتم إصدار الرسوم لعدد {preview.student_count} طالب ({preview.installment_count} قسط لكل طالب)</strong>
          <span>الصافي لكل طالب: {formatMoney(Number(preview.amount_per_student) - Number(preview.discount_per_student))} — الإجمالي: {formatMoney(preview.total_net)}</span>
          <small>عينة من الطلاب: {preview.students.slice(0, 8).map((student) => student.full_name).join('، ')}{preview.student_count > 8 ? '…' : ''}</small>
          <span style={{ fontSize: '.85rem', color: 'var(--text-secondary)' }}>سيصل إشعار لأولياء الأمور المخوّلين بالاطلاع المالي.</span>
          <div style={row}>
            <Button type="button" onClick={() => run(true)} isLoading={busy}>تأكيد الإصدار</Button>
            <Button type="button" variant="outline" onClick={() => setPreview(null)}>تعديل</Button>
          </div>
        </div>
      )}
    </form>
  );
};

/* ---------------- Payments ---------------- */
const Payments: React.FC<{ readOnly: boolean }> = ({ readOnly }) => {
  const toast = useStableToast();
  const [search, setSearch] = useState('');
  const [items, setItems] = useState<FeePayment[] | null>(null);
  const load = useCallback(() => {
    billingService.payments({ search }).then((res) => setItems(res.results)).catch((err) => toast.error(errorText(err)));
  }, [search, toast]);
  useEffect(() => { load(); }, [load]);

  const voidIt = async (payment: FeePayment) => {
    const reason = window.prompt(`سبب إلغاء الإيصال ${payment.receipt_number}؟`);
    if (!reason) return;
    try {
      await billingService.voidPayment(payment.id, reason);
      toast.success('تم إلغاء الإيصال وإعادة المبلغ للرصيد المتبقي.');
      load();
    } catch (err) {
      toast.error(errorText(err));
    }
  };

  const printReceipt = (payment: FeePayment) => {
    const win = window.open('', '_blank', 'width=480,height=640');
    if (!win) return;
    const doc = win.document;
    doc.title = `إيصال ${payment.receipt_number}`;
    doc.documentElement.dir = 'rtl';
    doc.body.style.fontFamily = 'system-ui, sans-serif';
    doc.body.style.padding = '24px';
    const lines: Array<[string, string]> = [
      ['رقم الإيصال', payment.receipt_number], ['الطالب', payment.student_name], ['البند', payment.fee_title],
      ['المبلغ', formatMoney(payment.amount, payment.currency)], ['طريقة الدفع', PAYMENT_METHOD_LABELS[payment.method]],
      ['التاريخ', payment.paid_on], ['المرجع', payment.reference || '—'],
    ];
    const heading = doc.createElement('h2');
    heading.textContent = 'إيصال استلام';
    doc.body.appendChild(heading);
    lines.forEach(([label, value]) => {
      const line = doc.createElement('p');
      const strong = doc.createElement('strong');
      strong.textContent = `${label}: `;
      line.appendChild(strong);
      line.appendChild(doc.createTextNode(value));
      doc.body.appendChild(line);
    });
    win.print();
  };

  return (
    <div style={{ display: 'grid', gap: '.85rem' }}>
      <div style={row} role="search">
        <label style={field}>بحث
          <input style={input} placeholder="رقم الإيصال أو اسم الطالب" value={search} onChange={(event) => setSearch(event.target.value)} />
        </label>
      </div>
      {!items ? <LoadingSpinner text="تحميل الدفعات..." /> : (
        <ResponsiveTable
          data={items}
          keyExtractor={(item) => item.id}
          emptyMessage="لا توجد دفعات مسجلة."
          columns={[
            { key: 'receipt_number', header: 'الإيصال' },
            { key: 'student_name', header: 'الطالب' },
            { key: 'fee_title', header: 'البند' },
            { key: 'amount', header: 'المبلغ', render: (p) => formatMoney(p.amount, p.currency) },
            { key: 'method', header: 'الطريقة', render: (p) => PAYMENT_METHOD_LABELS[p.method] },
            { key: 'paid_on', header: 'التاريخ' },
            { key: 'status', header: 'الحالة', render: (p) => p.is_void ? <Badge variant="danger">ملغى</Badge> : <Badge variant="success">ساري</Badge> },
            {
              key: 'actions', header: 'إجراءات', render: (p) => (
                <div style={{ display: 'flex', gap: '.35rem', flexWrap: 'wrap' }}>
                  <Button size="sm" variant="outline" leftIcon={<Receipt size={14} />} onClick={() => printReceipt(p)}>طباعة</Button>
                  {!readOnly && !p.is_void && <Button size="sm" variant="danger" onClick={() => voidIt(p)}>إلغاء</Button>}
                </div>
              ),
            },
          ]}
        />
      )}
    </div>
  );
};

/* ---------------- Categories ---------------- */
const Categories: React.FC<{ readOnly: boolean; categories: FeeCategory[]; onChange: () => void }> = ({ readOnly, categories, onChange }) => {
  const toast = useStableToast();
  const [name, setName] = useState('');
  const add = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await billingService.createCategory(name.trim());
      setName('');
      toast.success('تمت إضافة البند.');
      onChange();
    } catch (err) {
      toast.error(errorText(err));
    }
  };
  const toggle = async (category: FeeCategory) => {
    try {
      await billingService.updateCategory(category.id, { is_active: !category.is_active });
      onChange();
    } catch (err) {
      toast.error(errorText(err));
    }
  };
  return (
    <div style={{ display: 'grid', gap: '.85rem' }}>
      {!readOnly && (
        <form style={row} onSubmit={add} aria-label="إضافة بند">
          <label style={field}>اسم البند
            <input style={input} required maxLength={120} placeholder="مثال: رسوم دراسية" value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <Button type="submit" leftIcon={<Plus size={14} />}>إضافة</Button>
        </form>
      )}
      <ResponsiveTable
        data={categories}
        keyExtractor={(item) => item.id}
        emptyMessage="لا توجد بنود بعد."
        columns={[
          { key: 'name', header: 'البند' },
          { key: 'is_active', header: 'الحالة', render: (c) => <Badge variant={c.is_active ? 'success' : 'neutral'}>{c.is_active ? 'مفعّل' : 'موقوف'}</Badge> },
          {
            key: 'actions', header: 'إجراءات', render: (c) => readOnly ? '—' : (
              <Button size="sm" variant="outline" onClick={() => toggle(c)}>{c.is_active ? 'إيقاف' : 'تفعيل'}</Button>
            ),
          },
        ]}
      />
    </div>
  );
};

/* ---------------- Page ---------------- */
export const FeesPage: React.FC = () => {
  const { isReadOnly } = useAuth();
  const [tab, setTab] = useState<Tab>('overview');
  const [categories, setCategories] = useState<FeeCategory[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadCategories = useCallback(() => {
    billingService.categories().then(setCategories).catch(() => setCategories([]));
  }, []);
  useEffect(() => { loadCategories(); }, [loadCategories]);

  const visibleTabs = TABS.filter((item) => !(isReadOnly && item.id === 'issue'));

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <Card>
        <CardHeader>
          <CardTitle>الرسوم المدرسية</CardTitle>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '.9rem' }}>
            إصدار الرسوم والأقساط، تسجيل الدفعات يدويًا، ومتابعة المتأخرات. يرى ولي الأمر المخوّل ماليًا ملخص رسوم أبنائه في التطبيق.
          </p>
        </CardHeader>
        <div role="tablist" aria-label="أقسام الرسوم" style={{ display: 'flex', gap: '.4rem', flexWrap: 'wrap', padding: '0 1rem 1rem' }}>
          {visibleTabs.map((item) => (
            <Button key={item.id} role="tab" aria-selected={tab === item.id} size="sm"
              variant={tab === item.id ? 'primary' : 'outline'} onClick={() => setTab(item.id)}>{item.label}</Button>
          ))}
        </div>
      </Card>
      <Card>
        <div style={panel} role="tabpanel" key={`${tab}-${refreshKey}`}>
          {tab === 'overview' && <Overview />}
          {tab === 'fees' && <FeesList readOnly={isReadOnly} categories={categories} />}
          {tab === 'issue' && <IssueForm categories={categories} onIssued={() => { setRefreshKey((k) => k + 1); setTab('fees'); }} />}
          {tab === 'payments' && <Payments readOnly={isReadOnly} />}
          {tab === 'categories' && <Categories readOnly={isReadOnly} categories={categories} onChange={loadCategories} />}
        </div>
      </Card>
    </div>
  );
};
