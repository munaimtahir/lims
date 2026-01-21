from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.utils import ImageReader
from io import BytesIO
import os
from django.utils import timezone
from django.conf import settings
from apps.orders.models import Order
from apps.laboratory.ranges import pick_reference_range
from apps.core.models import SystemSettings
from apps.core.pdf_utils import add_report_image


def generate_pdf_report(order_id, lab_name=None, lab_address=None, lab_phone=None, lab_email=None):
    """
    Generate a professional PDF report for a given order.

    This function creates a well-formatted PDF with:
    - Professional header with lab information
    - Patient demographics
    - Formatted test results in tables
    - Reference ranges and flags
    - Digital signatures
    - Pagination for long reports

    Args:
        order_id (int): The ID of the order to generate the report for.
        lab_name (str, optional): Name of the laboratory (overrides System Settings).
        lab_address (str, optional): Address of the laboratory (overrides System Settings).
        lab_phone (str, optional): Phone number of the laboratory (overrides System Settings).
        lab_email (str, optional): Email of the laboratory (overrides System Settings).

    Returns:
        bytes: The content of the generated PDF file.

    Raises:
        ValueError: If the order is not found.
    """
    # Get system settings for lab information with fallback to environment variables
    try:
        system_settings = SystemSettings.get_settings()
        if lab_name is None:
            lab_name = system_settings.lab_name or os.environ.get("LAB_NAME", "Laboratory")
        if lab_address is None:
            lab_address = system_settings.lab_address or os.environ.get("LAB_ADDRESS", "")
        if lab_phone is None:
            lab_phone = system_settings.lab_phone or os.environ.get("LAB_PHONE", "")
        if lab_email is None:
            lab_email = system_settings.lab_email or os.environ.get("LAB_EMAIL", "")
        report_header = system_settings.report_header or ""
        report_footer = system_settings.report_footer or ""
        report_header_image = system_settings.report_header_image
        report_footer_image = system_settings.report_footer_image
    except Exception:
        # Fallback to environment variables if settings don't exist
        lab_name = lab_name or os.environ.get("LAB_NAME", "Laboratory")
        lab_address = lab_address or os.environ.get("LAB_ADDRESS", "")
        lab_phone = lab_phone or os.environ.get("LAB_PHONE", "")
        lab_email = lab_email or os.environ.get("LAB_EMAIL", "")
        report_header = ""
        report_footer = ""
        report_header_image = None
        report_footer_image = None
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    story = []
    styles = getSampleStyleSheet()

    try:
        order = Order.objects.select_related('patient').prefetch_related(
            'items__test', 'items__panel', 'items__results__test_parameter'
        ).get(id=order_id)
    except Order.DoesNotExist:
        raise ValueError("Order not found")

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12,
    )

    # Header
    header_data = []
    
    # Custom header from settings
    if report_header:
        header_data.append([Paragraph(report_header, styles['Normal'])])
        header_data.append([Spacer(1, 0.1*inch)])

    add_report_image(story, report_header_image)
    
    header_data.append([Paragraph(f"<b>{lab_name}</b>", title_style)])
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

    # Report title
    story.append(Paragraph("<b>LABORATORY REPORT</b>", title_style))
    story.append(Spacer(1, 0.1*inch))

    # Patient Information
    story.append(Paragraph("<b>Patient Information</b>", heading_style))
    patient_data = [
        ['Patient Name:', order.patient.get_full_name()],
        ['Patient ID:', order.patient.patient_id],
        ['Date of Birth:', order.patient.date_of_birth.strftime('%Y-%m-%d') if order.patient.date_of_birth else 'N/A'],
        ['Gender:', order.patient.gender],
        ['Order ID:', order.order_id],
        ['Order Date:', order.created_at.strftime('%Y-%m-%d %H:%M')],
        ['Report Date:', timezone.now().strftime('%Y-%m-%d %H:%M')],
    ]
    patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
    patient_table.setStyle(TableStyle([
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
    story.append(patient_table)
    story.append(Spacer(1, 0.3*inch))

    # Test Results
    story.append(Paragraph("<b>Test Results</b>", heading_style))

    for item in order.items.all():
        test_name = item.test.test_name if item.test else item.panel.panel_name if item.panel else "Unknown Test"
        
        # Test header
        story.append(Paragraph(f"<b>{test_name}</b>", styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))

        # Results table
        results_data = [['Parameter', 'Result', 'Unit', 'Reference Range', 'Flag']]
        
        for result in item.results.all().order_by('test_parameter__display_order'):
            param = result.test_parameter
            range_info = pick_reference_range(param, order.patient)
            ref_range = range_info["display"]

            flag_map = {
                "C": "Critical",
                "L": "Low",
                "H": "High",
                "critical_low": "Critical Low",
                "critical_high": "Critical High",
                "low": "Low",
                "high": "High",
                "normal": "Normal",
                "abnormal": "Abnormal",
            }
            flag_label = flag_map.get(result.flag, "Normal" if not result.flag else result.flag)

            # Format flag with color indication
            flag_text = flag_label
            if 'Critical' in flag_label:
                flag_text = f"<font color='red'><b>{flag_text}</b></font>"
            elif result.flag in ['high', 'low', 'H', 'L']:
                flag_text = f"<font color='orange'>{flag_text}</font>"

            results_data.append([
                param.effective_parameter_name,
                result.result_value,
                param.unit,
                ref_range,
                Paragraph(flag_text, styles['Normal']),
            ])

        if len(results_data) > 1:  # If there are results
            results_table = Table(results_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 1.5*inch, 1.2*inch])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ]))
            story.append(results_table)
        else:
            story.append(Paragraph("<i>No results available</i>", styles['Normal']))

        story.append(Spacer(1, 0.2*inch))

    # Footer with signatures
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("<b>Authorized Signatures</b>", heading_style))
    
    signature_data = [
        ['Lab Technician:', '___________________', 'Pathologist:', '___________________'],
        ['', '', '', ''],
        ['Date:', '___________________', 'Date:', '___________________'],
    ]
    signature_table = Table(signature_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(signature_table)
    
    add_report_image(story, report_footer_image, spacer=0.1 * inch)

    # Custom footer from settings
    if report_footer:
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(report_footer, styles['Normal']))

    # Build PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
