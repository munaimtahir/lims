from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import SampleCollection
from .serializers import SampleCollectionSerializer


class SampleCollectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Sample Collections.
    """

    queryset = SampleCollection.objects.all()
    serializer_class = SampleCollectionSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["order", "status", "sample_type"]
    search_fields = ["barcode", "order__order_id", "order__patient__first_name"]
    ordering_fields = ["collected_at", "status"]

    @action(detail=False, methods=["get"])
    def pending_collections(self, request):
        """
        Get all pending sample collections (worklist for phlebotomists).

        Returns:
            Response: A paginated list of pending sample collections.
        """
        pending_samples = (
            self.queryset.filter(status="pending")
            .select_related("order", "order__patient", "collected_by")
            .prefetch_related("order_items")
        )

        page = self.paginate_queryset(pending_samples)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(pending_samples, many=True)
        return Response(serializer.data)
