import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileQuestion, Home } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div
      style={{
        minHeight: '80vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
        textAlign: 'center',
      }}
    >
      <div style={{ maxWidth: '420px', width: '100%' }}>
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            backgroundColor: 'var(--neutral-100)',
            color: 'var(--neutral-500)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.25rem auto',
          }}
        >
          <FileQuestion size={32} />
        </div>

        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          الصفحة غير موجودة (404)
        </h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          عذراً، الصفحة التي تبحث عنها غير متوفرة أو قد تم نقلها.
        </p>

        <Button
          variant="primary"
          leftIcon={<Home size={18} />}
          onClick={() => navigate('/dashboard')}
        >
          العودة للوحة التحكم
        </Button>
      </div>
    </div>
  );
};
