from rest_framework import viewsets, filters
from rest_framework.decorators import action
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from io import BytesIO
from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for payments.

    Provides endpoints for creating, retrieving, updating, and listing payments.
    Includes functionality for filtering and ordering.
    """

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["order", "payment_method", "payment_date"]
    ordering_fields = ["payment_date", "amount"]

    @action(detail=True, methods=["get"])
    def receipt(self, request, pk=None):
        """
        Generate and download a receipt PDF for a payment.

        Args:
            request (Request): The request object.
            pk (int): The primary key of the payment.

        Returns:
            FileResponse: The PDF receipt file.
        """
        payment = self.get_object()

        # Generate PDF receipt
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Header
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50 * mm, height - 50 * mm, "PAYMENT RECEIPT")

        # Receipt details
        p.setFont("Helvetica", 12)
        y = height - 70 * mm

        p.drawString(50 * mm, y, f"Receipt Number: REC-{payment.id:06d}")
        y -= 15 * mm

        p.drawString(
            50 * mm, y, f"Date: {payment.payment_date.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        y -= 15 * mm

        p.drawString(50 * mm, y, f"Order ID: {payment.order.order_id}")
        y -= 15 * mm

        p.drawString(50 * mm, y, f"Patient: {payment.order.patient.get_full_name()}")
        y -= 15 * mm

        p.drawString(
            50 * mm, y, f"Payment Method: {payment.get_payment_method_display()}"
        )
        y -= 15 * mm

        if payment.transaction_id:
            p.drawString(50 * mm, y, f"Transaction ID: {payment.transaction_id}")
            y -= 15 * mm

        # Amount
        p.setFont("Helvetica-Bold", 14)
        y -= 10 * mm
        currency = (
            payment.order.patient.currency
            if hasattr(payment.order.patient, "currency")
            else ""
        )
        p.drawString(50 * mm, y, f"Amount Paid: {payment.amount} {currency}")
        y -= 15 * mm

        # Order details
        p.setFont("Helvetica", 12)
        p.drawString(50 * mm, y, "Order Details:")
        y -= 10 * mm

        p.setFont("Helvetica", 10)
        p.drawString(50 * mm, y, f"Total Amount: {payment.order.total_amount}")
        y -= 10 * mm

        if payment.order.discount > 0:
            p.drawString(50 * mm, y, f"Discount: {payment.order.discount}")
            y -= 10 * mm

        p.drawString(50 * mm, y, f"Net Amount: {payment.order.net_amount}")
        y -= 10 * mm

        # Calculate remaining balance
        total_paid = sum(p.amount for p in payment.order.payments.all())
        remaining = payment.order.net_amount - total_paid
        if remaining > 0:
            p.drawString(50 * mm, y, f"Remaining Balance: {remaining}")
            y -= 10 * mm

        # Notes
        if payment.notes:
            y -= 10 * mm
            p.setFont("Helvetica", 10)
            p.drawString(50 * mm, y, f"Notes: {payment.notes}")

        # Footer
        y = 50 * mm
        p.setFont("Helvetica", 8)
        p.drawString(
            50 * mm,
            y,
            f"Recorded by: {payment.recorded_by.full_name if payment.recorded_by else 'System'}",
        )
        y -= 10 * mm
        p.drawString(50 * mm, y, "Thank you for your payment!")

        p.showPage()
        p.save()

        buffer.seek(0)

        return FileResponse(
            buffer,
            content_type="application/pdf",
            filename=f"Receipt_{payment.id}_{payment.order.order_id}.pdf",
        )
