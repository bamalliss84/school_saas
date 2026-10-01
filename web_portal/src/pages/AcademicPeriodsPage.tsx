import React, { useCallback, useEffect, useState } from 'react';
import { Edit2, Plus, RotateCw } from 'lucide-react';

import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { EmptyState } from '../components/feedback/EmptyState';
import { LoadingSpinner } from '../components/feedback/LoadingSpinner';
import { useAuth } from '../context/useAuth';
import { useToast } from '../context/useToast';
import { academicService } from '../services/academicService';
import {
  AcademicTerm,
  AcademicTermInput,
  AcademicTermType,
  AcademicYear,
  AcademicYearInput,
} from '../types/academic';

const termTypeLabels: Record<AcademicTermType, string> = {
  term_1: 'الفصل الأول',
  term_2: 'الفصل الثاني',
  term_3: 'الفصل الثالث',
  summer: 'الفصل الصيفي',
};

const overlayStyle: React.CSSProperties = {
  position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(15, 23, 42, 0.45)',
  display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem',
};

const dialogStyle: React.CSSProperties = {
  width: 'min(560px, 100%)', background: '#fff', borderRadius: 'var(--radius-lg)',
  boxShadow: 'var(--shadow-xl)', padding: '1.5rem', display: 'grid', gap: '1rem',
};

const fieldStyle: React.CSSProperties = { display: 'grid', gap: '0.375rem' };

const formatDate = (value: string) => new Intl.DateTimeFormat('ar', {
  year: 'numeric', month: 'short', day: 'numeric',
}).format(new Date(`${value}T00:00:00`));

const errorText = (err: unknown, fallback: string) => err instanceof Error ? err.message : fallback;

