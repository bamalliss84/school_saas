"""Django settings for School SaaS."""

import os
from datetime import timedelta
from pathlib import Path


# Core and environment
BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {
        '1', 'true', 'yes', 'on',
    }


def env_int(name, default):
    return int(os.environ.get(name, default))


def env_list(name, default=''):
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


# DJANGO_ENV=production turns on fail-fast checks (see the end of this file).
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development').strip().lower()
IS_PRODUCTION = DJANGO_ENV == 'production'
_DEVELOPMENT_SECRET_KEY = 'django-insecure-development-only-change-me'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', _DEVELOPMENT_SECRET_KEY)
DEBUG = env_bool('DJANGO_DEBUG', False)
ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost')


# Applications and middleware
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'django_filters',
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'school_saas_db'),
        'USER': os.environ.get('POSTGRES_USER', 'school_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'school_pass_123'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': env_int('POSTGRES_CONN_MAX_AGE', 60),
    },
}


# Authentication and JWT
AUTH_USER_MODEL = 'core.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=env_int('JWT_ACCESS_MINUTES', 15),
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=env_int('JWT_REFRESH_DAYS', 7),
    ),
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'core.context.MembershipJWTAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'core.api_exceptions.api_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.environ.get('THROTTLE_ANON', '1000/hour'),
        'user': os.environ.get('THROTTLE_USER', '5000/hour'),
        'login': os.environ.get('THROTTLE_LOGIN', '100/hour'),
        'password_reset': os.environ.get('THROTTLE_PASSWORD_RESET', '20/hour'),
        'password_change': os.environ.get('THROTTLE_PASSWORD_CHANGE', '20/hour'),
        'refresh': os.environ.get('THROTTLE_REFRESH', '200/hour'),
        'logout': os.environ.get('THROTTLE_LOGOUT', '200/hour'),
        'reports': os.environ.get('THROTTLE_REPORTS', '1000/hour'),
        'bulk_attendance': os.environ.get('THROTTLE_BULK_ATTENDANCE', '500/hour'),
        'bulk_results': os.environ.get('THROTTLE_BULK_RESULTS', '500/hour'),
        'bulk_publish': os.environ.get('THROTTLE_BULK_PUBLISH', '200/hour'),
        'docs': os.environ.get('THROTTLE_DOCS', '300/hour'),
        'homework_write': os.environ.get('THROTTLE_HOMEWORK_WRITE', '500/hour'),
        'homework_submit': os.environ.get('THROTTLE_HOMEWORK_SUBMIT', '500/hour'),
        'homework_bulk_grade': os.environ.get('THROTTLE_HOMEWORK_BULK_GRADE', '200/hour'),
        'attachment_upload': os.environ.get('THROTTLE_ATTACHMENT_UPLOAD', '200/hour'),
        'notification_list': os.environ.get('THROTTLE_NOTIFICATION_LIST', '1000/hour'),
        'notification_read': os.environ.get('THROTTLE_NOTIFICATION_READ', '1000/hour'),
        'notification_read_all': os.environ.get('THROTTLE_NOTIFICATION_READ_ALL', '300/hour'),
        'notification_broadcast': os.environ.get('THROTTLE_NOTIFICATION_BROADCAST', '100/hour'),
        'conversation_list': os.environ.get('THROTTLE_CONVERSATION_LIST', '1000/hour'),
        'message_send': os.environ.get('THROTTLE_MESSAGE_SEND', '500/hour'),
        'message_attachment_upload': os.environ.get('THROTTLE_MESSAGE_ATTACHMENT_UPLOAD', '200/hour'),
        'school_support_create': os.environ.get('THROTTLE_SCHOOL_SUPPORT_CREATE', '100/hour'),
        'school_support_reply': os.environ.get('THROTTLE_SCHOOL_SUPPORT_REPLY', '500/hour'),
        'homework_dashboard': os.environ.get('THROTTLE_HOMEWORK_DASHBOARD', '1000/hour'),
        'announcement_list': os.environ.get('THROTTLE_ANNOUNCEMENT_LIST', '1000/hour'),
        'announcement_write': os.environ.get('THROTTLE_ANNOUNCEMENT_WRITE', '200/hour'),
        'announcement_read': os.environ.get('THROTTLE_ANNOUNCEMENT_READ', '1000/hour'),
        'announcement_attachment_upload': os.environ.get('THROTTLE_ANNOUNCEMENT_ATTACHMENT_UPLOAD', '200/hour'),
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'School SaaS API',
    'DESCRIPTION': 'Multi-tenant school management API. Prefer /api/v1/.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SECURITY': [{'jwtAuth': []}],
    'PREPROCESSING_HOOKS': ['core.schema.exclude_compatibility_paths'],
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',
        'core.schema.add_school_context_header',
    ],
    'ENUM_NAME_OVERRIDES': {
        'AttendanceStatusEnum': 'core.models.Attendance.STATUS_CHOICES',
        'ExamStatusEnum': 'core.models.Exam.STATUS_CHOICES',
        'ExamResultStatusEnum': 'core.models.ExamResult.STATUS_CHOICES',
        'ResultWorkflowStatusEnum': 'core.models.ExamResult.WORKFLOW_CHOICES',
        'ResultLogActionEnum': 'core.models.ExamResultLog.ACTION_CHOICES',
        'HomeworkStatusEnum': 'core.models.Homework.STATUS_CHOICES',
        'HomeworkSubmissionStatusEnum': 'core.models.HomeworkSubmission.STATUS_CHOICES',
        'ConversationStatusEnum': 'core.models.Conversation.STATUS_CHOICES',
        'ConversationPriorityEnum': 'core.models.Conversation.PRIORITY_CHOICES',
        'AnnouncementPriorityEnum': 'core.models.Announcement.PRIORITY_CHOICES',
        'EnrollmentStatusEnum': (
            'active', 'transferred', 'graduated', 'withdrawn', 'suspended',
        ),
    },
}


