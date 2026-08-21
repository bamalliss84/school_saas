import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { GraduationCap, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '../context';
import { LoginCredentials } from '../types/auth';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { LoginIllustration } from '../components/auth/LoginIllustration';

interface LocationState {
  from?: {
    pathname?: string;
  };
}

export const LoginPage: React.FC = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, unknown>>({});
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { isSubmitting, errors },
  } = useForm<LoginCredentials>();

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      const state = location.state as LocationState | null;
      const from = state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const onSubmit = async (data: LoginCredentials) => {
    setErrorMessage(null);
    setFieldErrors({});
    try {
      const response = await login(data);
      const userRole = response.user?.role;

      if (userRole !== 'school_admin' && userRole !== 'super_admin') {
        navigate('/unauthorized', { replace: true });
        return;
      }

      if (response.has_multiple_contexts && !response.default_membership_id) {
        navigate('/select-context', { replace: true });
      } else {
        const state = location.state as LocationState | null;
        const from = state?.from?.pathname || '/dashboard';
        navigate(from, { replace: true });
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'message' in err) {
        const msg = (err as { message: string }).message;
        setErrorMessage(msg || 'تعذّر تسجيل الدخول، تحقق من بيانات الدخول وحاول مرة أخرى.');
        if ('errors' in err && typeof (err as { errors: Record<string, unknown> }).errors === 'object') {
          setFieldErrors((err as { errors: Record<string, unknown> }).errors);
        }
      } else {
        setErrorMessage('تعذّر تسجيل الدخول، تحقق من بيانات الدخول وحاول مرة أخرى.');
      }
    }
  };

  return (
    <div className="login-page-container">
      <main className="login-card-wrapper">
        {/* Right Pane (RTL First): Login Form */}
        <section className="login-form-pane" aria-labelledby="login-heading">
          {/* Brand Badge */}
          <div className="login-brand-badge">
            <span className="login-brand-icon-wrap" aria-hidden="true">
              <GraduationCap size={17} />
            </span>
            <span className="login-brand-title">منصة المدرسة</span>
          </div>

          {/* Heading & Subheading */}
          <h1 id="login-heading" className="login-heading">
            تسجيل الدخول
          </h1>
          <p className="login-subheading">
            مرحباً بعودتك، أدخل بياناتك للوصول إلى لوحة إدارة المدرسة
          </p>

          {/* Error Banner */}
          {errorMessage && (
            <div className="login-error-alert" role="alert" aria-live="assertive">
              <AlertCircle size={16} className="flex-shrink-0" />
              <div>
                <span>{errorMessage}</span>
                {Object.keys(fieldErrors).length > 0 && (
                  <ul style={{ marginTop: '0.25rem', paddingRight: '1rem', fontSize: '0.75rem' }}>
                    {Object.entries(fieldErrors).map(([key, val]) => (
                      <li key={key}>
                        {key}: {Array.isArray(val) ? val.join(', ') : String(val)}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <Input
              label="اسم المستخدم أو البريد الإلكتروني"
              placeholder="اسم المستخدم أو البريد"
              autoComplete="username"
              error={errors.username?.message || (errorMessage ? ' ' : undefined)}
              {...register('username', {
                required: 'اسم المستخدم مطلوب',
              })}
            />

            <Input
              label="كلمة المرور"
              type={showPassword ? 'text' : 'password'}
              placeholder="كلمة المرور"
              autoComplete="current-password"
              error={errors.password?.message || (errorMessage ? ' ' : undefined)}
              endAdornment={
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              }
              {...register('password', {
                required: 'كلمة المرور مطلوبة',
              })}
            />

            <div style={{ marginTop: '1.125rem' }}>
              <Button
                type="submit"
                variant="primary"
                fullWidth
                size="lg"
                isLoading={isSubmitting}
                loadingText="جاري تسجيل الدخول..."
              >
                تسجيل الدخول
              </Button>
            </div>
          </form>

          {/* Footer Note */}
          <div className="login-footer-caption">
            دخول آمن إلى نظام إدارة المدرسة
          </div>
        </section>

        {/* Left Pane (RTL Second): Hub Diagram & Features */}
        <section className="login-feature-pane" aria-label="ميزات منصة المدرسة">
          <LoginIllustration />
          <h2 className="login-feature-title">
            إدارة مدرستك من مكان واحد
          </h2>
          <p className="login-feature-subtitle">
            الطلاب، المعلمون، الحضور، الجداول، الواجبات والنتائج في نظام موحد.
          </p>
        </section>
      </main>
    </div>
  );
};
