from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Orders.
    """

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["patient", "status", "is_paid", "created_at"]
    search_fields = [
        "order_id",
        "patient__first_name",
        "patient__last_name",
        "patient__phone",
    ]
    ordering_fields = ["created_at", "total_amount"]

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancel an order.

        Args:
            request (Request): The request object.
            pk (int, optional): The primary key of the order. Defaults to None.

        Returns:
            Response: A response object with a status message.
        """
        order = self.get_object()
        if order.status == "completed":
            return Response(
                {"error": "Cannot cancel completed order"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = "cancelled"
        order.save()
        return Response({"status": "order cancelled"})


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Order Items.

    This ViewSet is read-only.
    """

    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["order", "status"]
