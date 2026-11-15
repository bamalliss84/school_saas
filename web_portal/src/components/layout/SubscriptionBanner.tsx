import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { useAuth } from '../../context';
import { billingService, SUBSCRIPTION_WARNING_TEXT } from '../../services/billingService';

/** Shows a platform-subscription warning to school admins (no_subscription is shown only on the page). */
export const SubscriptionBanner: React.FC = () => {
  const { activeMembership } = useAuth();
  const [warning, setWarning] = useState<string | null>(null);
  const role = activeMembership?.role;
  const membershipId = activeMembership?.membership_id;

  useEffect(() => {
    setWarning(null);
    if (!membershipId || (role !== 'school_admin' && role !== 'super_admin')) return undefined;
    let cancelled = false;
    billingService.subscription()
      .then((status) => { if (!cancelled) setWarning(status.warning); })
      .catch(() => { if (!cancelled) setWarning(null); });
    return () => { cancelled = true; };
  }, [membershipId, role]);

  if (!warning || warning === 'no_subscription') return null;
  return (
    <div role="status" style={{
      display: 'flex', alignItems: 'center', gap: '.5rem', padding: '.55rem 1rem', fontSize: '.9rem',
      background: 'var(--warning-50, #fffbeb)', color: 'var(--warning-800, #92400e)', borderBottom: '1px solid var(--warning-200, #fde68a)',
    }}>
      <AlertTriangle size={16} aria-hidden="true" />
      <span style={{ flex: 1 }}>{SUBSCRIPTION_WARNING_TEXT[warning] || warning}</span>
      <Link to="/subscription">تفاصيل الاشتراك</Link>
    </div>
  );
};
