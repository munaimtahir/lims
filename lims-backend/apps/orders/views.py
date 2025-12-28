from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from apps.core.export_utils import export_to_csv, export_to_excel
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from .filters import OrderFilter


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
    filterset_class = OrderFilter
    search_fields = [
        "order_id",
        "patient__first_name",
        "patient__last_name",
        "patient__phone",
    ]
    ordering_fields = ["created_at", "total_amount", "net_amount"]
    
    @action(detail=False, methods=["get"])
    def export(self, request):
        """
        Export order search results to CSV or Excel.
        
        Query params:
            - format: 'csv' or 'excel' (default: 'csv')
            - All other order filter params are supported
        
        Returns:
            Response: CSV or Excel file download
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        format_type = request.query_params.get("format", "csv").lower()
        filename = f"orders_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        data = serializer.data
        headers = [
            "Order ID", "Patient", "Status", "Priority", "Total Amount",
            "Discount", "Net Amount", "Is Paid", "Created At"
        ]
        
        export_data = []
        for item in data:
            export_data.append([
                item.get("order_id", ""),
                item.get("patient", {}).get("full_name", "") if isinstance(item.get("patient"), dict) else str(item.get("patient", "")),
                item.get("status", ""),
                item.get("priority", ""),
                str(item.get("total_amount", "")),
                str(item.get("discount", "")),
                str(item.get("net_amount", "")),
                "Yes" if item.get("is_paid") else "No",
                item.get("created_at", ""),
            ])
        
        if format_type == "excel":
            return export_to_excel(export_data, f"{filename}.xlsx", headers, "Orders")
        else:
            return export_to_csv(export_data, f"{filename}.csv", headers)

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
        # Check against mapped statuses if needed, or rely on model validation
        if order.status == "PUBLISHED": # Using PUBLISHED as completed state
            return Response(
                {"error": "Cannot cancel completed order"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Use transition_to for proper validation and side effects
            order.transition_to("CANCELLED", user=request.user)
            return Response({"status": "order cancelled"})
        except Exception as e:
            # Fallback if transition fails
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Order Items.

    This ViewSet is read-only.
    """

    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["order", "status"]
