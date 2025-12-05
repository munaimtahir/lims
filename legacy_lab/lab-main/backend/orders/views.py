"""Order views."""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from patients.permissions import IsAdminOrReception

from .models import Order, OrderStatus
from .serializers import OrderSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    """
    Lists and creates orders.

    Allows for the retrieval of a list of all orders, and the creation of new
    orders. Creation is restricted to admin and reception users.

    Filtering:
    - `patient` (integer): Filters orders by the patient's ID.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrReception]

    def get_queryset(self):
        """
        Optionally filters the queryset by a `patient` ID.

        Returns:
            QuerySet: The filtered queryset of `Order` objects.
        """
        queryset = (
            Order.objects.all()
            .select_related("patient")
            .prefetch_related("items__test")
        )
        patient_id = self.request.query_params.get("patient")
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Creates a new order.

        Args:
            request: The request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The response object with the created order data.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class OrderDetailView(generics.RetrieveAPIView):
    """
    Retrieves the details of a specific order.
    """

    queryset = (
        Order.objects.all().select_related("patient").prefetch_related("items__test")
    )
    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrReception]


@api_view(["POST"])
@permission_classes([IsAdminOrReception])
def cancel_order(request, pk):
    """
    Cancels an order if no samples have been collected.

    Args:
        request: The request object.
        pk (int): The primary key of the order to cancel.

    Returns:
        Response: A response object with a success or error message.
    """
    try:
        order = Order.objects.prefetch_related("items__samples").get(pk=pk)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if order is already cancelled
    if order.status == OrderStatus.CANCELLED:
        return Response(
            {"error": "Order is already cancelled"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Check if any samples have been collected
    has_collected_samples = False
    for item in order.items.all():
        if item.samples.filter(status__in=["COLLECTED", "RECEIVED"]).exists():
            has_collected_samples = True
            break

    if has_collected_samples:
        return Response(
            {"error": "Cannot cancel order after samples have been collected"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Cancel the order
    order.status = OrderStatus.CANCELLED
    order.save()

    # Cancel all order items
    order.items.update(status=OrderStatus.CANCELLED)

    serializer = OrderSerializer(order)
    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsAdminOrReception])
def edit_order_tests(request, pk):
    """
    Edits the tests in an order (add/remove).

    This is only possible if no samples or results have been created for the order.

    Args:
        request: The request object, containing `tests_to_add` and/or `tests_to_remove`.
        pk (int): The primary key of the order to edit.

    Returns:
        Response: A response object with the updated order data or an error message.
    """
    try:
        order = Order.objects.prefetch_related("items__samples", "items__results").get(
            pk=pk
        )
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if order is cancelled
    if order.status == OrderStatus.CANCELLED:
        return Response(
            {"error": "Cannot edit a cancelled order"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if any samples exist
    has_samples = False
    for item in order.items.all():
        if item.samples.exists():
            has_samples = True
            break

    if has_samples:
        return Response(
            {"error": "Cannot edit tests after samples have been created"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if any results exist
    has_results = False
    for item in order.items.all():
        if item.results.exists():
            has_results = True
            break

    if has_results:
        return Response(
            {"error": "Cannot edit tests after results have been created"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get test modifications from request
    tests_to_add = request.data.get("tests_to_add", [])
    tests_to_remove = request.data.get("tests_to_remove", [])

    if not tests_to_add and not tests_to_remove:
        return Response(
            {"error": "No tests specified for addition or removal"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate that we're not removing all tests
    current_test_ids = set(order.items.values_list("test_id", flat=True))
    remaining_tests = current_test_ids - set(tests_to_remove)
    if not remaining_tests and not tests_to_add:
        return Response(
            {"error": "Cannot remove all tests from order"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Remove tests
    if tests_to_remove:
        from .models import OrderItem

        OrderItem.objects.filter(order=order, test_id__in=tests_to_remove).delete()

    # Add tests
    if tests_to_add:
        from .models import OrderItem

        for test_id in tests_to_add:
            # Check if test already exists in order
            if not OrderItem.objects.filter(order=order, test_id=test_id).exists():
                OrderItem.objects.create(order=order, test_id=test_id)

    # Refresh order and return
    order.refresh_from_db()
    serializer = OrderSerializer(order)
    return Response(serializer.data)
