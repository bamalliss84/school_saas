"""Password reset and change for the global User identity.

Reset is identity-level (not school-scoped): a User may belong to several
schools, so the reset never reads or exposes any membership data. Requests
always look successful to avoid revealing which accounts exist.
"""

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

logger = logging.getLogger(__name__)

INVALID_LINK_MESSAGE = 'رابط إعادة التعيين غير صالح أو منتهي الصلاحية.'


def _find_user(identifier):
    identifier = (identifier or '').strip()
    if not identifier:
        return None
    User = get_user_model()
    active = User.objects.filter(is_active=True)
    user = active.filter(username__iexact=identifier).first()
    if user:
        return user
    if '@' in identifier:
        matches = list(active.filter(email__iexact=identifier)[:2])
        # An email shared by several identities is ambiguous; never guess.
        if len(matches) == 1:
            return matches[0]
    return None


def build_reset_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.PASSWORD_RESET_URL}?{urlencode({'uid': uid, 'token': token})}"


def request_password_reset(identifier):
    """Email a reset link when the identifier maps to one active user with an email."""
    user = _find_user(identifier)
    if user is None or not user.email:
        logger.info('Password reset requested for an unknown or email-less identity.')
        return
    minutes = max(1, settings.PASSWORD_RESET_TIMEOUT // 60)
    body = (
        'مرحبًا،\n\n'
        'وصلنا طلب لإعادة تعيين كلمة المرور لحسابك في منصة المدرسة.\n'
        f'افتح الرابط التالي خلال {minutes} دقيقة لاختيار كلمة مرور جديدة:\n\n'
        f'{build_reset_link(user)}\n\n'
        'إذا لم تطلب ذلك فتجاهل هذه الرسالة، وستبقى كلمة مرورك كما هي.\n'
    )
    try:
        send_mail('إعادة تعيين كلمة المرور', body, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception:  # noqa: BLE001 - delivery failure must not reveal account existence
        logger.exception('Password reset email delivery failed for user id %s.', user.pk)


def _user_from_uid(uid):
    try:
        pk = force_str(urlsafe_base64_decode(uid or ''))
        return get_user_model().objects.get(pk=pk, is_active=True)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        return None


def _set_password(user, new_password):
    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        raise ValidationError({'new_password': list(exc.messages)}) from exc
    user.set_password(new_password)
    user.save(update_fields=['password'])
    # Sign the user out everywhere: every outstanding refresh token is revoked.
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


@transaction.atomic
def confirm_password_reset(uid, token, new_password):
    user = _user_from_uid(uid)
    if user is None or not default_token_generator.check_token(user, token or ''):
        raise ValidationError({'token': [INVALID_LINK_MESSAGE]})
    _set_password(user, new_password)
    return user


@transaction.atomic
def change_password(user, current_password, new_password):
    if not user.check_password(current_password or ''):
        raise ValidationError({'current_password': ['كلمة المرور الحالية غير صحيحة.']})
    if current_password == new_password:
        raise ValidationError({'new_password': ['اختر كلمة مرور مختلفة عن الحالية.']})
    _set_password(user, new_password)
    return user
