"""Report views."""

from django.core.files.base import ContentFile
from django.http import FileResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Order
from users.models import UserRole

from .models import Report
from .pdf_generator import generate_report_pdf
from .serializers import ReportSerializer


class ReportListView(generics.ListAPIView):
    """
    Lists all generated reports.
    """

    queryset = Report.objects.all().select_related("order", "generated_by")
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]


class ReportDetailView(generics.RetrieveAPIView):
    """
    Retrieves the details of a specific report.
    """

    queryset = Report.objects.all().select_related("order", "generated_by")
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_report(request, order_id):
    """
    Generates a PDF report for a given order.

    This endpoint is restricted to pathologists and admins. It checks if all
    results for the order are published before generating the report.

    Args:
        request: The request object.
        order_id (int): The ID of the order to generate a report for.

    Returns:
        Response: A response object with the report data or an error message.
    """
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role not in [UserRole.PATHOLOGIST, UserRole.ADMIN]:
        return Response(
            {"error": "Only pathologists can generate reports"},
            status=status.HTTP_403_FORBIDDEN,
        )

    for item in order.items.all():
        if not item.results.filter(status="PUBLISHED").exists():
            return Response(
                {"error": "All results must be published before generating a report"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    pdf_buffer = generate_report_pdf(order)

    report, created = Report.objects.get_or_create(order=order)
    report.generated_by = request.user
    report.pdf_file.save(
        f"report_{order.order_no}.pdf", ContentFile(pdf_buffer.read()), save=True
    )

    serializer = ReportSerializer(report)
    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_report(request, pk):
    """
    Downloads the PDF file for a specific report.

    Args:
        request: The request object.
        pk (int): The primary key of the report to download.

    Returns:
        FileResponse: A file response with the PDF report, or a 404 error.
    """
    try:
        report = Report.objects.get(pk=pk)
    except Report.DoesNotExist:
        return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)

    if not report.pdf_file:
        return Response(
            {"error": "PDF file not available"}, status=status.HTTP_404_NOT_FOUND
        )

    return FileResponse(
        report.pdf_file.open("rb"),
        as_attachment=True,
        filename=f"report_{report.order.order_no}.pdf",
    )
