"""Shared state-transition exceptions and helpers."""

from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidTransitionError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Invalid state transition."
    default_code = "invalid_state_transition"


class PermissionDeniedError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Permission denied."
    default_code = "permission_denied"


class BadPayloadError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid payload."
    default_code = "invalid_payload"
