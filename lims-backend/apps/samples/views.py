from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.authz import filter_queryset_for_branches, is_tenant_admin, user_tenant

from .models import Sample, SampleStatus
from .serializers import SampleSerializer


class SampleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Samples.
    """

    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["order_item__order", "status", "sample_type"]
    search_fields = [
        "barcode",
        "order_item__order__order_id",
        "order_item__order__patient__first_name",
    ]
    ordering_fields = ["collected_at", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = user_tenant(self.request.user)
        qs = qs.filter(tenant=tenant)
        if not is_tenant_admin(self.request.user):
            qs = filter_queryset_for_branches(qs, "collected_at_branch", self.request.user)
        return qs.select_related("order_item__order__collection_branch")

    @action(detail=False, methods=["get"])
    def pending_collections(self, request):
        """
        Get all pending sample collections (worklist for phlebotomists).

        Returns:
            Response: A paginated list of pending samples.
        """
        pending_samples = self.queryset.filter(
            status__in=[SampleStatus.PENDING, SampleStatus.POSTPONED]
        ).select_related(
            "order_item",
            "order_item__order",
            "order_item__order__patient",
            "collected_by",
        )

        page = self.paginate_queryset(pending_samples)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(pending_samples, many=True)
        return Response(serializer.data)

    def perform_update(self, serializer):
        """
        Perform the update and trigger side effects like creating test results.
        """
        instance = serializer.save()
        if instance.status in [SampleStatus.COLLECTED, SampleStatus.RECEIVED]:
            from apps.results.services.expected_results import ensure_test_results

            ensure_test_results(instance.order_item)

    def perform_destroy(self, instance):
        # Guard deletes after collection/receipt
        if instance.status in [SampleStatus.COLLECTED, SampleStatus.RECEIVED]:
            raise ValidationError("Collected/received samples cannot be deleted.")
        return super().perform_destroy(instance)
