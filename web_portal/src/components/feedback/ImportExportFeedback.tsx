import React, { useState } from 'react';
import { CheckCircle2, AlertCircle, FileSpreadsheet, ChevronDown, ChevronUp } from 'lucide-react';
import { ProgressBar } from './ProgressBar';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export interface ImportErrorItem {
  rowNumber: number;
  field?: string;
  message: string;
  rawData?: Record<string, unknown>;
}

export interface ImportFeedbackProps {
  status: 'idle' | 'processing' | 'success' | 'partial_error' | 'error';
  progress?: number;
  statusText?: string;
  successCount?: number;
  errorCount?: number;
  errors?: ImportErrorItem[];
  downloadErrorUrl?: string;
  onRetry?: () => void;
  fileName?: string;
}

export const ImportExportFeedback: React.FC<ImportFeedbackProps> = ({
  status,
  progress = 0,
  statusText,
  successCount = 0,
  errorCount = 0,
  errors = [],
  fileName,
  onRetry,
}) => {
  const [showErrorDetails, setShowErrorDetails] = useState(false);

  if (status === 'idle') return null;

  if (status === 'processing') {
    return (
      <div
        className="card"
        style={{
          padding: '1.25rem 1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <FileSpreadsheet size={18} className="text-primary" />
          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            {statusText || (fileName ? `جاري معالجة ${fileName}...` : 'جاري استيراد البيانات...')}
          </span>
        </div>
        <ProgressBar value={progress} />
      </div>
    );
  }

  if (status === 'success' && errorCount === 0) {
    return (
      <div
        className="card"
        style={{
          padding: '1.25rem 1.5rem',
          backgroundColor: '#f0fdf4',
          borderColor: '#bbf7d0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: 'var(--success-100)',
              color: 'var(--success-700)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CheckCircle2 size={18} />
          </div>
          <div>
            <h5 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#166534', margin: 0 }}>
              {statusText || 'تم تجهيز ومعالجة الملف بنجاح'}
            </h5>
            {successCount > 0 && (
              <p style={{ fontSize: '0.8125rem', color: '#15803d', margin: '0.125rem 0 0 0' }}>
                تم استيراد {successCount} سجل بنجاح دون أي أخطاء.
              </p>
            )}
          </div>
        </div>
        <Badge variant="success">مكتمل بنجاح</Badge>
      </div>
    );
  }

  // Partial error or full error state
  const hasErrors = errorCount > 0 || errors.length > 0;

  return (
    <div
      className="card"
      style={{
        padding: '1.25rem 1.5rem',
        backgroundColor: '#fef2f2',
        borderColor: '#fecaca',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.875rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: 'var(--danger-100)',
              color: 'var(--danger-700)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <AlertCircle size={18} />
          </div>
          <div>
            <h5 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#991b1b', margin: 0 }}>
              {successCount > 0
                ? `تم استيراد ${successCount} سجلاً وتعذر استيراد ${errorCount} سجلات`
                : statusText || 'تعذر معالجة بعض السجلات'}
            </h5>
            <p style={{ fontSize: '0.8125rem', color: '#b91c1c', margin: '0.125rem 0 0 0' }}>
              يرجى مراجعة الأخطاء الموضحة وتصحيحها في الملف ثم إعادة المحاولة.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {hasErrors && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowErrorDetails(!showErrorDetails)}
              rightIcon={showErrorDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              style={{ borderColor: '#fca5a5', color: '#991b1b', backgroundColor: '#ffffff' }}
            >
              {showErrorDetails ? 'إخفاء الأخطاء' : 'عرض الأخطاء'}
            </Button>
          )}
          {onRetry && (
            <Button variant="primary" size="sm" onClick={onRetry}>
              إعادة المحاولة
            </Button>
          )}
        </div>
      </div>

      {showErrorDetails && errors.length > 0 && (
        <div
          style={{
            marginTop: '0.5rem',
            backgroundColor: '#ffffff',
            borderRadius: 'var(--radius-md)',
            border: '1px solid #fee2e2',
            maxHeight: '200px',
            overflowY: 'auto',
            padding: '0.5rem',
          }}
        >
          <table style={{ width: '100%', fontSize: '0.75rem', borderCollapse: 'collapse', textAlign: 'right' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #fecaca', color: '#991b1b' }}>
                <th style={{ padding: '0.375rem 0.5rem' }}>رقم السطر</th>
                <th style={{ padding: '0.375rem 0.5rem' }}>الحقل</th>
                <th style={{ padding: '0.375rem 0.5rem' }}>سبب الخطأ</th>
              </tr>
            </thead>
            <tbody>
              {errors.map((err, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #fef2f2' }}>
                  <td style={{ padding: '0.375rem 0.5rem', fontWeight: 600 }}>{err.rowNumber}</td>
                  <td style={{ padding: '0.375rem 0.5rem', color: 'var(--text-muted)' }}>{err.field || '—'}</td>
                  <td style={{ padding: '0.375rem 0.5rem', color: 'var(--danger-700)' }}>{err.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
