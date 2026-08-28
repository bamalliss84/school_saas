import React, { useState, useEffect, useCallback } from 'react';
import {
  Plus,
  Search,
  BookOpen,
  Edit2,
  Trash2,
  CheckCircle,
  XCircle,
  RotateCw,
  Building,
} from 'lucide-react';
import { useAuth } from '../context/useAuth';
import { useToast } from '../context/useToast';
import { academicService } from '../services/academicService';
import { Subject, SubjectCreateInput, SubjectUpdateInput } from '../types/academic';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { EmptyState } from '../components/feedback/EmptyState';
import { LoadingSpinner } from '../components/feedback/LoadingSpinner';
import { ConfirmationModal } from '../components/feedback/ConfirmationModal';
import { SubjectModal } from '../components/academic/SubjectModal';

export const SubjectsPage: React.FC = () => {
  const { activeMembership, isReadOnly } = useAuth();
  const { success, error } = useToast();

  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSubject, setEditingSubject] = useState<Subject | null>(null);

  const [deletingSubject, setDeletingSubject] = useState<Subject | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchSubjects = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const is_active = activeFilter === 'all' ? undefined : activeFilter === 'active';
      const res = await academicService.getSubjects({
        search: searchQuery,
        is_active,
      });
      setSubjects(res.results);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'تعذر تحميل المواد الدراسية';
      setErrorMessage(msg);
      error(msg);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, activeFilter, error]);

  useEffect(() => {
    fetchSubjects();
  }, [activeMembership?.school?.id, fetchSubjects]);

  const handleSaveSubject = async (data: SubjectCreateInput | SubjectUpdateInput) => {
    if (editingSubject) {
      const updated = await academicService.updateSubject(editingSubject.id, data);
      setSubjects((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
      success(`تم تحديث المادة "${updated.name}" بنجاح`);
    } else {
      const created = await academicService.createSubject(data as SubjectCreateInput);
      setSubjects((prev) => [created, ...prev]);
      success(`تم إنشاء المادة الدراسية "${created.name}" بنجاح`);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deletingSubject) return;
    setIsDeleting(true);
    try {
      await academicService.deleteSubject(deletingSubject.id);
      setSubjects((prev) => prev.filter((s) => s.id !== deletingSubject.id));
      success(`تم حذف المادة "${deletingSubject.name}" بنجاح`);
      setDeletingSubject(null);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'لا يمكن حذف المادة لأنها مخصصة في منهج صف أو مرتبطة بتكليفات معلمين.';
      error(msg);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Page Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
              المواد الدراسية
            </h1>
            <Badge variant="neutral" icon={<Building size={13} />}>
              دليل المدرسة العام
            </Badge>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0 0' }}>
            إدارة كتالوج المواد الدراسية المعرفة على مستوى المدرسة وتُستخدم عبر الصفوف والمناهج
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchSubjects}
            disabled={isLoading}
            leftIcon={<RotateCw size={14} className={isLoading ? 'animate-spin' : ''} />}
          >
            تحديث
          </Button>

          {!isReadOnly && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setEditingSubject(null);
                setIsModalOpen(true);
              }}
              leftIcon={<Plus size={16} />}
            >
              إضافة مادة دراسية
            </Button>
          )}
        </div>
      </div>

      {/* Filter and Content Card */}
      <Card>
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div style={{ flex: '1 1 280px', maxWidth: '380px' }}>
            <Input
              placeholder="بحث في المواد (الاسم أو الرمز)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              rightIcon={<Search size={16} />}
              style={{ fontSize: '0.875rem' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>الحالة:</span>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                backgroundColor: 'var(--neutral-100)',
                padding: '0.25rem',
                borderRadius: 'var(--radius-md)',
                gap: '0.25rem',
              }}
            >
              <button
                type="button"
                onClick={() => setActiveFilter('all')}
                style={{
                  padding: '0.25rem 0.625rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: activeFilter === 'all' ? '#ffffff' : 'transparent',
                  color: activeFilter === 'all' ? 'var(--primary-700)' : 'var(--text-secondary)',
                  boxShadow: activeFilter === 'all' ? 'var(--shadow-sm)' : 'none',
                }}
              >
                الكل
              </button>
              <button
                type="button"
                onClick={() => setActiveFilter('active')}
                style={{
                  padding: '0.25rem 0.625rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: activeFilter === 'active' ? '#ffffff' : 'transparent',
                  color: activeFilter === 'active' ? 'var(--primary-700)' : 'var(--text-secondary)',
                  boxShadow: activeFilter === 'active' ? 'var(--shadow-sm)' : 'none',
                }}
              >
                النشطة فقط
              </button>
              <button
                type="button"
                onClick={() => setActiveFilter('inactive')}
                style={{
                  padding: '0.25rem 0.625rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: activeFilter === 'inactive' ? '#ffffff' : 'transparent',
                  color: activeFilter === 'inactive' ? 'var(--primary-700)' : 'var(--text-secondary)',
                  boxShadow: activeFilter === 'inactive' ? 'var(--shadow-sm)' : 'none',
                }}
              >
                المعطلة
              </button>
            </div>
          </div>
        </div>

        {/* Table / List Area */}
        {isLoading ? (
          <div style={{ padding: '4rem 2rem', textAlign: 'center' }}>
            <LoadingSpinner size={36} text="جاري تحميل كتالوج المواد الدراسية..." />
          </div>
        ) : errorMessage ? (
          <div style={{ padding: '3rem 2rem', textAlign: 'center', color: 'var(--danger-600)' }}>
            <p>{errorMessage}</p>
            <Button variant="outline" size="sm" onClick={fetchSubjects} style={{ marginTop: '0.75rem' }}>
              إعادة المحاولة
            </Button>
          </div>
        ) : subjects.length === 0 ? (
          <div style={{ padding: '3.5rem 1.5rem' }}>
            <EmptyState
              variant={searchQuery || activeFilter !== 'all' ? 'filtered' : 'default'}
              title={
                searchQuery || activeFilter !== 'all'
                  ? 'لا توجد مواد مطابقة لمعايير البحث'
                  : 'لا توجد مواد دراسية مسجلة'
              }
              description={
                searchQuery || activeFilter !== 'all'
                  ? 'جرّب تغيير عبارة البحث أو إعادة ضبط حالة التصفية.'
                  : 'ابدأ ببناء كتالوج المواد الدراسية المعتمدة للمدرسة لتخصيصها في المناهج وجداول الحصص.'
              }
              actionLabel={!isReadOnly && !searchQuery && activeFilter === 'all' ? 'إضافة مادة' : undefined}
              onAction={() => {
                setEditingSubject(null);
                setIsModalOpen(true);
              }}
              secondaryActionLabel={searchQuery || activeFilter !== 'all' ? 'إعادة ضبط الفلاتر' : undefined}
              onSecondaryAction={() => {
                setSearchQuery('');
                setActiveFilter('all');
              }}
            />
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'right' }}>
              <thead>
                <tr
                  style={{
                    backgroundColor: 'var(--neutral-50)',
                    borderBottom: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                    fontSize: '0.8125rem',
                    fontWeight: 700,
                  }}
                >
                  <th style={{ padding: '1rem 1.5rem' }}>المادة الدراسية</th>
                  <th style={{ padding: '1rem 1.5rem' }}>رمز المادة</th>
                  <th style={{ padding: '1rem 1.5rem' }}>نطاق التعريف</th>
                  <th style={{ padding: '1rem 1.5rem' }}>الحالة</th>
                  {!isReadOnly && <th style={{ padding: '1rem 1.5rem', width: '100px' }}>الإجراءات</th>}
                </tr>
              </thead>
              <tbody>
                {subjects.map((subject) => (
                  <tr
                    key={subject.id}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      transition: 'background-color var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--neutral-50)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <td style={{ padding: '1rem 1.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div
                          style={{
                            width: '34px',
                            height: '34px',
                            borderRadius: 'var(--radius-md)',
                            backgroundColor: 'var(--primary-50)',
                            color: 'var(--primary-700)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '1px solid var(--primary-200)',
                            flexShrink: 0,
                          }}
                        >
                          <BookOpen size={16} />
                        </div>
                        <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>
                          {subject.name}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '1rem 1.5rem' }}>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '0.25rem 0.5rem',
                          borderRadius: 'var(--radius-sm)',
                          backgroundColor: 'var(--neutral-100)',
                          color: 'var(--text-secondary)',
                        }}
                      >
                        {subject.code}
                      </span>
                    </td>
                    <td style={{ padding: '1rem 1.5rem', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                      عام للمدرسة
                    </td>
                    <td style={{ padding: '1rem 1.5rem' }}>
                      {subject.is_active ? (
                        <Badge variant="success" icon={<CheckCircle size={12} />}>
                          نشطة
                        </Badge>
                      ) : (
                        <Badge variant="neutral" icon={<XCircle size={12} />}>
                          معطلة
                        </Badge>
                      )}
                    </td>
                    {!isReadOnly && (
                      <td style={{ padding: '1rem 1.5rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <button
                            type="button"
                            title="تعديل المادة"
                            onClick={() => {
                              setEditingSubject(subject);
                              setIsModalOpen(true);
                            }}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: 'var(--text-muted)',
                              cursor: 'pointer',
                              padding: '0.375rem',
                              borderRadius: 'var(--radius-sm)',
                            }}
                          >
                            <Edit2 size={15} />
                          </button>
                          <button
                            type="button"
                            title="حذف المادة"
                            onClick={() => setDeletingSubject(subject)}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: 'var(--danger-500)',
                              cursor: 'pointer',
                              padding: '0.375rem',
                              borderRadius: 'var(--radius-sm)',
                            }}
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Subject Modal */}
      <SubjectModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleSaveSubject}
        subject={editingSubject}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={Boolean(deletingSubject)}
        onClose={() => setDeletingSubject(null)}
        onConfirm={handleConfirmDelete}
        isLoading={isDeleting}
        title="تأكيد حذف المادة الدراسية"
        message={`هل أنت متأكد من حذف مادة "${deletingSubject?.name}"؟ سيتم التحقق من عدم وجود مناهج أو تكليفات تدريسية مرتبطة بهذه المادة.`}
        confirmLabel="تأكيد الحذف"
        cancelLabel="إلغاء"
        variant="danger"
      />
    </div>
  );
};