export const AcademicPeriodsPage: React.FC = () => {
  const { activeMembership, isReadOnly } = useAuth();
  const { success, error } = useToast();
  const [years, setYears] = useState<AcademicYear[]>([]);
  const [selectedYearId, setSelectedYearId] = useState<number | null>(null);
  const [terms, setTerms] = useState<AcademicTerm[]>([]);
  const [loadingYears, setLoadingYears] = useState(true);
  const [loadingTerms, setLoadingTerms] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [yearDialog, setYearDialog] = useState<AcademicYear | 'new' | null>(null);
  const [termDialog, setTermDialog] = useState<AcademicTerm | 'new' | null>(null);

  const selectedYear = years.find((item) => item.id === selectedYearId) ?? null;

  const loadYears = useCallback(async () => {
    setLoadingYears(true);
    setPageError(null);
    try {
      const response = await academicService.getAcademicYears();
      setYears(response.results);
      setSelectedYearId((current) => {
        if (current && response.results.some((item) => item.id === current)) return current;
        const contextYear = activeMembership?.academic_year?.id;
        return response.results.find((item) => item.id === contextYear)?.id
          ?? response.results[0]?.id
          ?? null;
      });
    } catch (err) {
      const message = errorText(err, 'تعذر تحميل السنوات الدراسية');
      setPageError(message);
      error(message);
    } finally {
      setLoadingYears(false);
    }
  }, [activeMembership?.academic_year?.id, error]);

  const loadTerms = useCallback(async (academicYearId: number) => {
    setLoadingTerms(true);
    try {
      const response = await academicService.getAcademicTerms({ academic_year_id: academicYearId });
      setTerms(response.results);
    } catch (err) {
      const message = errorText(err, 'تعذر تحميل الفصول الدراسية');
      setTerms([]);
      error(message);
    } finally {
      setLoadingTerms(false);
    }
  }, [error]);

  useEffect(() => { loadYears(); }, [activeMembership?.school?.id, loadYears]);
  useEffect(() => {
    if (selectedYearId) loadTerms(selectedYearId);
    else setTerms([]);
  }, [selectedYearId, loadTerms]);

  const saveYear = async (data: AcademicYearInput) => {
    try {
      const saved = yearDialog === 'new'
        ? await academicService.createAcademicYear(data)
        : await academicService.updateAcademicYear(yearDialog!.id, data);
      setYears((current) => yearDialog === 'new'
        ? [saved, ...current]
        : current.map((item) => item.id === saved.id ? saved : item));
      setSelectedYearId(saved.id);
      setYearDialog(null);
      success(yearDialog === 'new' ? 'تم إنشاء السنة الدراسية' : 'تم تحديث السنة الدراسية');
    } catch (err) {
      error(errorText(err, 'تعذر حفظ السنة الدراسية'));
    }
  };

  const saveTerm = async (data: AcademicTermInput) => {
    try {
      const saved = termDialog === 'new'
        ? await academicService.createAcademicTerm(data)
        : await academicService.updateAcademicTerm(termDialog!.id, data);
      setTerms((current) => termDialog === 'new'
        ? [...current, saved].sort((a, b) => a.start_date.localeCompare(b.start_date))
        : current.map((item) => item.id === saved.id ? saved : item));
      setTermDialog(null);
      success(termDialog === 'new' ? 'تم إنشاء الفصل الدراسي' : 'تم تحديث الفصل الدراسي');
    } catch (err) {
      error(errorText(err, 'تعذر حفظ الفصل؛ تحقق من التواريخ وعدم التداخل'));
    }
  };

  return (
    <div style={{ display: 'grid', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800 }}>السنوات والفصول الدراسية</h1>
          <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>
            إدارة التقويم الأكاديمي للمدرسة النشطة دون تغيير سياق التشغيل الحالي.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Button variant="outline" size="sm" onClick={loadYears} leftIcon={<RotateCw size={14} />}>
            تحديث
          </Button>
          {!isReadOnly && (
            <Button size="sm" onClick={() => setYearDialog('new')} leftIcon={<Plus size={15} />}>
              إضافة سنة دراسية
            </Button>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(260px, 0.8fr) minmax(360px, 1.4fr)', gap: '1rem' }}>
        <Card>
          <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-subtle)', fontWeight: 700 }}>
            السنوات الدراسية
          </div>
          {loadingYears ? <div style={{ padding: '3rem' }}><LoadingSpinner /></div>
            : pageError ? <div style={{ padding: '1.5rem', color: 'var(--danger-600)' }}>{pageError}</div>
            : years.length === 0 ? <EmptyState title="لا توجد سنوات دراسية" description="أضف أول سنة دراسية للمدرسة." />
            : <div style={{ display: 'grid' }}>{years.map((year) => (
              <button key={year.id} type="button" onClick={() => setSelectedYearId(year.id)} style={{
                padding: '1rem 1.25rem', border: 0, borderBottom: '1px solid var(--border-subtle)',
                background: selectedYearId === year.id ? 'var(--primary-50)' : '#fff', textAlign: 'right', cursor: 'pointer',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem' }}>
                  <strong>{year.name}</strong>
                  <span style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                    <Badge variant={year.is_active ? 'success' : 'neutral'}>{year.is_active ? 'نشطة' : 'غير نشطة'}</Badge>
                    {!isReadOnly && <span role="button" tabIndex={0} aria-label="تعديل" onClick={(event) => { event.stopPropagation(); setYearDialog(year); }}><Edit2 size={15} /></span>}
                  </span>
                </div>
                <small style={{ color: 'var(--text-secondary)' }}>{formatDate(year.start_date)} — {formatDate(year.end_date)}</small>
              </button>
            ))}</div>}
        </Card>

        <Card>
          <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
            <div><strong>الفصول الدراسية</strong>{selectedYear && <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{selectedYear.name}</div>}</div>
            {!isReadOnly && selectedYear && <Button size="sm" onClick={() => setTermDialog('new')} leftIcon={<Plus size={15} />}>إضافة فصل دراسي</Button>}
          </div>
          <div style={{ padding: '0.75rem 1.25rem', background: 'var(--warning-50)', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
            حالة الفصل إدارية فقط؛ لا يعني تعطيل الفصل استبعاده من مطابقة تاريخ الحضور أو العقود التشغيلية الحالية.
          </div>
          {loadingTerms ? <div style={{ padding: '3rem' }}><LoadingSpinner /></div>
            : !selectedYear ? <EmptyState title="اختر سنة دراسية" description="اختر سنة لعرض فصولها الدراسية." />
            : terms.length === 0 ? <EmptyState title="لا توجد فصول دراسية" description="أضف فصول السنة مع تواريخ غير متداخلة." />
            : <div style={{ display: 'grid' }}>{terms.map((term) => (
              <div key={term.id} style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                <div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}><strong>{term.name}</strong><Badge variant="neutral">{termTypeLabels[term.term_type]}</Badge></div>
                  <small style={{ color: 'var(--text-secondary)' }}>{formatDate(term.start_date)} — {formatDate(term.end_date)}</small>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <Badge variant={term.is_active ? 'success' : 'neutral'}>{term.is_active ? 'متاح إداريًا' : 'غير متاح إداريًا'}</Badge>
                  {!isReadOnly && <button type="button" aria-label="تعديل" onClick={() => setTermDialog(term)} style={{ border: 0, background: 'transparent', cursor: 'pointer' }}><Edit2 size={16} /></button>}
                </div>
              </div>
            ))}</div>}
        </Card>
      </div>

      {yearDialog && <YearDialog value={yearDialog === 'new' ? null : yearDialog} onClose={() => setYearDialog(null)} onSave={saveYear} />}
      {termDialog && selectedYear && <TermDialog value={termDialog === 'new' ? null : termDialog} year={selectedYear} onClose={() => setTermDialog(null)} onSave={saveTerm} />}
    </div>
  );
};

const YearDialog: React.FC<{ value: AcademicYear | null; onClose: () => void; onSave: (data: AcademicYearInput) => Promise<void> }> = ({ value, onClose, onSave }) => {
  const [data, setData] = useState<AcademicYearInput>({ name: value?.name ?? '', start_date: value?.start_date ?? '', end_date: value?.end_date ?? '', is_active: value?.is_active ?? true });
  const [saving, setSaving] = useState(false);
  const submit = async (event: React.FormEvent) => { event.preventDefault(); setSaving(true); try { await onSave(data); } finally { setSaving(false); } };
  return <div style={overlayStyle} role="presentation"><form style={dialogStyle} onSubmit={submit} role="dialog" aria-label="نموذج السنة الدراسية">
    <h2 style={{ margin: 0 }}>{value ? 'تعديل سنة دراسية' : 'إضافة سنة دراسية'}</h2>
    <label style={fieldStyle}>اسم السنة<Input required value={data.name} onChange={(e) => setData({ ...data, name: e.target.value })} /></label>
    <label style={fieldStyle}>تاريخ البداية<Input required type="date" value={data.start_date} onChange={(e) => setData({ ...data, start_date: e.target.value })} /></label>
    <label style={fieldStyle}>تاريخ النهاية<Input required type="date" value={data.end_date} onChange={(e) => setData({ ...data, end_date: e.target.value })} /></label>
    <label><input type="checkbox" checked={data.is_active} onChange={(e) => setData({ ...data, is_active: e.target.checked })} /> نشطة للاختيار في السياق</label>
    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}><Button type="button" variant="outline" onClick={onClose}>إلغاء</Button><Button type="submit" disabled={saving}>{saving ? 'جارٍ الحفظ...' : 'حفظ'}</Button></div>
  </form></div>;
};

const TermDialog: React.FC<{ value: AcademicTerm | null; year: AcademicYear; onClose: () => void; onSave: (data: AcademicTermInput) => Promise<void> }> = ({ value, year, onClose, onSave }) => {
  const [data, setData] = useState<AcademicTermInput>({ academic_year: year.id, name: value?.name ?? '', term_type: value?.term_type ?? 'term_1', start_date: value?.start_date ?? '', end_date: value?.end_date ?? '', is_active: value?.is_active ?? true });
  const [saving, setSaving] = useState(false);
  const submit = async (event: React.FormEvent) => { event.preventDefault(); setSaving(true); try { await onSave(data); } finally { setSaving(false); } };
  return <div style={overlayStyle} role="presentation"><form style={dialogStyle} onSubmit={submit} role="dialog" aria-label="نموذج الفصل الدراسي">
    <h2 style={{ margin: 0 }}>{value ? 'تعديل فصل دراسي' : 'إضافة فصل دراسي'}</h2>
    <div style={{ color: 'var(--text-secondary)' }}>{year.name}</div>
    <label style={fieldStyle}>اسم الفصل<Input required value={data.name} onChange={(e) => setData({ ...data, name: e.target.value })} /></label>
    <label style={fieldStyle}>نوع الفصل<select value={data.term_type} onChange={(e) => setData({ ...data, term_type: e.target.value as AcademicTermType })} style={{ padding: '0.7rem', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)' }}>{Object.entries(termTypeLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
    <label style={fieldStyle}>تاريخ البداية<Input required type="date" min={year.start_date} max={year.end_date} value={data.start_date} onChange={(e) => setData({ ...data, start_date: e.target.value })} /></label>
    <label style={fieldStyle}>تاريخ النهاية<Input required type="date" min={year.start_date} max={year.end_date} value={data.end_date} onChange={(e) => setData({ ...data, end_date: e.target.value })} /></label>
    <label><input type="checkbox" checked={data.is_active} onChange={(e) => setData({ ...data, is_active: e.target.checked })} /> متاح إداريًا</label>
    <small style={{ color: 'var(--text-secondary)' }}>هذا الحقل لا يغيّر مطابقة التاريخ التشغيلية للحضور.</small>
    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}><Button type="button" variant="outline" onClick={onClose}>إلغاء</Button><Button type="submit" disabled={saving}>{saving ? 'جارٍ الحفظ...' : 'حفظ'}</Button></div>
  </form></div>;
};
