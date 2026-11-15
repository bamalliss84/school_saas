import React, { useEffect, useState } from 'react';
import { Badge, Card, CardHeader, CardTitle, ResponsiveTable } from '../components/ui';
import { EmptyState, LoadingSpinner } from '../components/feedback';
import { Kpi } from './FeesPage';
import {
  billingService,
  formatMoney,
  SUBSCRIPTION_STATUS_LABELS,
  SUBSCRIPTION_WARNING_TEXT,
  type SubscriptionStatus,
} from '../services/billingService';


const PERIOD_LABELS: Record<string, string> = { monthly: 'شهري', termly: 'فصلي', yearly: 'سنوي' };

const statusVariant = (status: string | null) =>
  status === 'active' ? 'success' : status === 'trial' ? 'primary' : status === 'past_due' ? 'warning' : 'danger';

export const SubscriptionPage: React.FC = () => {
  const [data, setData] = useState<SubscriptionStatus | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    billingService.subscription().then(setData).catch(() => setFailed(true));
  }, []);

  if (failed) return <EmptyState title="تعذر تحميل بيانات الاشتراك" description="حاول مرة أخرى لاحقًا." />;
  if (!data) return <LoadingSpinner text="تحميل الاشتراك..." />;

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <Card>
        <CardHeader>
          <CardTitle>اشتراك المدرسة في المنصة</CardTitle>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '.9rem' }}>
            تُدار الباقات والفواتير من إدارة المنصة. هذه الصفحة للاطلاع فقط.
          </p>
        </CardHeader>
        <div style={{ padding: '0 1rem 1rem', display: 'grid', gap: '1rem' }}>
          {data.warning && (
            <div role="alert" style={{
              padding: '.75rem 1rem', borderRadius: 'var(--radius-md)',
              background: 'var(--warning-50, #fffbeb)', color: 'var(--warning-800, #92400e)', border: '1px solid var(--warning-200, #fde68a)',
            }}>
              {SUBSCRIPTION_WARNING_TEXT[data.warning] || data.warning}
            </div>
          )}
          {data.has_subscription && data.plan ? (
            <div style={{ display: 'grid', gap: '.75rem', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))' }}>
              <Kpi label="الباقة" value={data.plan.name} hint={PERIOD_LABELS[data.plan.billing_period] || data.plan.billing_period} />
              <div style={{ display: 'grid', gap: '.35rem', padding: '.9rem 1rem', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)' }}>
                <span style={{ fontSize: '.8rem', color: 'var(--text-secondary)' }}>الحالة</span>
                <span><Badge variant={statusVariant(data.status)}>{SUBSCRIPTION_STATUS_LABELS[data.status || ''] || data.status}</Badge></span>
              </div>
              <Kpi label="ينتهي في" value={data.end_date || '—'} hint={data.days_left !== undefined ? `متبقٍ ${data.days_left} يوم` : undefined} />
              <Kpi label="الطلاب النشطون" value={String(data.student_count)}
                hint={data.student_limit ? `الحد ${data.student_limit}` : 'بدون حد'} />
              <Kpi label="المستحق للمنصة" value={formatMoney(data.outstanding, data.currency)} />
            </div>
          ) : null}
          {data.plan?.features && data.plan.features.length > 0 && (
            <div>
              <strong>مزايا الباقة</strong>
              <ul style={{ margin: '.4rem 0 0', paddingInlineStart: '1.25rem' }}>
                {data.plan.features.map((feature) => <li key={feature}>{feature}</li>)}
              </ul>
            </div>
          )}
        </div>
      </Card>
      <Card>
        <CardHeader><CardTitle>فواتير الاشتراك</CardTitle></CardHeader>
        <div style={{ padding: '0 1rem 1rem' }}>
          <ResponsiveTable
            data={data.invoices || []}
            keyExtractor={(item) => item.id}
            emptyMessage="لا توجد فواتير."
            columns={[
              { key: 'number', header: 'رقم الفاتورة' },
              { key: 'period', header: 'الفترة', render: (inv) => `${inv.period_start} → ${inv.period_end}` },
              { key: 'amount', header: 'المبلغ', render: (inv) => formatMoney(inv.amount, inv.currency) },
              { key: 'balance', header: 'المتبقي', render: (inv) => formatMoney(inv.balance, inv.currency) },
              { key: 'due_date', header: 'الاستحقاق' },
              {
                key: 'status', header: 'الحالة', render: (inv) => (
                  <Badge variant={inv.status === 'paid' ? 'success' : inv.status === 'void' ? 'neutral' : 'warning'}>
                    {inv.status === 'paid' ? 'مدفوعة' : inv.status === 'void' ? 'ملغاة' : 'مستحقة'}
                  </Badge>
                ),
              },
            ]}
          />
        </div>
      </Card>
    </div>
  );
};
