import React, { useState, useEffect } from 'react';
import { X, BookOpen } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { ClassSubject, Classroom, Subject } from '../../types/academic';

export interface ClassSubjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { classroom: number; subject: number; weekly_periods: number }) => Promise<void>;
  classroom: Classroom;
  availableSubjects: Subject[];
  assignedSubjects: ClassSubject[];
  editingItem?: ClassSubject | null;
  isLoading?: boolean;
}

export const ClassSubjectModal: React.FC<ClassSubjectModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  classroom,
  availableSubjects,
  assignedSubjects,
  editingItem,
  isLoading = false,
}) => {
  const isEditing = Boolean(editingItem);
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | ''>('');
  const [weeklyPeriods, setWeeklyPeriods] = useState<number>(4);
  const [error, setError] = useState<string | null>(null);

  const assignedSubjectIds = new Set(assignedSubjects.map((s) => s.subject));

  // Filter available subjects (exclude already assigned, except when editing)
  const selectableSubjects = isEditing
    ? availableSubjects
    : availableSubjects.filter((s) => !assignedSubjectIds.has(s.id));

  useEffect(() => {
    if (editingItem) {
      setSelectedSubjectId(editingItem.subject);
      setWeeklyPeriods(editingItem.weekly_periods);
    } else {
      setSelectedSubjectId(selectableSubjects[0]?.id || '');
      setWeeklyPeriods(4);
    }
    setError(null);
  }, [editingItem, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedSubjectId) {
      setError('يرجى اختيار المادة الدراسية');
      return;
    }

    if (!weeklyPeriods || weeklyPeriods < 1) {
      setError('يرجى تحديد عدد الحصص الأسبوعية بشكل صحيح (1 على الأقل)');
      return;
    }

    try {
      setError(null);
      await onSubmit({
        classroom: classroom.id,
        subject: Number(selectedSubjectId),
        weekly_periods: Number(weeklyPeriods),
      });
      onClose();
    } catch (err: unknown) {
      if (typeof err === 'object' && err !== null && 'message' in err) {
        setError((err as { message: string }).message);
      } else {
        setError('حدث خطأ أثناء حفظ التخصيص الدراسي للمادة.');
      }
    }
  };

  return (
    <div
      className="modal-overlay"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '480px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          borderRadius: 'var(--radius-xl)',
          overflow: 'hidden',
          animation: 'modalPop 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--primary-50)',
                color: 'var(--primary-600)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid var(--primary-200)',
              }}
            >
              <BookOpen size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                {isEditing ? 'تعديل نصاب المادة في المنهج' : 'إدراج مادة في منهج الصف'}
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '0.125rem 0 0 0' }}>
                الصف: <strong style={{ color: 'var(--text-primary)' }}>{classroom.name}</strong>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '0.25rem',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {error && (
              <div
                style={{
                  padding: '0.75rem 1rem',
                  backgroundColor: 'var(--danger-50)',
                  border: '1px solid var(--danger-200)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--danger-700)',
                  fontSize: '0.8125rem',
                }}
              >
                {error}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="select-subject" className="form-label">
                المادة الدراسية *
              </label>
              <select
                id="select-subject"
                className="form-select"
                value={selectedSubjectId}
                onChange={(e) => setSelectedSubjectId(Number(e.target.value))}
                disabled={isEditing || selectableSubjects.length === 0}
                style={{
                  width: '100%',
                  padding: '0.625rem 0.875rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-strong)',
                  backgroundColor: isEditing ? 'var(--neutral-100)' : 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem',
                }}
              >
                {selectableSubjects.length === 0 ? (
                  <option value="">لا توجد مواد إضافية متاحة للإسناد</option>
                ) : (
                  selectableSubjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.code})
                    </option>
                  ))
                )}
              </select>
              <span className="form-hint" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                المواد المعرفة على مستوى المدرسة
              </span>
            </div>

            <Input
              label="عدد الحصص الأسبوعية *"
              type="number"
              min={1}
              max={30}
              value={weeklyPeriods}
              onChange={(e) => setWeeklyPeriods(parseInt(e.target.value, 10) || 1)}
              hint="النصاب الأسبوعي لحصص هذه المادة لهذا الصف"
            />
          </div>

          <div
            style={{
              padding: '1rem 1.5rem',
              backgroundColor: 'var(--neutral-50)',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              gap: '0.75rem',
            }}
          >
            <Button variant="outline" type="button" onClick={onClose} disabled={isLoading}>
              إلغاء
            </Button>
            <Button
              variant="primary"
              type="submit"
              disabled={isLoading || (!isEditing && selectableSubjects.length === 0)}
            >
              {isLoading ? 'جاري الحفظ...' : isEditing ? 'تحديث النصاب' : 'إسناد المادة للمنهج'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
