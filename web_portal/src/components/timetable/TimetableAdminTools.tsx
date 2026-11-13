import React, { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../../services/apiClient';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Conflict, timetableConflicts } from '../../utils/timetable';

type Row = Record<string, unknown>;
type Period = { id: number; name: string; sequence: number; start_time: string; end_time: string; kind: string; is_active: boolean };
type Notify = { success: (m: string) => void; error: (m: string) => void };

const WEEKDAYS: [number, string][] = [
  [0, 'الأحد'], [1, 'الاثنين'], [2, 'الثلاثاء'], [3, 'الأربعاء'], [4, 'الخميس'], [5, 'الجمعة'], [6, 'السبت'],
];
const dayName = (value: number) => WEEKDAYS.find(([v]) => v === value)?.[1] ?? String(value);

const panel: React.CSSProperties = { padding: '1rem', display: 'grid', gap: '.75rem' };
const row: React.CSSProperties = { display: 'flex', gap: '.65rem', flexWrap: 'wrap', alignItems: 'end' };
const input: React.CSSProperties = {
  minHeight: 38, padding: '.45rem .65rem', border: '1px solid var(--border-subtle)',
  borderRadius: 'var(--radius-md)', background: 'var(--surface-primary)', color: 'var(--text-primary)',
};
const label: React.CSSProperties = { display: 'grid', gap: '.35rem', fontWeight: 600 };

const message = (e: unknown) => (e instanceof Error ? e.message : 'تعذر تنفيذ العملية');
const asList = <T,>(value: unknown): T[] =>
  Array.isArray(value) ? (value as T[]) : (((value as Row)?.results as T[]) || []);

const conflictText: Record<string, string> = {
  teacher_conflict: 'المعلم لديه حصة أخرى في هذه الفترة',
  class_section_conflict: 'الشعبة لديها حصة أخرى في هذه الفترة',
  exact_duplicate: 'هذه الحصة موجودة مسبقًا',
  invalid_cell: 'خلية غير صالحة',
};

export const ConflictList: React.FC<{ conflicts: Conflict[] }> = ({ conflicts }) =>
  conflicts.length ? (
    <div role="alert" style={{ color: 'var(--danger-600)', display: 'grid', gap: '.25rem' }}>
      <strong>تعارضات في الجدول ({conflicts.length}) — لم يُحفظ أي تغيير</strong>
      {conflicts.map((c, i) => (
        <span key={i}>
          {c.weekday !== undefined ? dayName(c.weekday) + ': ' : ''}
          {(c.code && conflictText[c.code]) || c.message || 'تعارض'}
        </span>
      ))}
    </div>
  ) : null;

/** F1F-1: working days and periods setup. */
export const TimetableSetupPanel: React.FC<{ notify: Notify; onChanged: () => void }> = ({ notify, onChanged }) => {
  const [open, setOpen] = useState(false);
  const [workingDays, setWorkingDays] = useState<number[]>([]);
  const [periods, setPeriods] = useState<Period[]>([]);
  const [draft, setDraft] = useState({ name: '', sequence: '', start_time: '', end_time: '', kind: 'lesson' });

  const refresh = useCallback(async () => {
    try {
      const [config, list] = await Promise.all([
        apiClient.get<Row>('/timetable/config/'),
        apiClient.get<unknown>('/timetable/periods/', { params: { page_size: 100 } }),
      ]);
      setWorkingDays(((config?.working_days as number[]) || []).slice().sort());
      setPeriods(asList<Period>(list).slice().sort((a, b) => a.sequence - b.sequence));
    } catch (e) {
      notify.error(message(e));
    }
  }, [notify]);

  useEffect(() => { if (open) refresh(); }, [open, refresh]);

  const run = async (work: () => Promise<unknown>, done: string) => {
    try {
      await work();
      notify.success(done);
      await refresh();
      onChanged();
      return true;
    } catch (e) {
      notify.error(message(e));
      return false;
    }
  };

  const toggleDay = (day: number) =>
    setWorkingDays((days) => (days.includes(day) ? days.filter((d) => d !== day) : [...days, day].sort()));

  const addPeriod = async () => {
    if (!draft.name || draft.sequence === '' || !draft.start_time || !draft.end_time) {
      return notify.error('أكمل اسم الفترة وترتيبها ووقت البداية والنهاية');
    }
    if (draft.end_time <= draft.start_time) return notify.error('وقت النهاية يجب أن يكون بعد وقت البداية');
    const ok = await run(() => apiClient.post('/timetable/periods/', { ...draft, sequence: Number(draft.sequence) }), 'تمت إضافة الفترة');
    if (ok) setDraft({ name: '', sequence: '', start_time: '', end_time: '', kind: 'lesson' });
  };

  return (
    <Card>
      <div style={panel}>
        <div style={row}>
          <Button variant="outline" onClick={() => setOpen((v) => !v)}>
            {open ? 'إخفاء إعداد الأيام والفترات' : 'إعداد الأيام والفترات'}
          </Button>
        </div>
        {open && (
          <>
            <fieldset style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', display: 'flex', gap: '.75rem', flexWrap: 'wrap' }}>
              <legend>أيام العمل</legend>
              {WEEKDAYS.map(([value, name]) => (
                <label key={value}>
                  <input type="checkbox" checked={workingDays.includes(value)} onChange={() => toggleDay(value)} /> {name}
                </label>
              ))}
              <Button size="sm" onClick={() => {
                if (!workingDays.length) return notify.error('اختر يوم عمل واحدًا على الأقل');
                run(() => apiClient.put('/timetable/config/', { working_days: workingDays }), 'تم حفظ أيام العمل');
              }}>حفظ أيام العمل</Button>
            </fieldset>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }} aria-label="الفترات">
                <thead><tr><th>الترتيب</th><th>الفترة</th><th>الوقت</th><th>النوع</th><th /></tr></thead>
                <tbody>
                  {periods.map((p) => (
                    <tr key={p.id}>
                      <td>{p.sequence}</td><td>{p.name}</td><td>{p.start_time?.slice(0, 5)} - {p.end_time?.slice(0, 5)}</td>
                      <td>{p.kind === 'break' ? 'استراحة' : 'حصة'}</td>
                      <td><Button size="sm" variant="danger" onClick={() => { if (window.confirm('حذف الفترة ' + p.name + '؟')) run(() => apiClient.delete('/timetable/periods/' + p.id + '/'), 'تم حذف الفترة'); }}>حذف</Button></td>
                    </tr>
                  ))}
                  {!periods.length && <tr><td colSpan={5}>لا توجد فترات بعد.</td></tr>}
                </tbody>
              </table>
            </div>
            <div style={row}>
              <label style={label}>اسم الفترة<input style={input} value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} /></label>
              <label style={label}>الترتيب<input style={input} type="number" min={0} value={draft.sequence} onChange={(e) => setDraft({ ...draft, sequence: e.target.value })} /></label>
              <label style={label}>البداية<input style={input} type="time" value={draft.start_time} onChange={(e) => setDraft({ ...draft, start_time: e.target.value })} /></label>
              <label style={label}>النهاية<input style={input} type="time" value={draft.end_time} onChange={(e) => setDraft({ ...draft, end_time: e.target.value })} /></label>
              <label style={label}>النوع<select style={input} value={draft.kind} onChange={(e) => setDraft({ ...draft, kind: e.target.value })}><option value="lesson">حصة</option><option value="break">استراحة</option></select></label>
              <Button onClick={addPeriod}>إضافة فترة</Button>
            </div>
            <small>لا يمكن حذف فترة مستخدمة في الجدول أو تحويلها إلى استراحة؛ يرفض الخادم ذلك.</small>
          </>
        )}
      </div>
    </Card>
  );
};

