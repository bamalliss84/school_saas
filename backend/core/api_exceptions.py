import logging

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import exception_handler


logger = logging.getLogger('core.api')

DEFAULT_MESSAGES = {
    400: 'Validation failed.',
    401: 'Authentication credentials were not provided.',
    403: 'You do not have permission to perform this action.',
    404: 'Not found.',
    405: 'Method not allowed.',
    415: 'Unsupported media type.',
    429: 'Request was throttled.',
    500: 'Internal server error.',
}


def api_exception_handler(exc, context):
    """Return predictable error envelopes while preserving DRF status codes."""
    response = exception_handler(exc, context)
    if response is None:
        if settings.DEBUG:
            return None
        logger.exception(
            'Unhandled API exception in %s',
            context.get('view').__class__.__name__ if context.get('view') else 'unknown',
            exc_info=exc,
        )
        return Response({
            'success': False,
            'message': DEFAULT_MESSAGES[500],
            'errors': {},
        }, status=500)

    original_data = response.data
    detail = original_data.get('detail') if isinstance(original_data, dict) else None

    if response.status_code == 400:
        message = DEFAULT_MESSAGES[400]
        errors = original_data
    else:
        message = DEFAULT_MESSAGES.get(
            response.status_code,
            str(detail) if detail else 'Request failed.',
        )
        if response.status_code not in DEFAULT_MESSAGES and detail:
            message = str(detail)
        context_code = getattr(exc, 'context_error_code', None)
        errors = {'code': context_code} if context_code else {}

    response.data = {
        'success': False,
        'message': message,
        'errors': errors,
    }
    return response