# Security, CORS and CSRF
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')
TRUST_X_FORWARDED_FOR = env_bool('TRUST_X_FORWARDED_FOR', False)
CORS_ALLOW_ALL_ORIGINS = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', IS_PRODUCTION)
# Health probes come from the internal network over plain HTTP.
SECURE_REDIRECT_EXEMPT = [r'^health/', r'^api/v1/health/']
if env_bool('USE_X_FORWARDED_PROTO', IS_PRODUCTION):
    # Only behind a trusted TLS-terminating proxy that overwrites this header.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_HSTS_SECONDS = env_int('SECURE_HSTS_SECONDS', 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    'SECURE_HSTS_INCLUDE_SUBDOMAINS', False,
)
SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', False)


# Logging
LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO')

# Optional error alerts by email (core.monitoring). Off unless recipients are set.
# Alerts carry no personal data; the same error is sent at most once per throttle window.
ERROR_ALERT_EMAILS = env_list('ERROR_ALERT_EMAILS', '')
ERROR_ALERT_THROTTLE_SECONDS = env_int('ERROR_ALERT_THROTTLE_SECONDS', 600)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'error_alerts': {
            'class': 'core.monitoring.ErrorAlertEmailHandler',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'error_alerts'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'school_saas': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'error_alerts'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}


# Static and media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Internationalization
LANGUAGE_CODE = os.environ.get('DJANGO_LANGUAGE_CODE', 'ar')
# ISO 4217 currency used for new school fees and platform plans.
DEFAULT_CURRENCY = os.environ.get('DEFAULT_CURRENCY', 'YER').strip().upper()[:3] or 'YER'
TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'Asia/Aden')
USE_I18N = True
USE_TZ = True


# Email placeholders (configure a real backend in deployment)
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.invalid')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = env_int('EMAIL_PORT', 587)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_TIMEOUT = env_int('EMAIL_TIMEOUT', 10)

