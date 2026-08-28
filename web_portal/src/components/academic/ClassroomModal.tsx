import React, { useState, useEffect } from 'react';
import { X, Layers } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Classroom, ClassroomCreateInput, ClassroomUpdateInput } from '../../types/academic';

export interface ClassroomModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ClassroomCreateInput | ClassroomUpdateInput) => Promise<void>;
  classroom?: Classroom | null;
  isLoading?: boolean;
}

export const ClassroomModal: React.FC<ClassroomModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  classroom,
  isLoading = false,
}) => {
  const isEditing = Boolean(classroom);
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (classroom) {
      setName(classroom.name);
      setCode(classroom.code);
      setIsActive(classroom.is_active);
    } else {
      setName('');
      setCode('');
      setIsActive(true);
    }
    setErrors({});
  }, [classroom, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = 'اسم الصف مطلوب';
    }
    if (!code.trim()) {
      newErrors.code = 'رمز الصف مطلوب';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      setErrors({});
      await onSubmit({
        name: name.trim(),
        code: code.trim(),
        is_active: isActive,
      });
      onClose();
    } catch (err: unknown) {
      if (typeof err === 'object' && err !== null && 'errors' in err) {
        const apiErrors = (err as { errors: Record<string, unknown> }).errors || {};
        const fieldErrors: Record<string, string> = {};
        Object.entries(apiErrors).forEach(([key, val]) => {
          if (Array.isArray(val)) {
            fieldErrors[key] = val.join(', ');
          } else if (typeof val === 'string') {
            fieldErrors[key] = val;
          }
        });
        setErrors(fieldErrors);
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
              <Layers size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                {isEditing ? 'تعديل الصف الدراسي' : 'إضافة صف دراسي جديد'}
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '0.125rem 0 0 0' }}>
                {isEditing ? 'تحديث بيانات الصف الحالي' : 'إضافة مستوى دراسي إلى العام الحالي'}
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
          <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Input
              label="اسم الصف الدراسي *"
              placeholder="مثال: الصف العاشر، الأول الابتدائي"
              value={name}
              onChange={(e) => setName(e.target.value)}
              error={errors.name}
              autoFocus
            />

            <Input
              label="رمز الصف *"
              placeholder="مثال: G10، PRIM-1"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              error={errors.code}
              hint="رمز فريد لتمييز الصف داخل العام الدراسي"
            />

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
              <input
                type="checkbox"
                id="classroom-is-active"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: 'var(--primary-600)', cursor: 'pointer' }}
              />
              <label
                htmlFor="classroom-is-active"
                style={{ fontSize: '0.875rem', color: 'var(--text-primary)', fontWeight: 500, cursor: 'pointer' }}
              >
                الصف الدراسي نشط ومتاح للتسجيل والجدولة
              </label>
            </div>
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
            <Button variant="primary" type="submit" disabled={isLoading}>
              {isLoading ? 'جاري الحفظ...' : isEditing ? 'تحديث الصف' : 'إنشاء الصف'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
