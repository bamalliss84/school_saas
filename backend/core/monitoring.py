"""Optional error alerts by email (no third-party service needed).

Enabled only when ``ERROR_ALERT_EMAILS`` is set. Each alert is deliberately
minimal: error type, request method and path (no query string), and the stack
frames (file, line, function). It never contains the exception message, request
body, headers, cookies, local variables or user data, because those may hold
personal or school data. Full details stay in the server logs.

The same error (same type and location) is reported at most once per
``ERROR_ALERT_THROTTLE_SECONDS`` per process, so a failing page cannot flood
the inbox. Sending never raises: monitoring must not break a request.
"""

import hashlib
import logging
import traceback

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

MAX_FRAMES = 25


def _frames(exc_info):
    if not exc_info or exc_info[2] is None:
        return []
    return [
        f'{frame.filename}:{frame.lineno} in {frame.name}'
        for frame in traceback.extract_tb(exc_info[2])[-MAX_FRAMES:]
    ]


def _one_line(value, limit):
    return ' '.join(str(value).split())[:limit]


def build_alert(record):
    """Return (signature, subject, body) for a log record, without personal data."""
    exc_info = record.exc_info if record.exc_info and record.exc_info[0] else None
    error_type = exc_info[0].__name__ if exc_info else 'Error'
    frames = _frames(exc_info)
    request = getattr(record, 'request', None)
    method = getattr(request, 'method', '') or ''
    path = getattr(request, 'path', '') or ''
    status = getattr(record, 'status_code', '')
    location = frames[-1] if frames else f'{record.pathname}:{record.lineno}'
    signature = hashlib.sha256(f'{error_type}|{location}'.encode()).hexdigest()[:32]

    environment = getattr(settings, 'DJANGO_ENV', 'development')
    where = f'{method} {path}'.strip() or record.name
    subject = _one_line(f'[school_saas {environment}] {error_type} at {where}', 180)
    lines = [
        f'Environment: {environment}',
        f'Logger: {record.name} ({record.levelname})',
        f'Error type: {error_type}',
    ]
    if where != record.name:
        lines.append(f'Request: {where}')
    if status:
        lines.append(f'Status: {status}')
    lines.append(f'Signature: {signature}')
    lines.append('')
    lines.append('Stack (most recent call last):' if frames else f'Location: {location}')
    lines.extend(f'  {frame}' for frame in frames)
    lines.append('')
    lines.append('Details (message, request data) are only in the server logs.')
    return signature, subject, '\n'.join(lines)


class ErrorAlertEmailHandler(logging.Handler):
    """Logging handler that emails a privacy-safe alert for ERROR records."""

    def __init__(self, level=logging.ERROR):
        super().__init__(level=level)

    def emit(self, record):
        try:
            recipients = list(getattr(settings, 'ERROR_ALERT_EMAILS', []) or [])
            if not recipients:
                return
            # Django also logs every 5xx *response* on django.request without a stack.
            # The real exception was already reported where it was raised.
            if record.name == 'django.request' and not (record.exc_info and record.exc_info[0]):
                return
            signature, subject, body = build_alert(record)
            throttle = int(getattr(settings, 'ERROR_ALERT_THROTTLE_SECONDS', 600))
            if throttle > 0 and not cache.add(f'error-alert:{signature}', 1, timeout=throttle):
                return
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)
        except Exception:  # noqa: BLE001 - monitoring must never break the caller
            self.handleError(record)
