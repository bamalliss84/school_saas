from rest_framework.views import exception_handler


DEFAULT_MESSAGES = {
    400: 'Validation failed.',
    401: 'Authentication credentials were not provided.',
    403: 'You do not have permission to perform this action.',
    404: 'Not found.',
}


def api_exception_handler(exc, context):
    """Return predictable error envelopes while preserving DRF status codes."""
    response = exception_handler(exc, context)
    if response is None:
        return None

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
        errors = {}

    response.data = {
        'success': False,
        'message': message,
        'errors': errors,
    }
    return response