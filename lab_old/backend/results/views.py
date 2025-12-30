"""Result views."""

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from settings.permissions import (
    user_can_enter_result,
    user_can_publish,
    user_can_verify,
)
from settings.utils import should_skip_verification

from .models import Result
from .serializers import ResultSerializer


class ResultListCreateView(generics.ListCreateAPIView):
    """
    Lists and creates results.
    """

    queryset = Result.objects.all().select_related(
        "order_item", "entered_by", "verified_by"
    )
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]


class ResultDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieves and updates a specific result.
    """

    queryset = Result.objects.all().select_related(
        "order_item", "entered_by", "verified_by"
    )
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enter_result(request, pk):
    """
    Marks a result as entered.

    This action is typically performed by a technologist.

    Args:
        request: The request object.
        pk (int): The primary key of the result to enter.

    Returns:
        Response: A response object with the updated result data or an error message.
    """
    try:
        result = Result.objects.get(pk=pk)
    except Result.DoesNotExist:
        return Response({"error": "Result not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_enter_result(request.user):
        return Response(
            {"error": "You do not have permission to enter results"},
            status=status.HTTP_403_FORBIDDEN,
        )

    result.status = "ENTERED"
    result.entered_at = timezone.now()
    result.entered_by = request.user
    result.save()

    serializer = ResultSerializer(result)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_result(request, pk):
    """
    Marks a result as verified.

    This action is typically performed by a pathologist.

    Args:
        request: The request object.
        pk (int): The primary key of the result to verify.

    Returns:
        Response: A response object with the updated result data or an error message.
    """
    try:
        result = Result.objects.get(pk=pk)
    except Result.DoesNotExist:
        return Response({"error": "Result not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_verify(request.user):
        return Response(
            {"error": "You do not have permission to verify results"},
            status=status.HTTP_403_FORBIDDEN,
        )

    if result.status != "ENTERED":
        return Response(
            {"error": "Result must be entered before verification"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result.status = "VERIFIED"
    result.verified_at = timezone.now()
    result.verified_by = request.user
    result.save()

    serializer = ResultSerializer(result)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def publish_result(request, pk):
    """
    Marks a result as published.

    This action is typically performed by a pathologist and is the final step
    in the result workflow.

    Args:
        request: The request object.
        pk (int): The primary key of the result to publish.

    Returns:
        Response: A response object with the updated result data or an error message.
    """
    try:
        result = Result.objects.get(pk=pk)
    except Result.DoesNotExist:
        return Response({"error": "Result not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_publish(request.user):
        return Response(
            {"error": "You do not have permission to publish results"},
            status=status.HTTP_403_FORBIDDEN,
        )

    skip_verification = should_skip_verification()
    required_status = "ENTERED" if skip_verification else "VERIFIED"

    if result.status != required_status:
        error_message = (
            "Result must be verified before publishing"
            if not skip_verification
            else "Result must be entered before publishing"
        )
        return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

    result.status = "PUBLISHED"
    result.published_at = timezone.now()
    result.save()

    serializer = ResultSerializer(result)
    return Response(serializer.data)
