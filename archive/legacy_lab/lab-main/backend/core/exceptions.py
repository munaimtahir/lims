"""Custom exception handler for consistent error responses."""

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns a consistent error envelope.
    Format: {error: {code, message, details}}
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "error": {
                "code": response.status_code,
                "message": str(exc),
                "details": response.data,
            }
        }
        response.data = error_data

    return response
