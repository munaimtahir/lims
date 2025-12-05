"""Sample views."""

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import OrderStatus
from results.models import Result, ResultStatus
from settings.permissions import user_can_collect
from users.models import UserRole

from .models import Sample, SampleStatus
from .serializers import SampleSerializer


class SampleListCreateView(generics.ListCreateAPIView):
    """
    Lists and creates samples.
    """

    queryset = Sample.objects.all().select_related(
        "order_item", "collected_by", "received_by"
    )
    serializer_class = SampleSerializer
    permission_classes = [IsAuthenticated]


class SampleDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieves and updates a specific sample.
    """

    queryset = Sample.objects.all().select_related(
        "order_item", "collected_by", "received_by"
    )
    serializer_class = SampleSerializer
    permission_classes = [IsAuthenticated]


def _create_result_for_order_item(order_item):
    """
    Creates a Result object for the given order item if one doesn't exist.

    This is called when a sample is received in the lab, enabling result entry.

    Args:
        order_item: The OrderItem to create a result for.

    Returns:
        Result: The created or existing Result object.
    """
    # Check if a result already exists for this order item
    existing_result = Result.objects.filter(order_item=order_item).first()
    if existing_result:
        return existing_result

    # Create a new DRAFT result for the order item
    return Result.objects.create(
        order_item=order_item,
        value="",
        status=ResultStatus.DRAFT,
    )


def _update_order_status_on_sample_receive(order_item):
    """
    Updates the order status when a sample is received.

    When all samples for an order are received, the order transitions
    to IN_PROCESS status (ready for result entry).

    Args:
        order_item: The OrderItem whose sample was received.
    """
    order = order_item.order

    # Check if all samples for all order items are received
    all_samples_received = True
    for item in order.items.all():
        sample = item.samples.first()
        if not sample or sample.status not in [SampleStatus.RECEIVED]:
            all_samples_received = False
            break

    # If all samples are received, update order status to IN_PROCESS
    if all_samples_received and order.status in [
        OrderStatus.NEW,
        OrderStatus.COLLECTED,
    ]:
        order.status = OrderStatus.IN_PROCESS
        order.save()

    # Also update the order item status
    if order_item.status in [OrderStatus.NEW, OrderStatus.COLLECTED]:
        order_item.status = OrderStatus.IN_PROCESS
        order_item.save()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def collect_sample(request, pk):
    """
    Marks a sample as collected.

    Args:
        request: The request object.
        pk (int): The primary key of the sample to collect.

    Returns:
        Response: A response object with the updated sample data or an error message.
    """
    try:
        sample = Sample.objects.get(pk=pk)
    except Sample.DoesNotExist:
        return Response({"error": "Sample not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_collect(request.user):
        return Response(
            {"error": "You do not have permission to collect samples"},
            status=status.HTTP_403_FORBIDDEN,
        )

    sample.status = SampleStatus.COLLECTED
    sample.collected_at = timezone.now()
    sample.collected_by = request.user
    sample.save()

    # Update order status to COLLECTED if this is the first collection
    order = sample.order_item.order
    if order.status == OrderStatus.NEW:
        order.status = OrderStatus.COLLECTED
        order.save()

    # Update order item status
    if sample.order_item.status == OrderStatus.NEW:
        sample.order_item.status = OrderStatus.COLLECTED
        sample.order_item.save()

    serializer = SampleSerializer(sample)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def receive_sample(request, pk):
    """
    Marks a sample as received in the lab.

    This action also creates a Result object for the order item,
    enabling result entry for this test.

    Args:
        request: The request object.
        pk (int): The primary key of the sample to receive.

    Returns:
        Response: A response object with the updated sample data or an error message.
    """
    try:
        sample = Sample.objects.get(pk=pk)
    except Sample.DoesNotExist:
        return Response({"error": "Sample not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role not in [
        UserRole.PHLEBOTOMY,
        UserRole.TECHNOLOGIST,
        UserRole.PATHOLOGIST,
        UserRole.ADMIN,
    ]:
        return Response(
            {"error": "Only lab staff can receive samples"},
            status=status.HTTP_403_FORBIDDEN,
        )

    sample.status = SampleStatus.RECEIVED
    sample.received_at = timezone.now()
    sample.received_by = request.user
    sample.save()

    # Create a Result object for this order item (ready for result entry)
    _create_result_for_order_item(sample.order_item)

    # Update order and order item status
    _update_order_status_on_sample_receive(sample.order_item)

    serializer = SampleSerializer(sample)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_sample(request, pk):
    """
    Rejects a sample with a given reason.

    Args:
        request: The request object, containing the `rejection_reason`.
        pk (int): The primary key of the sample to reject.

    Returns:
        Response: A response object with the updated sample data or an error message.
    """
    try:
        sample = Sample.objects.get(pk=pk)
    except Sample.DoesNotExist:
        return Response({"error": "Sample not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role not in [
        UserRole.PHLEBOTOMY,
        UserRole.TECHNOLOGIST,
        UserRole.PATHOLOGIST,
        UserRole.ADMIN,
    ]:
        return Response(
            {"error": "Only lab staff can reject samples"},
            status=status.HTTP_403_FORBIDDEN,
        )

    if sample.status not in [
        SampleStatus.PENDING,
        SampleStatus.COLLECTED,
        SampleStatus.RECEIVED,
    ]:
        return Response(
            {"error": f"Cannot reject sample with status {sample.status}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rejection_reason = request.data.get("rejection_reason", "").strip()
    if not rejection_reason:
        return Response(
            {"error": "Rejection reason is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    sample.status = SampleStatus.REJECTED
    sample.rejection_reason = rejection_reason
    sample.save()

    serializer = SampleSerializer(sample)
    return Response(serializer.data)
