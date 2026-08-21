import React, { useState } from 'react';
import { School, Check, Star, AlertCircle, X, ShieldAlert } from 'lucide-react';
import { useAuth } from '../../context';
import { SchoolMembership } from '../../types/context';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export const ContextSelectorModal: React.FC = () => {
  const {
    showContextModal,
    setShowContextModal,
    allMemberships,
    activeMembership,
    switchContext,
  } = useAuth();

  const [selectedId, setSelectedId] = useState<number | null>(
    activeMembership?.membership_id || null
  );
  const [setAsDefault, setSetAsDefault] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!showContextModal) return null;

  const handleSelect = async () => {
    if (!selectedId) {
      setErrorMsg('يرجى اختيار مدرسة للمتابعة.');
      return;
    }

    const membership = (allMemberships as SchoolMembership[]).find((m: SchoolMembership) => m.membership_id === selectedId);
    if (!membership) {
      setErrorMsg('السياق المحدد غير متوفر.');
      return;
    }

    if (membership.status === 'suspended' || membership.status === 'ended') {
      setErrorMsg('هذا السياق معلق أو منتهي ولا يمكن استخدامه.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      await switchContext(membership, setAsDefault);
      setShowContextModal(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'تعذر تحديد السياق، يرجى المحاولة مرة أخرى.';
      setErrorMsg(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'school_admin': return 'مدير مدرسة';
      case 'super_admin': return 'مدير عام للنظام';
      case 'teacher': return 'معلم';
      case 'parent': return 'ولي أمر';
      case 'student': return 'طالب';
      default: return role;
    }
  };

  const getStatusBadge = (membership: SchoolMembership) => {
    if (membership.status === 'historical' || membership.access_mode === 'read_only') {
      return <Badge variant="warning">أرشيف (للقراءة فقط)</Badge>;
    }
    if (membership.status === 'active') {
      return <Badge variant="success">نشط</Badge>;
    }
    if (membership.status === 'suspended') {
      return <Badge variant="danger">معلق</Badge>;
    }
    return <Badge variant="neutral">منتهي</Badge>;
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog">
        <div className="modal-header">
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
              }}
            >
              <School size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                اختيار المدرسة والسياق الأكاديمي
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                حدد سياق المدرسة النشط لإدارة بياناتها
              </p>
            </div>
          </div>
          {activeMembership && (
            <button
              onClick={() => setShowContextModal(false)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '0.25rem',
              }}
              aria-label="إغلاق"
            >
              <X size={20} />
            </button>
          )}
        </div>

        <div className="modal-body">
          {errorMsg && (
            <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>
              <AlertCircle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {(allMemberships as SchoolMembership[]).map((m: SchoolMembership) => {
              const isSelected = selectedId === m.membership_id;
              const isUnavailable = m.status === 'suspended' || m.status === 'ended';

              return (
                <div
                  key={m.membership_id}
                  onClick={() => !isUnavailable && setSelectedId(m.membership_id)}
                  style={{
                    padding: '1rem 1.25rem',
                    borderRadius: 'var(--radius-lg)',
                    border: `2px solid ${
                      isSelected ? 'var(--primary-600)' : 'var(--border-subtle)'
                    }`,
                    backgroundColor: isSelected
                      ? 'var(--primary-50)'
                      : isUnavailable
                      ? 'var(--neutral-50)'
                      : 'var(--bg-surface)',
                    opacity: isUnavailable ? 0.6 : 1,
                    cursor: isUnavailable ? 'not-allowed' : 'pointer',
                    transition: 'all var(--transition-fast)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>
                        {m.school.name}
                      </span>
                      {m.is_default && (
                        <Badge variant="primary" icon={<Star size={12} />}>
                          الافتراضي
                        </Badge>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {getStatusBadge(m)}
                      {isSelected && (
                        <div
                          style={{
                            width: '20px',
                            height: '20px',
                            borderRadius: '50%',
                            backgroundColor: 'var(--primary-600)',
                            color: '#ffffff',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <Check size={14} />
                        </div>
                      )}
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '1rem',
                      fontSize: '0.8125rem',
                      color: 'var(--text-secondary)',
                      marginTop: '0.25rem',
                    }}
                  >
                    <div>
                      <span>الدور: </span>
                      <strong>{getRoleLabel(m.role)}</strong>
                    </div>
                    {m.academic_year && (
                      <div>
                        <span>العام الدراسي: </span>
                        <strong>{m.academic_year.name}</strong>
                      </div>
                    )}
                  </div>

                  {isUnavailable && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.375rem',
                        color: 'var(--danger-600)',
                        fontSize: '0.75rem',
                        marginTop: '0.25rem',
                      }}
                    >
                      <ShieldAlert size={14} />
                      <span>هذا السياق غير متاح للاستخدام حاليًا.</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ marginTop: '1.25rem' }}>
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.875rem',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              <input
                type="checkbox"
                checked={setAsDefault}
                onChange={(e) => setSetAsDefault(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: 'var(--primary-600)' }}
              />
              <span>تعيين هذا السياق كافتراضي عند تسجيل الدخول القادم</span>
            </label>
          </div>
        </div>

        <div className="modal-footer">
          {activeMembership && (
            <Button
              variant="outline"
              onClick={() => setShowContextModal(false)}
              disabled={isSubmitting}
            >
              إلغاء
            </Button>
          )}
          <Button
            variant="primary"
            onClick={handleSelect}
            isLoading={isSubmitting}
            disabled={!selectedId}
          >
            تأكيد السياق
          </Button>
        </div>
      </div>
    </div>
  );
};
