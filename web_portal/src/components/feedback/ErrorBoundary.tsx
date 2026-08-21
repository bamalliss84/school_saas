import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '../ui/Button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught React Error in Boundary:', error, errorInfo);
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
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
          <div
            className="card"
            style={{ maxWidth: '480px', width: '100%', padding: '2.5rem 2rem', textAlign: 'center' }}
          >
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                backgroundColor: 'var(--danger-50)',
                color: 'var(--danger-600)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1.5rem auto',
              }}
            >
              <AlertCircle size={32} />
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
              حدث خطأ غير متوقع في التطبيق
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              نعتذر عن هذا الخطأ. يرجى إعادة تحميل الصفحة أو المحاولة لاحقًا.
            </p>
            <Button variant="primary" fullWidth leftIcon={<RefreshCw size={16} />} onClick={this.handleReset}>
              إعادة تحميل الصفحة
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
