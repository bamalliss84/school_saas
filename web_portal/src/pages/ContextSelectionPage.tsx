import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { School, Check, Star, AlertCircle, LogOut } from 'lucide-react';
import { useAuth } from '../context';
import { SchoolMembership } from '../types/context';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export const ContextSelectionPage: React.FC = () => {
  const { allMemberships, activeMembership, switchContext, logout } = useAuth();
  const navigate = useNavigate();

  const [selectedId, setSelectedId] = useState<number | null>(
    activeMembership?.membership_id || null
  );
  const [setAsDefault, setSetAsDefault] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

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
      navigate('/dashboard', { replace: true });
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

  const getStatusBadge = (m: SchoolMembership) => {
    if (m.status === 'historical' || m.access_mode === 'read_only') {
      return <Badge variant="warning">أرشيف (للقراءة فقط)</Badge>;
    }
    if (m.status === 'active') {
      return <Badge variant="success">نشط</Badge>;
    }
    if (m.status === 'suspended') {
      return <Badge variant="danger">معلق</Badge>;
    }
    return <Badge variant="neutral">منتهي</Badge>;
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-app)',
        padding: '1.5rem',
      }}
    >
      <div className="card" style={{ maxWidth: '540px', width: '100%', padding: '2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: 'var(--radius-xl)',
              backgroundColor: 'var(--primary-50)',
              color: 'var(--primary-600)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem auto',
            }}
          >
            <School size={28} />
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            تحديد سياق المدرسة
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            حسابك مرتبط بأكثر من مدرسة أو عام دراسي. حدد السياق الذي ترغب بالعمل عليه:
          </p>
        </div>

        {errorMsg && (
          <div className="alert alert-danger" style={{ marginBottom: '1.25rem' }}>
            <AlertCircle size={18} />
            <span>{errorMsg}</span>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
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
              </div>
            );
          })}
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
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

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Button
            variant="primary"
            fullWidth
            size="lg"
            onClick={handleSelect}
            isLoading={isSubmitting}
            disabled={!selectedId}
          >
            متابعة إلى لوحة التحكم
          </Button>
          <Button
            variant="outline"
            size="lg"
            onClick={() => logout()}
            leftIcon={<LogOut size={18} />}
          >
            خروج
          </Button>
        </div>
      </div>
    </div>
  );
};
