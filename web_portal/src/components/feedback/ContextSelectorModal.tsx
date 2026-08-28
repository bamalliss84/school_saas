import React, { useState, useMemo } from 'react';
import {
  School,
  Check,
  Star,
  AlertCircle,
  X,
  ShieldAlert,
  Search,
  Clock,
  Building,
} from 'lucide-react';
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
    activeMembership?.membership_id || (allMemberships.length > 0 ? allMemberships[0].membership_id : null)
  );
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [setAsDefault, setSetAsDefault] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Sync selectedId when modal opens
  React.useEffect(() => {
    if (showContextModal) {
      setSelectedId(activeMembership?.membership_id || (allMemberships.length > 0 ? allMemberships[0].membership_id : null));
      setSearchQuery('');
      setErrorMsg(null);
      setSetAsDefault(false);
    }
  }, [showContextModal, activeMembership, allMemberships]);

  const filteredMemberships = useMemo(() => {
    if (!searchQuery.trim()) return allMemberships;
    const query = searchQuery.trim().toLowerCase();
    return allMemberships.filter((m) => {
      const schoolMatch = m.school?.name?.toLowerCase().includes(query);
      const yearMatch = m.academic_year?.name?.toLowerCase().includes(query);
      return schoolMatch || yearMatch;
    });
  }, [allMemberships, searchQuery]);

  if (!showContextModal) return null;

  const selectedMembership = allMemberships.find((m) => m.membership_id === selectedId);
  const isSelectedHistorical = selectedMembership?.status === 'historical' || selectedMembership?.access_mode === 'read_only';

  const handleSelect = async () => {
    if (!selectedId) {
      setErrorMsg('يرجى اختيار مدرسة للمتابعة.');
      return;
    }

    const membership = allMemberships.find((m) => m.membership_id === selectedId);
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
      await switchContext(membership, setAsDefault && !isSelectedHistorical);
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
      return (
        <Badge variant="warning" icon={<Clock size={11} />}>
          أرشيف (للقراءة فقط)
        </Badge>
      );
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
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="context-modal-title">
      <div className="modal-dialog" style={{ maxWidth: '560px' }}>
        {/* Modal Header */}
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
                flexShrink: 0,
              }}
            >
              <School size={20} />
            </div>
            <div>
              <h3 id="context-modal-title" style={{ fontSize: '1.0625rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                اختيار المدرسة والسياق الأكاديمي
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.0625rem' }}>
                حدد سياق المدرسة والعام الدراسي لإدارة العمليات التشغيلية
              </p>
            </div>
          </div>
          {activeMembership && (
            <button
              onClick={() => !isSubmitting && setShowContextModal(false)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
                padding: '0.25rem',
                borderRadius: 'var(--radius-sm)',
              }}
              aria-label="إغلاق"
              disabled={isSubmitting}
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {errorMsg && (
            <div className="alert alert-danger" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem' }}>
              <AlertCircle size={16} className="flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Search Bar for multiple contexts */}
          {allMemberships.length > 2 && (
            <div style={{ marginBottom: '0.875rem', position: 'relative' }}>
              <Search
                size={14}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)',
                }}
              />
              <input
                type="text"
                placeholder="بحث عن مدرسة أو عام دراسي..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.4375rem 2.25rem 0.4375rem 0.75rem',
                  fontSize: '0.78125rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  backgroundColor: 'var(--neutral-50)',
                  outline: 'none',
                }}
              />
            </div>
          )}

          {/* Single-context informational note (Requirement 10) */}
          {allMemberships.length === 1 && (
            <div
              style={{
                padding: '0.625rem 0.75rem',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--primary-50)',
                border: '1px solid var(--primary-100)',
                color: 'var(--primary-800)',
                fontSize: '0.75rem',
                marginBottom: '0.75rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <Building size={16} className="flex-shrink-0" />
              <span>لديك سياق مدرسي واحد متاح لهذا الحساب.</span>
            </div>
          )}

          {/* Context List Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
            {filteredMemberships.map((m: SchoolMembership) => {
              const isSelected = selectedId === m.membership_id;
              const isCurrentActive = activeMembership?.membership_id === m.membership_id;
              const isUnavailable = m.status === 'suspended' || m.status === 'ended';
              const isHistorical = m.status === 'historical' || m.access_mode === 'read_only';

              return (
                <div
                  key={m.membership_id}
                  onClick={() => !isUnavailable && !isSubmitting && setSelectedId(m.membership_id)}
                  style={{
                    padding: '0.875rem 1rem',
                    borderRadius: 'var(--radius-lg)',
                    border: `2px solid ${
                      isSelected
                        ? 'var(--primary-600)'
                        : isCurrentActive
                        ? 'var(--primary-200)'
                        : 'var(--border-subtle)'
                    }`,
                    backgroundColor: isSelected
                      ? '#eff6ff'
                      : isUnavailable
                      ? 'var(--neutral-50)'
                      : '#ffffff',
                    opacity: isUnavailable ? 0.55 : 1,
                    cursor: isUnavailable || isSubmitting ? 'not-allowed' : 'pointer',
                    transition: 'all 0.15s ease',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.375rem',
                    boxShadow: isSelected ? '0 1px 3px rgba(37, 99, 235, 0.1)' : 'none',
                  }}
                >
                  {/* Top line: School Name + Badges */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', minWidth: 0 }}>
                      <span
                        style={{
                          fontWeight: 800,
                          fontSize: '0.875rem',
                          color: 'var(--text-primary)',
                          wordBreak: 'break-word',
                        }}
                      >
                        {m.school.name}
                      </span>
                      {m.is_default && (
                        <Badge variant="primary" icon={<Star size={10} />}>
                          الافتراضي
                        </Badge>
                      )}
                      {isCurrentActive && (
                        <span
                          style={{
                            fontSize: '0.625rem',
                            fontWeight: 700,
                            color: 'var(--primary-700)',
                            backgroundColor: 'var(--primary-100)',
                            padding: '0.0625rem 0.375rem',
                            borderRadius: 'var(--radius-full)',
                          }}
                        >
                          السياق الحالي
                        </span>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', flexShrink: 0 }}>
                      {getStatusBadge(m)}
                      {isSelected && (
                        <div
                          style={{
                            width: '18px',
                            height: '18px',
                            borderRadius: '50%',
                            backgroundColor: 'var(--primary-600)',
                            color: '#ffffff',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <Check size={12} strokeWidth={3} />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Subline: Role & Academic Year */}
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '0.875rem',
                      fontSize: '0.75rem',
                      color: 'var(--text-secondary)',
                      marginTop: '0.125rem',
                    }}
                  >
                    <div>
                      <span>الدور: </span>
                      <strong style={{ color: 'var(--text-primary)' }}>{getRoleLabel(m.role)}</strong>
                    </div>
                    {m.academic_year && (
                      <div>
                        <span>العام الدراسي: </span>
                        <strong style={{ color: isHistorical ? '#b45309' : 'var(--text-primary)' }}>
                          {m.academic_year.name}
                        </strong>
                      </div>
                    )}
                  </div>

                  {/* Historical read-only warning indicator */}
                  {isHistorical && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.375rem',
                        color: '#92400e',
                        fontSize: '0.6875rem',
                        marginTop: '0.125rem',
                      }}
                    >
                      <Clock size={12} />
                      <span>بيانات هذا العام الدراسي للعرض والأرشفة فقط (Read-only).</span>
                    </div>
                  )}

                  {/* Unavailable warning indicator */}
                  {isUnavailable && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.375rem',
                        color: 'var(--danger-600)',
                        fontSize: '0.6875rem',
                        marginTop: '0.125rem',
                      }}
                    >
                      <ShieldAlert size={12} />
                      <span>هذا السياق غير متاح للاستخدام حاليًا.</span>
                    </div>
                  )}
                </div>
              );
            })}

            {filteredMemberships.length === 0 && (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                لا توجد مدارس أو سياقات مطابقة لبحثك.
              </div>
            )}
          </div>

          {/* Make Default Checkbox (Only enabled for active contexts) */}
          {!isSelectedHistorical && selectedMembership?.status === 'active' && (
            <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.78125rem',
                  color: 'var(--text-secondary)',
                  cursor: isSubmitting ? 'not-allowed' : 'pointer',
                }}
              >
                <input
                  type="checkbox"
                  checked={setAsDefault}
                  onChange={(e) => setSetAsDefault(e.target.checked)}
                  disabled={isSubmitting}
                  style={{ width: '15px', height: '15px', accentColor: 'var(--primary-600)' }}
                />
                <span>تعيين هذا السياق كافتراضي عند تسجيل الدخول القادم</span>
              </label>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          {activeMembership && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowContextModal(false)}
              disabled={isSubmitting}
              style={{ fontSize: '0.78125rem' }}
            >
              إلغاء
            </Button>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={handleSelect}
            isLoading={isSubmitting}
            disabled={!selectedId || isSubmitting}
            style={{ fontSize: '0.78125rem', padding: '0.375rem 1rem' }}
          >
            تأكيد السياق
          </Button>
        </div>
      </div>
    </div>
  );
};
