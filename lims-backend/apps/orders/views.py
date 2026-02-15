from django.db import transaction
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
from apps.core.authz import (
    filter_queryset_for_branches,
    is_tenant_admin,
    user_active_branches,
    user_has_branch_access,
    user_tenant,
)
from apps.core.export_utils import export_to_csv, export_to_excel
from apps.patients.models import Patient
from apps.reports.models import Report, ReportStatus
from apps.orders.services import transition_visit_state

from .filters import OrderFilter
from .models import Dispatch, DispatchItem, DispatchStatus, Order, OrderItem
from .serializers import (
    DispatchCreateSerializer,
    DispatchSerializer,
    OrderItemSerializer,
    OrderSerializer,
)


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

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status != "NEW":
            return Response(
                {"detail": "Only NEW orders can be deleted. Use explicit admin override."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.instance
        target_status = serializer.validated_data.get("status")
        if target_status and target_status != instance.status:
            transition_visit_state(instance, target_status, self.request.user, source="api")
            serializer.validated_data.pop("status", None)
        serializer.save()

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = user_tenant(self.request.user)
        qs = qs.filter(tenant=tenant)
        if not is_tenant_admin(self.request.user):
            qs = filter_queryset_for_branches(qs, "collection_branch", self.request.user)
        return qs.select_related("patient", "collection_branch", "processing_branch")

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
        try:
            transition_visit_state(order, "CANCELLED", request.user, source="api")
            return Response({"detail": "Order cancelled successfully."})
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=getattr(e, "status_code", status.HTTP_400_BAD_REQUEST),
            )

    @action(detail=True, methods=["post"], url_path="admin-delete")
    def admin_delete(self, request, pk=None):
        order = self.get_object()
        if not request.user.is_admin:
            return Response(
                {"detail": "Only Admin can use override delete."},
                status=status.HTTP_403_FORBIDDEN,
            )
        order.delete()
        return Response({"detail": "Order deleted via admin override."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="receipt.pdf")
    def receipt_pdf(self, request, pk=None):
        """Return receipt PDF for the latest payment on the order."""
        order = self.get_object()
        payment = order.payments.order_by("-payment_date").first()
        if not payment:
            return Response(
                {"detail": "Receipt not available for this order."},
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
                {"detail": "Report is not published."},
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
                {"detail": "Report file not found."},
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

    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["order", "status"]

    def get_queryset(self):
        qs = OrderItem.objects.select_related(
            "order",
            "order__patient",
            "test",
            "panel",
        )
        tenant = user_tenant(self.request.user)
        qs = qs.filter(order__tenant=tenant)
        if not is_tenant_admin(self.request.user):
            qs = filter_queryset_for_branches(qs, "order__collection_branch", self.request.user)
        return qs


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
            can_reprint_report = bool(report and report.report_file)
            receipt_pdf_url = None
            report_pdf_url = None
            if patient.latest_order_id and patient.latest_order_id in payments:
                receipt_pdf_url = (
                    f"/api/v1/orders/orders/{patient.latest_order_id}/receipt.pdf"
                )
            if patient.latest_order_id and can_reprint_report and report:
                report_pdf_url = report.report_file.url
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
                    "receipt_pdf_url": receipt_pdf_url,
                    "report_pdf_url": report_pdf_url,
                    # Backwards-compatible fields for existing clients
                    "receipt_url": str(patient.latest_order_id)
                    if patient.latest_order_id
                    else None,
                    "report_url": report_pdf_url,
                }
            )

        return paginator.get_paginated_response(results)


class DispatchViewSet(viewsets.ModelViewSet):
    """
    Create dispatch (branch → main lab), send (mark IN_TRANSIT), receive (mark RECEIVED, set samples).
    Branch users can create/send only for their branch; main lab can receive.
    """

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return DispatchCreateSerializer
        return DispatchSerializer

    def get_queryset(self):
        qs = Dispatch.objects.all().select_related(
            "from_branch", "to_branch", "tenant", "created_by", "received_by"
        ).prefetch_related("items", "items__order")
        tenant = user_tenant(self.request.user)
        qs = qs.filter(tenant=tenant)
        if not is_tenant_admin(self.request.user):
            branches = user_active_branches(self.request.user)
            branch_ids = list(branches.values_list("id", flat=True))
            qs = qs.filter(
                Q(from_branch_id__in=branch_ids) | Q(to_branch_id__in=branch_ids)
            )
        return qs.distinct()

    def create(self, request, *args, **kwargs):
        ser = DispatchCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        from_branch = ser.validated_data["from_branch"]
        to_branch = ser.validated_data["to_branch"]
        order_ids = ser.validated_data["order_ids"]
        if not user_has_branch_access(request.user, from_branch):
            return Response(
                {"detail": "You can only create dispatches from your branch."},
                status=status.HTTP_403_FORBIDDEN,
            )
        tenant = user_tenant(request.user)
        orders = Order.objects.filter(
            id__in=order_ids,
            tenant=tenant,
            collection_branch=from_branch,
            status="COLLECTED",
        )
        if orders.count() != len(order_ids):
            return Response(
                {"detail": "Some orders are not COLLECTED or not from this branch."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            dispatch = Dispatch.objects.create(
                tenant=tenant,
                from_branch=from_branch,
                to_branch=to_branch,
                created_by=request.user,
                status=DispatchStatus.CREATED,
            )
            for order in orders:
                DispatchItem.objects.get_or_create(dispatch=dispatch, order=order)
        serializer = DispatchSerializer(dispatch)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DispatchSerializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = DispatchSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """Mark dispatch IN_TRANSIT (branch user)."""
        dispatch = self.get_object()
        if dispatch.status != DispatchStatus.CREATED:
            return Response(
                {"detail": f"Dispatch is {dispatch.status}, cannot send."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user_has_branch_access(request.user, dispatch.from_branch):
            return Response(
                {"detail": "Only your branch can send this dispatch."},
                status=status.HTTP_403_FORBIDDEN,
            )
        dispatch.status = DispatchStatus.IN_TRANSIT
        dispatch.sent_at = timezone.now()
        dispatch.save(update_fields=["status", "sent_at"])
        serializer = DispatchSerializer(dispatch)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """Mark dispatch RECEIVED and set all samples to RECEIVED (main lab user)."""
        dispatch = self.get_object()
        if dispatch.status != DispatchStatus.IN_TRANSIT:
            return Response(
                {"detail": f"Dispatch is {dispatch.status}, cannot receive."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user_has_branch_access(request.user, dispatch.to_branch):
            return Response(
                {"detail": "Only the receiving branch can receive this dispatch."},
                status=status.HTTP_403_FORBIDDEN,
            )
        from apps.samples.models import Sample, SampleStatus

        now = timezone.now()
        order_ids = list(dispatch.items.values_list("order_id", flat=True))
        samples = Sample.objects.filter(
            order_item__order_id__in=order_ids,
            status=SampleStatus.COLLECTED,
        )
        samples.update(
            status=SampleStatus.RECEIVED,
            received_at=now,
            received_by=request.user,
        )
        dispatch.status = DispatchStatus.RECEIVED
        dispatch.received_at = now
        dispatch.received_by = request.user
        dispatch.save(update_fields=["status", "received_at", "received_by"])
        serializer = DispatchSerializer(dispatch)
        return Response(serializer.data)