/** F1F-5: copy a day within the section, or the whole week to another section, with preview first. */
export const TimetableCopyPanel: React.FC<{
  classId?: number; sectionId?: number; sections: Row[]; days: Row[]; notify: Notify; onChanged: () => void;
}> = ({ classId, sectionId, sections, days, notify, onChanged }) => {
  const [mode, setMode] = useState<'day' | 'week'>('day');
  const [source, setSource] = useState('');
  const [target, setTarget] = useState('');
  const [targetSection, setTargetSection] = useState('');
  const [clearTarget, setClearTarget] = useState(false);
  const [preview, setPreview] = useState<Row | null>(null);
  const [conflicts, setConflicts] = useState<Conflict[]>([]);

  const body = (validateOnly: boolean) => ({
    source_classroom_id: classId, source_section_id: sectionId,
    target_classroom_id: classId,
    target_section_id: mode === 'week' ? Number(targetSection) : sectionId,
    ...(mode === 'day' ? { source_weekday: Number(source), target_weekday: Number(target) } : {}),
    clear_target: clearTarget, validate_only: validateOnly,
  });

  const submit = async (validateOnly: boolean) => {
    if (!classId || !sectionId) return notify.error('اختر الصف والشعبة المصدر أولًا');
    if (mode === 'day' && (source === '' || target === '' || source === target)) return notify.error('اختر يومين مختلفين للنسخ');
    if (mode === 'week' && (!targetSection || Number(targetSection) === sectionId)) return notify.error('اختر شعبة هدف مختلفة');
    setConflicts([]);
    try {
      const result = await apiClient.post<Row>('/timetable/copy-' + mode + '/', body(validateOnly));
      if (validateOnly) {
        setPreview(result);
        setConflicts(result?.valid === false ? timetableConflicts(result) : []);
      } else {
        notify.success('تم نسخ الجدول');
        setPreview(null);
        onChanged();
      }
    } catch (e) {
      const list = timetableConflicts((e as { errors?: unknown })?.errors);
      setConflicts(list);
      if (!list.length) notify.error(message(e));
    }
  };

  const reset = () => { setPreview(null); setConflicts([]); };

  return (
    <Card>
      <div style={panel}>
        <strong>نسخ الجدول</strong>
        <div style={row}>
          <label style={label}>نوع النسخ<select style={input} value={mode} onChange={(e) => { setMode(e.target.value as 'day' | 'week'); reset(); }}><option value="day">نسخ يوم إلى يوم</option><option value="week">نسخ الأسبوع إلى شعبة أخرى</option></select></label>
          {mode === 'day' ? (
            <>
              <label style={label}>من يوم<select style={input} value={source} onChange={(e) => { setSource(e.target.value); reset(); }}><option value="">اختر</option>{days.map((d) => <option key={String(d.value)} value={String(d.value)}>{dayName(Number(d.value))}</option>)}</select></label>
              <label style={label}>إلى يوم<select style={input} value={target} onChange={(e) => { setTarget(e.target.value); reset(); }}><option value="">اختر</option>{days.map((d) => <option key={String(d.value)} value={String(d.value)}>{dayName(Number(d.value))}</option>)}</select></label>
            </>
          ) : (
            <label style={label}>الشعبة الهدف<select style={input} value={targetSection} onChange={(e) => { setTargetSection(e.target.value); reset(); }}><option value="">اختر</option>{sections.filter((s) => s.id !== sectionId).map((s) => <option key={String(s.id)} value={String(s.id)}>{String(s.name)}</option>)}</select></label>
          )}
          <label><input type="checkbox" checked={clearTarget} onChange={(e) => { setClearTarget(e.target.checked); reset(); }} /> مسح حصص الهدف أولًا</label>
          <Button variant="outline" onClick={() => submit(true)}>معاينة النسخ</Button>
          {preview?.valid === true && <Button onClick={() => submit(false)}>تأكيد النسخ</Button>}
        </div>
        {preview?.valid === true && <span role="status">المعاينة صالحة: {String(preview.valid_cells ?? 0)} حصة جاهزة للنسخ.</span>}
        <ConflictList conflicts={conflicts} />
      </div>
    </Card>
  );
};
