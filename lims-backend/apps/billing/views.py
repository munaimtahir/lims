from rest_framework import viewsets, filters
from rest_framework.decorators import action
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.utils import ImageReader
from io import BytesIO
from apps.core.models import SystemSettings
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
        Generate and download a professional receipt PDF for a payment.

        Args:
            request (Request): The request object.
            pk (int): The primary key of the payment.

        Returns:
            FileResponse: The PDF receipt file.
        """
        payment = self.get_object()
        
        # Get lab information from SystemSettings with fallback to env or query params
        try:
            system_settings = SystemSettings.get_settings()
            lab_name = request.query_params.get("lab_name") or system_settings.lab_name or os.environ.get("LAB_NAME", "Laboratory")
            lab_address = request.query_params.get("lab_address") or system_settings.lab_address or os.environ.get("LAB_ADDRESS", "")
            lab_phone = request.query_params.get("lab_phone") or system_settings.lab_phone or os.environ.get("LAB_PHONE", "")
            lab_email = request.query_params.get("lab_email") or system_settings.lab_email or os.environ.get("LAB_EMAIL", "")
            report_header = system_settings.report_header or ""
            report_footer = system_settings.report_footer or ""
            report_header_image = system_settings.report_header_image
            report_footer_image = system_settings.report_footer_image
        except Exception:
            # Fallback to query params or env if SystemSettings fails
            lab_name = request.query_params.get("lab_name") or os.environ.get("LAB_NAME", "Laboratory")
            lab_address = request.query_params.get("lab_address") or os.environ.get("LAB_ADDRESS", "")
            lab_phone = request.query_params.get("lab_phone") or os.environ.get("LAB_PHONE", "")
            lab_email = request.query_params.get("lab_email") or os.environ.get("LAB_EMAIL", "")
            report_header = ""
            report_footer = ""
            report_header_image = None
            report_footer_image = None

        def add_report_image(story, image_field, max_width=6 * inch, spacer=0.15 * inch):
            if not image_field:
                return
            try:
                image_reader = ImageReader(image_field)
                img_width, img_height = image_reader.getSize()
                scale = min(max_width / img_width, 1)
                rendered = Image(image_reader, width=img_width * scale, height=img_height * scale)
                story.append(rendered)
                story.append(Spacer(1, spacer))
            except Exception:
                return

        # Generate PDF receipt
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'ReceiptTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            'ReceiptHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            spaceBefore=12,
        )

        # Header with lab information
        if report_header:
            story.append(Paragraph(report_header, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))

        add_report_image(story, report_header_image)

        header_data = [
            [Paragraph(f"<b>{lab_name}</b>", title_style)],
        ]
        if lab_address:
            header_data.append([Paragraph(lab_address, styles['Normal'])])
        if lab_phone or lab_email:
            contact_info = []
            if lab_phone:
                contact_info.append(f"Phone: {lab_phone}")
            if lab_email:
                contact_info.append(f"Email: {lab_email}")
            header_data.append([Paragraph(" | ".join(contact_info), styles['Normal'])])

        header_table = Table(header_data, colWidths=[6*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.2*inch))

        # Receipt title
        story.append(Paragraph("<b>PAYMENT RECEIPT</b>", title_style))
        story.append(Spacer(1, 0.2*inch))

        # Receipt information
        story.append(Paragraph("<b>Receipt Information</b>", heading_style))
        receipt_data = [
            ['Receipt Number:', f"REC-{payment.id:06d}"],
            ['Date:', payment.payment_date.strftime('%Y-%m-%d %H:%M:%S')],
            ['Order ID:', payment.order.order_id],
            ['Patient:', payment.order.patient.get_full_name()],
            ['Payment Method:', payment.get_payment_method_display()],
        ]
        if payment.transaction_id:
            receipt_data.append(['Transaction ID:', payment.transaction_id])

        receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
        receipt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(receipt_table)
        story.append(Spacer(1, 0.3*inch))

        # Payment details
        story.append(Paragraph("<b>Payment Details</b>", heading_style))
        
        # Calculate totals
        total_paid = sum(p.amount for p in payment.order.payments.all())
        remaining = payment.order.net_amount - total_paid
        currency = "PKR"  # Default currency, can be from settings

        payment_details_data = [
            ['Description', 'Amount'],
            ['Subtotal', f"{currency} {payment.order.total_amount:.2f}"],
        ]
        
        if payment.order.discount > 0:
            payment_details_data.append(['Discount', f"-{currency} {payment.order.discount:.2f}"])
        
        payment_details_data.append(['Net Amount', f"{currency} {payment.order.net_amount:.2f}"])
        payment_details_data.append(['Amount Paid', f"{currency} {payment.amount:.2f}"])
        
        if remaining > 0:
            payment_details_data.append(['Remaining Balance', f"{currency} {remaining:.2f}"])
        else:
            payment_details_data.append(['Status', '<font color="green"><b>PAID IN FULL</b></font>'])

        payment_table = Table(payment_details_data, colWidths=[4*inch, 2*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('FONTNAME', (0, -2), (1, -1), 'Helvetica-Bold'),  # Bold for totals
        ]))
        story.append(payment_table)
        story.append(Spacer(1, 0.3*inch))

        # Notes
        if payment.notes:
            story.append(Paragraph("<b>Notes</b>", heading_style))
            story.append(Paragraph(payment.notes, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

        # Footer
        story.append(Spacer(1, 0.3*inch))
        add_report_image(story, report_footer_image, spacer=0.1 * inch)
        if report_footer:
            story.append(Paragraph(report_footer, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        footer_text = f"Recorded by: {payment.recorded_by.full_name if payment.recorded_by else 'System'}"
        story.append(Paragraph(footer_text, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("<b>Thank you for your payment!</b>", styles['Normal']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        return FileResponse(
            buffer,
            content_type="application/pdf",
            filename=f"Receipt_{payment.id}_{payment.order.order_id}.pdf",
        )
