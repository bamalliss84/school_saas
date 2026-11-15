import { apiClient } from './apiClient';

export type PaymentState = 'unpaid' | 'partial' | 'paid' | 'overdue' | 'cancelled';
export type PaymentMethod = 'cash' | 'bank_transfer' | 'card' | 'cheque' | 'other';

export interface FeeSummary {
  currency: string | null;
  total: string;
  paid: string;
  remaining: string;
  overdue: string;
  overdue_count: number;
  fee_count: number;
  next_due: { fee_id: number; title: string; due_date: string; balance: string } | null;
  collected_this_month?: string;
  by_category?: Array<FeeSummary & { id: number; name: string }>;
}

export interface FeeCategory { id: number; name: string; description: string; is_active: boolean }

export interface StudentFee {
  id: number;
  student: number;
  student_name: string;
  student_code: string;
  category: number;
  category_name: string;
  title: string;
  amount: string;
  discount: string;
  net_amount: string;
  paid_amount: string;
  balance: string;
  currency: string;
  due_date: string;
  status: 'open' | 'cancelled';
  payment_state: PaymentState;
  cancel_reason: string;
  installment_number: number;
  installment_count: number;
}

export interface FeePayment {
  id: number;
  student_fee: number;
  student_id: number;
  student_name: string;
  fee_title: string;
  amount: string;
  currency: string;
  method: PaymentMethod;
  reference: string;
  paid_on: string;
  receipt_number: string;
  is_void: boolean;
  void_reason: string;
}

export interface Paged<T> { count: number; next: string | null; previous: string | null; results: T[] }

export interface IssuePayload {
  category_id: number;
  title: string;
  amount: string;
  discount?: string;
  due_date?: string;
  installments?: Array<{ amount: string; due_date: string }>;
  scope: 'school' | 'classroom' | 'section' | 'students';
  classroom_id?: number;
  section_id?: number;
  student_ids?: number[];
  confirm: boolean;
}

export interface IssueResult {
  confirmed: boolean;
  created?: number;
  student_count: number;
  installment_count: number;
  amount_per_student: string;
  discount_per_student: string;
  total_net: string;
  students: Array<{ id: number; full_name: string; classroom: string; section: string }>;
}

export interface SubscriptionStatus {
  has_subscription: boolean;
  status: string | null;
  warning: string | null;
  plan?: { id: number; code: string; name: string; billing_period: string; features: string[] };
  start_date?: string;
  end_date?: string;
  days_left?: number;
  student_count: number;
  student_limit?: number | null;
  price_per_student?: string;
  currency?: string;
  outstanding: string;
  invoices?: PlatformInvoice[];
}

export interface PlatformInvoice {
  id: number;
  school: number;
  school_name: string;
  subscription: number;
  number: string;
  period_start: string;
  period_end: string;
  student_count: number;
  amount: string;
  paid_amount: string;
  balance: string;
  currency: string;
  issued_on: string;
  due_date: string;
  status: 'issued' | 'paid' | 'void';
}

export interface Plan {
  id: number;
  code: string;
  name: string;
  description: string;
  base_price: string;
  price_per_student: string;
  currency: string;
  billing_period: 'monthly' | 'termly' | 'yearly';
  max_students: number | null;
  features: string[];
  is_active: boolean;
  sort_order: number;
}

export interface PlatformSchoolRow extends SubscriptionStatus {
  school_id: number;
  school_name: string;
  school_code: string;
  is_active: boolean;
  id?: number;
}

export interface PlatformSummary {
  schools_total: number;
  schools_active: number;
  subscriptions: Record<string, number>;
  schools_without_subscription: number;
  expiring_soon: number;
  outstanding: string;
  overdue: string;
  collected_this_month: string;
  invoiced_this_year: string;
}

type Query = Record<string, string | number | boolean | undefined | null>;

