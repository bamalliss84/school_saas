import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { CheckCircle2, ClipboardCheck, History, RefreshCw, RotateCcw, Send, XCircle } from 'lucide-react';
import { useAuth } from '../context/useAuth';
import { useToast } from '../context/useToast';
import { ApiError } from '../services/apiClient';
import { examService } from '../services/examService';
import { Exam, ExamResult, ExamResultLog } from '../types/exams';
import { Badge, Button, Card, CardBody, CardHeader, CardSubtitle, CardTitle, PageHeader } from '../components/ui';
import { EmptyState, ErrorAlert } from '../components/feedback';
import { ConfirmationModal } from '../components/feedback/ConfirmationModal';

const workflowLabels = { draft: 'مسودة', submitted: 'بانتظار الاعتماد', approved: 'معتمد', rejected: 'مرفوض' };
const resultLabels = { not_graded: 'غير مرصود', present: 'حاضر', absent: 'غائب', excused: 'غياب بعذر', exempted: 'معفى' };
const examLabels = { draft: 'مسودة', published: 'منشور', closed: 'مغلق', cancelled: 'ملغي' };
const actionLabels: Record<string, string> = { create: 'إنشاء', update: 'تعديل', submit: 'إرسال للاعتماد', approve: 'اعتماد', reject: 'رفض', reopen: 'إعادة فتح', publish: 'نشر', unpublish: 'إلغاء نشر' };

const errorMessage = (error: unknown) => error instanceof ApiError ? error.message : error instanceof Error ? error.message : 'حدث خطأ غير متوقع';

