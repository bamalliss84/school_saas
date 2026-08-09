"""Reusable serializer fields with predictable API query semantics."""

from rest_framework import serializers
from rest_framework.fields import empty


class OptionalBooleanField(serializers.BooleanField):
    """A BooleanField that stays absent when an HTML-style QueryDict omits it.

    DRF's stock BooleanField treats an omitted key in HTML input as ``False``.
    ``request.query_params`` is a QueryDict and therefore triggers that HTML
    behavior, which can silently apply a false-valued filter even when the
    client did not send the parameter. Query serializers must preserve the
    distinction between "not supplied" and an explicit ``false``.
    """

    default_empty_html = empty