export const billingService = {
  feeSummary: () => apiClient.get<FeeSummary>('/admin/fees/summary/'),
  fees: (params: Query) => apiClient.get<Paged<StudentFee> & { summary: FeeSummary }>('/admin/fees/', { params }),
  feeDetail: (id: number) => apiClient.get<StudentFee & { payments: FeePayment[] }>(`/admin/fees/${id}/`),
  issueFees: (payload: IssuePayload) => apiClient.post<IssueResult>('/admin/fees/issue/', payload),
  cancelFee: (id: number, reason: string) => apiClient.post<StudentFee>(`/admin/fees/${id}/cancel/`, { reason }),
  recordPayment: (id: number, payload: { amount: string; method: PaymentMethod; paid_on?: string; reference?: string }) =>
    apiClient.post<FeePayment>(`/admin/fees/${id}/payments/`, payload),
  payments: (params: Query) => apiClient.get<Paged<FeePayment>>('/admin/fees/payments/', { params }),
  voidPayment: (id: number, reason: string) => apiClient.post<FeePayment>(`/admin/fees/payments/${id}/void/`, { reason }),
  categories: () => apiClient.get<FeeCategory[]>('/admin/fees/categories/'),
  createCategory: (name: string, description = '') =>
    apiClient.post<FeeCategory>('/admin/fees/categories/', { name, description }),
  updateCategory: (id: number, data: Partial<FeeCategory>) =>
    apiClient.patch<FeeCategory>(`/admin/fees/categories/${id}/`, data),
  subscription: () => apiClient.get<SubscriptionStatus>('/admin/subscription/'),

  platformSummary: () => apiClient.get<PlatformSummary>('/platform/summary/', { skipContext: true }),
  platformSchools: (warning?: string) =>
    apiClient.get<{ count: number; results: PlatformSchoolRow[] }>('/platform/schools/', { params: { warning }, skipContext: true }),
  plans: () => apiClient.get<Plan[]>('/platform/plans/', { skipContext: true }),
  createPlan: (data: Partial<Plan>) => apiClient.post<Plan>('/platform/plans/', data, { skipContext: true }),
  updatePlan: (id: number, data: Partial<Plan>) => apiClient.patch<Plan>(`/platform/plans/${id}/`, data, { skipContext: true }),
  createSubscription: (data: Record<string, unknown>) =>
    apiClient.post('/platform/subscriptions/', data, { skipContext: true }),
  updateSubscription: (id: number, data: Record<string, unknown>) =>
    apiClient.patch(`/platform/subscriptions/${id}/`, data, { skipContext: true }),
  platformInvoices: (params: Query) =>
    apiClient.get<Paged<PlatformInvoice>>('/platform/invoices/', { params, skipContext: true }),
  issueInvoice: (data: Record<string, unknown>) =>
    apiClient.post<PlatformInvoice>('/platform/invoices/', data, { skipContext: true }),
  payInvoice: (id: number, data: { amount: string; method: PaymentMethod; reference?: string; paid_on?: string }) =>
    apiClient.post<PlatformInvoice>(`/platform/invoices/${id}/payments/`, data, { skipContext: true }),
  voidInvoice: (id: number, reason: string) =>
    apiClient.post<PlatformInvoice>(`/platform/invoices/${id}/void/`, { reason }, { skipContext: true }),
};

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  cash: 'نقدًا',
  bank_transfer: 'تحويل بنكي',
  card: 'بطاقة',
  cheque: 'شيك',
  other: 'أخرى',
};

export const PAYMENT_STATE_LABELS: Record<PaymentState, string> = {
  unpaid: 'غير مدفوع',
  partial: 'مدفوع جزئيًا',
  paid: 'مدفوع',
  overdue: 'متأخر',
  cancelled: 'ملغى',
};

export const SUBSCRIPTION_STATUS_LABELS: Record<string, string> = {
  trial: 'تجريبي',
  active: 'نشط',
  past_due: 'متأخر السداد',
  suspended: 'موقوف',
  cancelled: 'ملغى',
  expired: 'منتهي',
};

export const formatMoney = (value: string | number | null | undefined, currency?: string | null): string => {
  const number = Number(value ?? 0);
  const text = Number.isFinite(number)
    ? number.toLocaleString('ar', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
    : String(value ?? '');
  return currency ? `${text} ${currency}` : text;
};

export const SUBSCRIPTION_WARNING_TEXT: Record<string, string> = {
  no_subscription: 'لا يوجد اشتراك فعّال للمدرسة. تواصل مع إدارة المنصة لتفعيل الاشتراك.',
  past_due: 'يوجد مبلغ متأخر على اشتراك المدرسة. يرجى السداد لتجنب إيقاف الخدمة.',
  suspended: 'اشتراك المدرسة موقوف. تواصل مع إدارة المنصة.',
  expired: 'انتهى اشتراك المدرسة. يرجى التجديد.',
  trial_ending: 'الفترة التجريبية قاربت على الانتهاء.',
  expiring: 'اشتراك المدرسة قارب على الانتهاء. يرجى التجديد.',
  over_limit: 'عدد الطلاب النشطين تجاوز حد الباقة.',
};