export const ExamsPage: React.FC = () => {
  const { activeMembership, isReadOnly } = useAuth();
  const toast = useToast();
  const membershipId = activeMembership?.membership_id;
  const [exams, setExams] = useState<Exam[]>([]);
  const [selectedExam, setSelectedExam] = useState<Exam | null>(null);
  const [results, setResults] = useState<ExamResult[]>([]);
  const [logs, setLogs] = useState<Record<number, ExamResultLog[]>>({});
  const [loading, setLoading] = useState(true);
  const [loadingResults, setLoadingResults] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingOnly, setPendingOnly] = useState(false);
  const [query, setQuery] = useState('');
  const [action, setAction] = useState<{ type: 'approve' | 'reject' | 'reopen'; result: ExamResult } | null>(null);
  const [reason, setReason] = useState('');
  const [mutating, setMutating] = useState<number | null>(null);

  const loadExams = useCallback(async () => {
    setLoading(true); setError(null); setSelectedExam(null); setResults([]); setLogs({});
    try {
      const response = await examService.getExams({ academic_year_id: activeMembership?.academic_year?.id });
      setExams(response.results);
    } catch (err) { setError(errorMessage(err)); setExams([]); }
    finally { setLoading(false); }
  }, [activeMembership?.academic_year?.id]);

  useEffect(() => { void loadExams(); }, [loadExams, membershipId]);

  const openExam = async (exam: Exam) => {
    setSelectedExam(exam); setResults([]); setLogs({}); setLoadingResults(true); setError(null);
    try {
      const response = await examService.getResults({ exam_id: exam.id });
      setResults(response.results);
    } catch (err) { setError(errorMessage(err)); }
    finally { setLoadingResults(false); }
  };

  const replaceResult = (updated: ExamResult) => setResults((current) => current.map((item) => item.id === updated.id ? updated : item));

  const confirmWorkflow = async () => {
    if (!action || (action.type === 'reject' && !reason.trim())) return;
    setMutating(action.result.id);
    try {
      const updated = action.type === 'approve'
        ? await examService.approveResult(action.result.id, reason.trim() || undefined)
        : action.type === 'reject'
          ? await examService.rejectResult(action.result.id, reason.trim())
          : await examService.reopenResult(action.result.id, reason.trim() || undefined);
      replaceResult(updated);
      toast.success(action.type === 'approve' ? 'تم اعتماد النتيجة' : action.type === 'reject' ? 'تم رفض النتيجة وإعادتها للمسودة' : 'تمت إعادة فتح النتيجة');
      setAction(null); setReason('');
    } catch (err) { toast.error(errorMessage(err)); }
    finally { setMutating(null); }
  };

  const togglePublication = async () => {
    if (!selectedExam) return;
    setMutating(-1);
    try {
      const hasPublished = results.some((result) => result.is_published);
      const summary = hasPublished ? await examService.unpublishExam(selectedExam.id) : await examService.publishExam(selectedExam.id);
      setResults((current) => current.map((item) => summary.results.find((row) => row.id === item.id) ?? item));
      toast.success(hasPublished ? 'تم إلغاء نشر النتائج' : 'تم نشر النتائج المعتمدة');
      const refreshed = await examService.getResults({ exam_id: selectedExam.id });
      setResults(refreshed.results);
    } catch (err) { toast.error(errorMessage(err)); }
    finally { setMutating(null); }
  };

  const loadLogs = async (resultId: number) => {
    if (logs[resultId]) { setLogs((current) => { const next = { ...current }; delete next[resultId]; return next; }); return; }
    try {
      setLogs((current) => ({ ...current, [resultId]: [] }));
      const entries = await examService.getResultLogs(resultId);
      setLogs((current) => ({ ...current, [resultId]: entries }));
    }
    catch (err) { toast.error(errorMessage(err)); setLogs((current) => { const next = { ...current }; delete next[resultId]; return next; }); }
  };

  const visibleExams = useMemo(() => exams.filter((exam) => exam.title.toLowerCase().includes(query.toLowerCase())), [exams, query]);
  const visibleResults = pendingOnly ? results.filter((result) => result.workflow_status === 'submitted') : results;
  const published = results.some((result) => result.is_published);
  const canPublish = !isReadOnly && results.some((result) => result.workflow_status === 'approved');

  return <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
    <PageHeader title="الاختبارات والنتائج" description="مراجعة نتائج السياق الأكاديمي النشط واعتمادها ونشرها" />
    {isReadOnly && <ErrorAlert variant="info" title="السياق التاريخي للقراءة فقط" message="يمكنك استعراض الاختبارات والنتائج والسجل، ولا يمكن تنفيذ تغييرات." />}
    {error && <ErrorAlert title="تعذر تحميل الاختبارات" message={error} />}
    <Card><CardBody>
      <div style={{ display: 'flex', gap: '.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <input aria-label="بحث الاختبارات" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="ابحث باسم الاختبار" className="input" style={{ minWidth: 240 }} />
        <label style={{ display: 'flex', gap: '.4rem', alignItems: 'center' }}><input type="checkbox" checked={pendingOnly} onChange={(e) => setPendingOnly(e.target.checked)} /> النتائج بانتظار الاعتماد</label>
        <Button variant="outline" size="sm" onClick={() => void loadExams()} leftIcon={<RefreshCw size={14} />}>تحديث</Button>
      </div>
    </CardBody></Card>
    {loading ? <Card><CardBody><p>جاري تحميل الاختبارات...</p></CardBody></Card> : visibleExams.length === 0 ?
      <Card><CardBody><EmptyState title="لا توجد اختبارات في هذا السياق" description="لم تُسجل اختبارات للسنة الأكاديمية النشطة." actionLabel="إعادة المحاولة" onAction={() => void loadExams()} /></CardBody></Card> :
      <Card><CardHeader><div><CardTitle>قائمة الاختبارات</CardTitle><CardSubtitle>{visibleExams.length} اختبار</CardSubtitle></div></CardHeader><CardBody>
        <div className="responsive-table-container"><table className="responsive-table"><thead><tr><th>الاختبار</th><th>التاريخ</th><th>الدرجة</th><th>الحالة</th><th></th></tr></thead><tbody>{visibleExams.map((item) => <tr key={item.id}>
          <td><button onClick={() => void openExam(item)} style={{ border: 0, background: 'none', color: 'var(--primary-700)', cursor: 'pointer', fontWeight: 700 }}>{item.title}</button></td>
          <td>{new Date(item.exam_date).toLocaleDateString('ar')}</td><td>{item.total_marks}</td><td><Badge>{examLabels[item.status]}</Badge></td>
          <td><Button size="sm" variant="outline" onClick={() => void openExam(item)}>فتح التفاصيل</Button></td>
        </tr>)}</tbody></table></div>
      </CardBody></Card>}
    {selectedExam && <Card><CardHeader><div><CardTitle>{selectedExam.title}</CardTitle><CardSubtitle>{selectedExam.notes || 'لا توجد ملاحظات'} · {selectedExam.exam_date}</CardSubtitle></div>
      {!isReadOnly && results.length > 0 && <Button size="sm" variant={published ? 'outline' : 'primary'} disabled={!published && !canPublish} isLoading={mutating === -1} onClick={() => void togglePublication()} leftIcon={published ? <RotateCcw size={14} /> : <Send size={14} />}>{published ? 'إلغاء النشر' : 'نشر النتائج المعتمدة'}</Button>}
    </CardHeader><CardBody>
      {loadingResults ? <p>جاري تحميل سجل النتائج...</p> : visibleResults.length === 0 ? <EmptyState title={pendingOnly ? 'لا توجد نتائج بانتظار الاعتماد' : 'لا توجد نتائج لهذا الاختبار'} /> :
      <div className="responsive-table-container"><table className="responsive-table"><thead><tr><th>الطالب</th><th>الحالة</th><th>الدرجة</th><th>سير العمل</th><th>النشر</th><th>الإجراءات</th></tr></thead><tbody>{visibleResults.map((result) => <React.Fragment key={result.id}><tr>
        <td><strong>{result.student_name}</strong><div style={{ color: 'var(--text-secondary)', fontSize: '.75rem' }}>{result.student_code}</div></td>
        <td>{resultLabels[result.status]}</td><td>{result.score === null ? '—' : `${Number(result.score).toString()} / ${result.total_marks}`}</td>
        <td><Badge variant={result.workflow_status === 'approved' ? 'success' : result.workflow_status === 'submitted' ? 'warning' : 'neutral'}>{workflowLabels[result.workflow_status]}</Badge>{result.approval_reason && <div style={{ fontSize: '.75rem', marginTop: '.25rem' }}>{result.approval_reason}</div>}</td>
        <td><Badge variant={result.is_published ? 'success' : 'neutral'}>{result.is_published ? 'منشورة' : 'غير منشورة'}</Badge></td>
        <td><div style={{ display: 'flex', gap: '.35rem', flexWrap: 'wrap' }}>
          {!isReadOnly && result.workflow_status === 'submitted' && <><Button size="sm" onClick={() => { setAction({ type: 'approve', result }); setReason(''); }} leftIcon={<CheckCircle2 size={13} />}>اعتماد</Button><Button size="sm" variant="danger" onClick={() => { setAction({ type: 'reject', result }); setReason(''); }} leftIcon={<XCircle size={13} />}>رفض</Button></>}
          {!isReadOnly && result.workflow_status === 'approved' && <Button size="sm" variant="outline" onClick={() => { setAction({ type: 'reopen', result }); setReason(''); }} leftIcon={<RotateCcw size={13} />}>إعادة فتح</Button>}
          <Button size="sm" variant="outline" onClick={() => void loadLogs(result.id)} leftIcon={<History size={13} />}>السجل</Button>
        </div></td>
      </tr>{logs[result.id] && <tr><td colSpan={6}><div style={{ padding: '.75rem', background: 'var(--neutral-50)', borderRadius: 'var(--radius-md)' }}><strong>سجل التغييرات</strong>{logs[result.id].length === 0 ? <p>لا توجد أحداث مسجلة.</p> : <ul>{logs[result.id].map((log) => <li key={log.id}>{actionLabels[log.action]} · {new Date(log.changed_at).toLocaleString('ar')}{log.reason ? ` · ${log.reason}` : ''}</li>)}</ul>}</div></td></tr>}</React.Fragment>)}</tbody></table></div>}
    </CardBody></Card>}
    <ConfirmationModal isOpen={Boolean(action && action.type !== 'reject')} onClose={() => setAction(null)} onConfirm={() => void confirmWorkflow()} isLoading={Boolean(action && mutating === action.result.id)} title={action?.type === 'approve' ? 'اعتماد النتيجة' : 'إعادة فتح النتيجة'} message={action?.type === 'approve' ? 'سيتم اعتماد النتيجة وإتاحتها للنشر لاحقًا.' : 'ستعود النتيجة إلى المسودة، وسيُلغي الخادم نشرها إن كانت منشورة.'} confirmLabel={action?.type === 'approve' ? 'تأكيد الاعتماد' : 'تأكيد إعادة الفتح'} variant="warning" />
    {action?.type === 'reject' && <div className="modal-overlay" role="dialog" aria-modal="true" style={{ position: 'fixed', inset: 0, zIndex: 9999, background: 'rgba(15,23,42,.65)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}><Card style={{ width: '100%', maxWidth: 420 }}><CardHeader><div><CardTitle>رفض النتيجة</CardTitle><CardSubtitle>تعاد النتيجة إلى المسودة وفق عقد الخادم.</CardSubtitle></div></CardHeader><CardBody>
      <label htmlFor="reject-reason" style={{ display: 'block', fontWeight: 700, marginBottom: '.35rem' }}>سبب الرفض</label><textarea id="reject-reason" className="input" value={reason} onChange={(e) => setReason(e.target.value)} style={{ width: '100%', minHeight: 90 }} />
      <div style={{ display: 'flex', gap: '.5rem', marginTop: '1rem' }}><Button variant="danger" disabled={!reason.trim()} isLoading={mutating === action.result.id} onClick={() => void confirmWorkflow()} leftIcon={<ClipboardCheck size={14} />}>تأكيد الرفض</Button><Button variant="outline" onClick={() => setAction(null)}>إلغاء</Button></div>
    </CardBody></Card></div>}
  </div>;
};
