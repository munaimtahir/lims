"""
Custom exception handlers for clean JSON error responses.
"""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns clean JSON responses.

    Ensures all API errors return consistent JSON format without raw tracebacks.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response is None, it's an unhandled exception
    if response is None:
        # Log the exception for debugging
        logger.exception(f"Unhandled exception: {exc}")

        # Return a clean JSON error response
        return Response(
            {
                "detail": "An unexpected error occurred. Please try again later.",
                "error": "internal_server_error",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Customize the response data format
    custom_response_data = {"detail": None, "error": None}

    # Extract error details
    if hasattr(response, "data"):
        if isinstance(response.data, dict):
            # Handle validation errors
            if "detail" in response.data:
                custom_response_data["detail"] = response.data["detail"]
            elif "non_field_errors" in response.data:
                custom_response_data["detail"] = response.data["non_field_errors"]
            else:
                # Multiple field errors
                custom_response_data["detail"] = "Validation failed"
                custom_response_data["errors"] = response.data
        else:
            custom_response_data["detail"] = str(response.data)

    # Set error code based on status
    status_code = response.status_code
    if status_code == 400:
        custom_response_data["error"] = "bad_request"
    elif status_code == 401:
        custom_response_data["error"] = "unauthorized"
    elif status_code == 403:
        custom_response_data["error"] = "forbidden"
    elif status_code == 404:
        custom_response_data["error"] = "not_found"
    elif status_code == 405:
        custom_response_data["error"] = "method_not_allowed"
    elif status_code == 429:
        custom_response_data["error"] = "too_many_requests"
    elif status_code >= 500:
        custom_response_data["error"] = "internal_server_error"
        # Don't expose internal error details in production
        if (
            not hasattr(context.get("request", None), "user")
            or not context.get("request").user.is_staff
        ):
            custom_response_data[
                "detail"
            ] = "An unexpected error occurred. Please try again later."

    response.data = custom_response_data
    return response