# Password reset: link target in the web portal and token lifetime (seconds).
PASSWORD_RESET_URL = os.environ.get('PASSWORD_RESET_URL', 'http://localhost:5173/reset-password')
PASSWORD_RESET_TIMEOUT = env_int('PASSWORD_RESET_TIMEOUT', 3600)
# Homework attachments
MAX_HOMEWORK_ATTACHMENT_SIZE_MB = env_int('MAX_HOMEWORK_ATTACHMENT_SIZE_MB', 10)
MAX_SUBMISSION_ATTACHMENT_SIZE_MB = env_int('MAX_SUBMISSION_ATTACHMENT_SIZE_MB', 10)
MAX_ATTACHMENTS_PER_HOMEWORK = env_int('MAX_ATTACHMENTS_PER_HOMEWORK', 10)
MAX_ATTACHMENTS_PER_SUBMISSION = env_int('MAX_ATTACHMENTS_PER_SUBMISSION', 10)
ALLOWED_ATTACHMENT_EXTENSIONS = tuple(env_list(
    'ALLOWED_ATTACHMENT_EXTENSIONS', 'pdf,doc,docx,xls,xlsx,ppt,pptx,txt,jpg,jpeg,png',
))
ALLOWED_ATTACHMENT_MIME_TYPES = tuple(env_list(
    'ALLOWED_ATTACHMENT_MIME_TYPES',
    'application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation,text/plain,image/jpeg,image/png',
))
MAX_MESSAGE_LENGTH = env_int('MAX_MESSAGE_LENGTH', 4000)
MAX_MESSAGE_ATTACHMENT_SIZE_MB = env_int('MAX_MESSAGE_ATTACHMENT_SIZE_MB', 10)
MAX_ATTACHMENTS_PER_MESSAGE = env_int('MAX_ATTACHMENTS_PER_MESSAGE', 5)
ALLOWED_MESSAGE_ATTACHMENT_EXTENSIONS = tuple(env_list(
    'ALLOWED_MESSAGE_ATTACHMENT_EXTENSIONS', 'pdf,doc,docx,xls,xlsx,ppt,pptx,txt,jpg,jpeg,png',
))
ALLOWED_MESSAGE_ATTACHMENT_MIME_TYPES = tuple(env_list(
    'ALLOWED_MESSAGE_ATTACHMENT_MIME_TYPES',
    'application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation,text/plain,image/jpeg,image/png',
))
# Announcements
MAX_ANNOUNCEMENT_ATTACHMENT_SIZE_MB = env_int('MAX_ANNOUNCEMENT_ATTACHMENT_SIZE_MB', 10)
MAX_ATTACHMENTS_PER_ANNOUNCEMENT = env_int('MAX_ATTACHMENTS_PER_ANNOUNCEMENT', 10)
ALLOWED_ANNOUNCEMENT_ATTACHMENT_EXTENSIONS = tuple(env_list(
    'ALLOWED_ANNOUNCEMENT_ATTACHMENT_EXTENSIONS',
    'pdf,doc,docx,xls,xlsx,ppt,pptx,txt,jpg,jpeg,png',
))
ALLOWED_ANNOUNCEMENT_ATTACHMENT_MIME_TYPES = tuple(env_list(
    'ALLOWED_ANNOUNCEMENT_ATTACHMENT_MIME_TYPES',
    'application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation,text/plain,image/jpeg,image/png',
))


# Production fail-fast checks
def _production_problems():
    problems = []
    if SECRET_KEY == _DEVELOPMENT_SECRET_KEY or len(SECRET_KEY) < 50:
        problems.append('DJANGO_SECRET_KEY must be set to a random value of at least 50 characters.')
    if DEBUG:
        problems.append('DJANGO_DEBUG must be false.')
    if not os.environ.get('DJANGO_ALLOWED_HOSTS'):
        problems.append('DJANGO_ALLOWED_HOSTS must list the public host names.')
    if not os.environ.get('POSTGRES_PASSWORD'):
        problems.append('POSTGRES_PASSWORD must be provided by the environment.')
    if EMAIL_BACKEND.endswith('console.EmailBackend'):
        problems.append('EMAIL_BACKEND must be a real backend (password reset emails).')
    return problems


if IS_PRODUCTION:
    _problems = _production_problems()
    if _problems:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured('Unsafe production settings: ' + ' '.join(_problems))
