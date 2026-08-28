import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, AlertCircle, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { AttentionAlert } from '../../types/dashboard';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Button } from '../ui/Button';

interface AttentionAlertsCardProps {
  alerts: AttentionAlert[];
  isLoading?: boolean;
}

export const AttentionAlertsCard: React.FC<AttentionAlertsCardProps> = ({ alerts, isLoading }) => {
  const navigate = useNavigate();

  if (isLoading) {
    return <div className="skeleton" style={{ height: '220px', borderRadius: 'var(--radius-xl)' }} />;
  }

  const getAlertIcon = (severity: AttentionAlert['severity']) => {
    switch (severity) {
      case 'danger':
        return <AlertTriangle size={15} className="text-danger flex-shrink-0" />;
      case 'warning':
        return <AlertCircle size={15} className="text-warning flex-shrink-0" />;
      default:
        return <ShieldAlert size={15} className="text-primary flex-shrink-0" />;
    }
  };

  return (
    <Card className="dashboard-operational-card">
      <CardHeader style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--danger-50)',
                color: 'var(--danger-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ShieldAlert size={16} />
            </div>
            <CardTitle style={{ fontSize: '0.9375rem', fontWeight: 800 }}>يحتاج انتباهك</CardTitle>
          </div>

          {alerts.length > 0 && (
            <span
              style={{
                fontSize: '0.6875rem',
                fontWeight: 700,
                backgroundColor: 'var(--danger-50)',
                color: 'var(--danger-700)',
                padding: '0.125rem 0.5rem',
                borderRadius: 'var(--radius-full)',
                border: '1px solid var(--danger-100)',
              }}
            >
              {alerts.length} تنبيهات
            </span>
          )}
        </div>
      </CardHeader>

      <CardBody style={{ padding: alerts.length > 0 ? '0.625rem 0.75rem' : '1.25rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {alerts.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '0.375rem', padding: '1rem 0', color: 'var(--text-muted)' }}>
            <CheckCircle2 size={24} className="text-success" />
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--neutral-700)' }}>لا توجد تنبيهات عاجلة اليوم</span>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>جميع العمليات التشغيلية تسير بانتظام</span>
          </div>
        ) : (
          alerts.map((alert) => (
            <div key={alert.id} className={`attention-alert-row ${alert.severity}`}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: 0 }}>
                {getAlertIcon(alert.severity)}
                <span className="attention-alert-title" title={alert.title}>
                  {alert.title}
                </span>
              </div>

              <Button
                variant={alert.severity === 'danger' ? 'danger' : 'outline'}
                size="sm"
                onClick={() => navigate(alert.actionRoute)}
                style={{
                  padding: '0.1875rem 0.625rem',
                  fontSize: '0.6875rem',
                  height: '26px',
                  flexShrink: 0,
                }}
              >
                <span>{alert.actionLabel}</span>
              </Button>
            </div>
          ))
        )}
      </CardBody>
    </Card>
  );
};
