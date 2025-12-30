"""PDF generation utilities for Al Shifa reports."""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_report_pdf(order):
    """Generate PDF report for an order using Al Shifa template."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#003366"),
        spaceAfter=12,
        alignment=1,  # Center
    )

    # Header
    story.append(Paragraph("AL SHIFA LABORATORY", title_style))
    story.append(Spacer(1, 0.2 * inch))

    # Patient Information
    patient = order.patient
    patient_info = [
        ["Patient Name:", patient.full_name, "MRN:", patient.mrn],
        ["Father Name:", patient.father_name, "Age/Sex:", f"{patient.sex}"],
        ["Order No:", order.order_no, "Date:", datetime.now().strftime("%Y-%m-%d")],
    ]

    patient_table = Table(
        patient_info, colWidths=[1.5 * inch, 2.5 * inch, 1 * inch, 2 * inch]
    )
    patient_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(patient_table)
    story.append(Spacer(1, 0.3 * inch))

    # Results Table
    results_data = [["Test Name", "Result", "Unit", "Reference Range", "Flag"]]

    for item in order.items.all():
        results = item.results.filter(status="PUBLISHED")
        for result in results:
            results_data.append(
                [
                    item.test.name,
                    result.value,
                    result.unit or "-",
                    result.reference_range or "-",
                    result.flags or "N",
                ]
            )

    results_table = Table(
        results_data,
        colWidths=[2.5 * inch, 1.5 * inch, 1 * inch, 1.5 * inch, 0.5 * inch],
    )
    results_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
            ]
        )
    )
    story.append(results_table)
    story.append(Spacer(1, 0.5 * inch))

    # Signatories
    sig_data = [
        ["Dr. Mubashir Ahmad", "Dr. Muhammad Munaim Tahir"],
        ["MBBS, M.Phil (Biochemistry)", "MBBS, M.Phil (Hematology)"],
        ["Consultant Biochemist", "Consultant Hematologist"],
    ]
    sig_table = Table(sig_data, colWidths=[3.5 * inch, 3.5 * inch])
    sig_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(sig_table)

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
