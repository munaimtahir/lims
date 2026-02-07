from django.db.models import OuterRef, Q, Subquery
from django.http import FileResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Payment
from apps.billing.views import PaymentViewSet
from apps.core.export_utils import export_to_csv, export_to_excel
from apps.patients.models import Patient
from apps.reports.models import Report, ReportStatus

from .filters import OrderFilter
from .models import Order, OrderItem
from .serializers import OrderItemSerializer, OrderSerializer


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
        "patient__full_name",
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
            "Order ID",
            "Patient",
            "Status",
            "Priority",
            "Total Amount",
            "Discount",
            "Net Amount",
            "Is Paid",
            "Created At",
        ]

        export_data = []
        for item in data:
            export_data.append(
                [
                    item.get("order_id", ""),
                    (
                        item.get("patient", {}).get("full_name", "")
                        if isinstance(item.get("patient"), dict)
                        else str(item.get("patient", ""))
                    ),
                    item.get("status", ""),
                    item.get("priority", ""),
                    str(item.get("total_amount", "")),
                    str(item.get("discount", "")),
                    str(item.get("net_amount", "")),
                    "Yes" if item.get("is_paid") else "No",
                    item.get("created_at", ""),
                ]
            )

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
        if order.status == "PUBLISHED":  # Using PUBLISHED as completed state
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

    @action(detail=True, methods=["get"], url_path="receipt.pdf")
    def receipt_pdf(self, request, pk=None):
        """Return receipt PDF for the latest payment on the order."""
        order = self.get_object()
        payment = order.payments.order_by("-payment_date").first()
        if not payment:
            return Response(
                {"error": "Receipt not available for this order"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return PaymentViewSet.as_view({"get": "receipt"})(
            request._request, pk=payment.pk
        )

    @action(detail=True, methods=["get"], url_path="report.pdf")
    def report_pdf(self, request, pk=None):
        """Return report PDF for a published order."""
        order = self.get_object()
        if order.status != "PUBLISHED":
            return Response(
                {"error": "Report is not published"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report = (
            Report.objects.filter(
                order=order, status__in=[ReportStatus.FINAL, ReportStatus.AMENDED]
            )
            .order_by("-generated_at")
            .first()
        )
        if not report or not report.report_file:
            return Response(
                {"error": "Report file not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return FileResponse(
            report.report_file.open("rb"),
            content_type="application/pdf",
            filename=report.report_file.name.split("/")[-1],
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


class WorklistPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class WorklistPatientsView(APIView):
    """List patients with latest order workflow status for worklist."""

    pagination_class = WorklistPagination
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get("search")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        status_filter = request.query_params.get("status")

        orders = Order.objects.select_related("patient").all()

        if date_from:
            orders = orders.filter(created_at__date__gte=date_from)
        if date_to:
            orders = orders.filter(created_at__date__lte=date_to)

        if status_filter:
            if status_filter.lower() == "paid":
                orders = orders.filter(is_paid=True)
            elif status_filter.lower() in ["registered", "new"]:
                orders = orders.filter(status="NEW", is_paid=False)
            elif status_filter.upper() in dict(Order.STATUS_CHOICES):
                orders = orders.filter(status=status_filter.upper())

        if search:
            matching_patients = Patient.objects.filter(
                Q(full_name__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(patient_id__icontains=search)
            )
            orders = orders.filter(
                Q(order_id__icontains=search) | Q(patient__in=matching_patients)
            )

        latest_order_subquery = orders.filter(patient=OuterRef("pk")).order_by(
            "-created_at"
        )

        patients = (
            Patient.objects.annotate(
                latest_order_id=Subquery(latest_order_subquery.values("id")[:1]),
                latest_order_number=Subquery(
                    latest_order_subquery.values("order_id")[:1]
                ),
                latest_order_created_at=Subquery(
                    latest_order_subquery.values("created_at")[:1]
                ),
                latest_order_status=Subquery(
                    latest_order_subquery.values("status")[:1]
                ),
                latest_order_is_paid=Subquery(
                    latest_order_subquery.values("is_paid")[:1]
                ),
            )
            .filter(latest_order_id__isnull=False)
            .order_by("-latest_order_created_at")
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(patients, request)
        order_ids = [patient.latest_order_id for patient in page]

        payments = set(
            Payment.objects.filter(order_id__in=order_ids).values_list(
                "order_id", flat=True
            )
        )
        reports = Report.objects.filter(
            order_id__in=order_ids,
            status__in=[ReportStatus.FINAL, ReportStatus.AMENDED],
        ).order_by("-generated_at")
        report_map = {}
        for report in reports:
            report_map.setdefault(report.order_id, report)

        results = []
        for patient in page:
            latest_order_status = patient.latest_order_status or "NEW"
            current_status = "Registered / Order Created"
            if latest_order_status == "NEW" and patient.latest_order_is_paid:
                current_status = "Paid"
            elif latest_order_status == "COLLECTED":
                current_status = "Sample Collected"
            elif latest_order_status == "IN_PROCESS":
                current_status = "In Testing / Result Pending"
            elif latest_order_status == "VERIFIED":
                current_status = "Report Ready / Verified"
            elif latest_order_status == "PUBLISHED":
                current_status = "Report Published"
            elif latest_order_status == "CANCELLED":
                current_status = "Cancelled"

            report = report_map.get(patient.latest_order_id)
            can_reprint_report = bool(
                report and latest_order_status == "PUBLISHED" and report.report_file
            )
            age_years = (
                patient.age_years if patient.age_years is not None else patient.age
            )

            results.append(
                {
                    "patient_id": patient.id,
                    "patient_name": patient.get_full_name(),
                    "mobile": patient.phone,
                    "gender": patient.gender,
                    "date_of_birth": patient.date_of_birth,
                    "age_years": age_years,
                    "age_months": patient.age_months,
                    "age_days": patient.age_days,
                    "latest_order_id": patient.latest_order_id,
                    "latest_order_number": patient.latest_order_number,
                    "latest_order_created_at": patient.latest_order_created_at,
                    "current_status": current_status,
                    "can_reprint_receipt": patient.latest_order_id in payments,
                    "can_reprint_report": can_reprint_report,
                    "receipt_pdf_url": f"/api/v1/orders/orders/{patient.latest_order_id}/receipt.pdf"
                    if patient.latest_order_id in payments
                    else None,
                    "report_pdf_url": f"/api/v1/orders/orders/{patient.latest_order_id}/report.pdf"
                    if can_reprint_report
                    else None,
                }
            )

        return paginator.get_paginated_response(results)
