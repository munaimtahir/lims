import os
from io import BytesIO

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.core.models import (
    PrintTemplate,
    SystemSettings,
    default_print_template_config,
)
from apps.core.pdf_utils import add_report_image
from apps.laboratory.ranges import pick_reference_range
from apps.orders.models import Order


def _merge_template_config(config):
    base = default_print_template_config()
    if not isinstance(config, dict):
        return base
    for key, value in config.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key].update(value)
        else:
            base[key] = value
    return base


def safe_text(value, fallback="—"):
    if value is None:
        return fallback
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else fallback
    return str(value)


def fmt_dt(value):
    if not value:
        return "—"
    try:
        dt = timezone.localtime(value)
    except Exception:
        dt = value
    try:
        return dt.strftime("%d/%m/%Y %I:%M %p")
    except Exception:
        return "—"


def fmt_age_gender(patient):
    if not patient:
        return "—"
    age = None
    for field in ("age_years", "age"):
        try:
            candidate = getattr(patient, field, None)
        except Exception:
            candidate = None
        if candidate:
            age = candidate
            break
    gender = safe_text(getattr(patient, "gender", None))
    parts = []
    if age is not None:
        parts.append(f"{age}")
    if gender != "—":
        parts.append(gender)
    return " / ".join(parts) if parts else "—"


class PageNumCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        self._saved_page_states = []
        self._bottom_margin = kwargs.pop("bottom_margin", 0.6 * inch)
        self._right_margin = kwargs.pop("right_margin", 0.6 * inch)
        super().__init__(*args, **kwargs)

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_number(page_count)
            super().showPage()
        super().save()

    def _draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.grey)
        self.drawRightString(
            self._pagesize[0] - self._right_margin,
            self._bottom_margin * 0.6,
            f"Page {self._pageNumber} of {page_count}",
        )
        self.setFillColor(colors.black)


def generate_pdf_report(
    order_id, lab_name=None, lab_address=None, lab_phone=None, lab_email=None
):
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
    # Get system settings with locked template fallbacks
    try:
        system_settings = SystemSettings.get_settings()
        if lab_name is None:
            lab_name = (
                system_settings.lab_name
                or os.environ.get("LAB_NAME")
                or "Al Shifa Diagnostic Laboratory"
            )
        if lab_address is None:
            lab_address = (
                system_settings.lab_address
                or os.environ.get("LAB_ADDRESS")
                or "Circular Road, Jaranwala"
            )
        if lab_phone is None:
            lab_phone = (
                system_settings.lab_phone
                or os.environ.get("LAB_PHONE")
                or "041-4312286"
            )
        if lab_email is None:
            lab_email = system_settings.lab_email or os.environ.get("LAB_EMAIL", "")
        report_header_image = system_settings.report_header_image
        lab_logo = system_settings.lab_logo
    except Exception:
        lab_name = lab_name or os.environ.get("LAB_NAME") or "Al Shifa Diagnostic Laboratory"
        lab_address = lab_address or os.environ.get("LAB_ADDRESS") or "Circular Road, Jaranwala"
        lab_phone = lab_phone or os.environ.get("LAB_PHONE") or "041-4312286"
        lab_email = lab_email or os.environ.get("LAB_EMAIL", "")
        report_header_image = None
        lab_logo = None

    template = PrintTemplate.get_active(PrintTemplate.TYPE_REPORT)
    template_config = _merge_template_config(template.config if template else None)
    font_scale = float(template_config.get("font_scale", 1.0) or 1.0)
    margins = template_config.get("margins", {})

    def _margin_value(key, default):
        try:
            return float(margins.get(key, default) or default) * inch
        except (TypeError, ValueError):
            return float(default) * inch

    left_margin = _margin_value("left", 1.0)
    right_margin = _margin_value("right", 1.0)
    top_margin = _margin_value("top", 1.0)
    bottom_margin = _margin_value("bottom", 1.0)

    page_size = A4

    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    try:
        order = (
            Order.objects.select_related("patient", "ordered_by")
            .prefetch_related(
                "items__test",
                "items__panel",
                "items__results__test_parameter",
                "items__results__test_parameter__reference_ranges",
                "items__samples",
            )
            .get(id=order_id)
        )
    except Order.DoesNotExist:
        raise ValueError("Order not found")

    available_width = page_size[0] - left_margin - right_margin

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=16 * font_scale,
        leading=20 * font_scale,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=11 * font_scale,
        leading=14 * font_scale,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor("#1f2937"),
    )
    lab_info_style = ParagraphStyle(
        "LabInfo",
        parent=styles["Normal"],
        fontSize=10 * font_scale,
        leading=13 * font_scale,
        alignment=TA_LEFT,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9 * font_scale,
        leading=12 * font_scale,
        fontName="Helvetica-Bold",
    )
    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=9 * font_scale,
        leading=12 * font_scale,
    )
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontSize=9 * font_scale,
        leading=12 * font_scale,
        fontName="Helvetica-Bold",
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=9 * font_scale,
        leading=12 * font_scale,
    )

    # Header with logo + lab info (rendered on each page)
    logo_flowable = ""
    logo_col_width = 1.25 * inch
    if lab_logo:
        try:
            image_reader = ImageReader(lab_logo)
            img_width, img_height = image_reader.getSize()
            scale = min(logo_col_width / img_width, 1)
            logo_flowable = Image(
                image_reader, width=img_width * scale, height=img_height * scale
            )
        except Exception:
            logo_flowable = ""

    lab_info_text = (
        f"<b>{safe_text(lab_name)}</b><br/>"
        f"{safe_text(lab_address)}<br/>"
        f"Phone: {safe_text(lab_phone)}"
    )
    header_table = Table(
        [[logo_flowable, Paragraph(lab_info_text, lab_info_style)]],
        colWidths=[logo_col_width, available_width - logo_col_width],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    header_flowables = []
    if report_header_image:
        try:
            image_reader = ImageReader(report_header_image)
            img_width, img_height = image_reader.getSize()
            scale = min(available_width / img_width, 1)
            header_flowables.append(
                Image(
                    image_reader,
                    width=img_width * scale,
                    height=img_height * scale,
                )
            )
            header_flowables.append(Spacer(1, 0.15 * inch))
        except Exception:
            pass
    header_flowables.append(header_table)
    header_flowables.append(Spacer(1, 0.15 * inch))

    header_height = 0
    for flowable in header_flowables:
        _, flow_height = flowable.wrap(available_width, page_size[1])
        header_height += flow_height

    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        rightMargin=right_margin,
        leftMargin=left_margin,
        topMargin=top_margin + header_height,
        bottomMargin=bottom_margin,
        pageCompression=0,
    )

    # Report title
    items = list(order.items.all())
    report_title = "Laboratory Report"
    if len(items) == 1:
        item = items[0]
        if item.test:
            report_title = f"{safe_text(item.test.test_name)} Report"
        elif item.panel:
            report_title = f"{safe_text(item.panel.panel_name)} Report"
    story.append(Paragraph(f"<b>{safe_text(report_title)}</b>", title_style))

    # Demographics block
    patient = getattr(order, "patient", None)
    visit_ref = safe_text(order.order_id or order.id)
    mrn = safe_text(getattr(patient, "mrn", None) or getattr(patient, "patient_id", None))
    patient_name = safe_text(patient.get_full_name() if patient else None)
    mobile = safe_text(getattr(patient, "phone", None))
    consultant = safe_text(getattr(getattr(order, "ordered_by", None), "full_name", None))
    booking_dt = fmt_dt(getattr(order, "created_at", None))

    all_results = []
    all_samples = []
    for item in items:
        all_results.extend(list(item.results.all()))
        all_samples.extend(list(item.samples.all()))

    verified_times = [r.verified_at for r in all_results if r.verified_at]
    reporting_dt = fmt_dt(max(verified_times) if verified_times else timezone.now())

    sample_times = []
    for sample in all_samples:
        if sample.collected_at:
            sample_times.append(sample.collected_at)
        elif sample.received_at:
            sample_times.append(sample.received_at)
    sample_collected = fmt_dt(min(sample_times) if sample_times else None)

    ref_by = safe_text(
        getattr(order, "referred_by", None)
        or getattr(patient, "default_referred_by", None)
    )

    demographics_rows = [
        ("Ref #", visit_ref),
        ("MR #", mrn),
        ("Patient Name", patient_name),
        ("Age/Gender", fmt_age_gender(patient)),
        ("Mobile", mobile),
        ("Consultant", consultant),
        ("Booking Date/Time", booking_dt),
        ("Reporting Date/Time", reporting_dt),
        ("Sample Collected", sample_collected),
        ("Ref By", ref_by),
    ]
    demographics_data = [
        [Paragraph(label, label_style), Paragraph(safe_text(value), value_style)]
        for label, value in demographics_rows
    ]
    demographics_table = Table(
        demographics_data,
        colWidths=[1.8 * inch, available_width - 1.8 * inch],
    )
    demographics_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ]
        )
    )
    story.append(demographics_table)
    story.append(Spacer(1, 0.2 * inch))

    # Results block
    story.append(Paragraph("<b>Results</b>", section_style))
    results_data = [
        [
            Paragraph("Test", table_header_style),
            Paragraph("Result", table_header_style),
            Paragraph("Unit", table_header_style),
            Paragraph("Reference Range", table_header_style),
        ]
    ]

    for item in items:
        results = item.results.all().order_by("test_parameter__display_order")
        for result in results:
            param = result.test_parameter
            test_name = safe_text(getattr(param, "effective_parameter_name", None))
            result_value = safe_text((result.result_value or "").strip())
            unit = safe_text(getattr(param, "unit", None))
            range_info = pick_reference_range(param, patient)
            ref_range = safe_text(range_info.get("display"))
            results_data.append(
                [
                    Paragraph(test_name, table_cell_style),
                    Paragraph(result_value, table_cell_style),
                    Paragraph(unit, table_cell_style),
                    Paragraph(ref_range, table_cell_style),
                ]
            )

    if len(results_data) == 1:
        results_data.append(
            [
                Paragraph("—", table_cell_style),
                Paragraph("—", table_cell_style),
                Paragraph("—", table_cell_style),
                Paragraph("—", table_cell_style),
            ]
        )

    col_widths = [
        available_width * 0.42,
        available_width * 0.18,
        available_width * 0.12,
        available_width * 0.28,
    ]
    results_table = Table(results_data, colWidths=col_widths, repeatRows=1)
    results_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5f5")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(results_table)

    # Impression (optional)
    interpretation = safe_text(
        getattr(order, "interpretation", None) or getattr(order, "impression", None)
    )
    if interpretation != "—":
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("<b>Impression</b>", section_style))
        story.append(Paragraph(interpretation, value_style))

    # Footer
    story.append(Spacer(1, 0.25 * inch))
    disclaimer_text = (
        "Electronically verified. Laboratory results should be interpreted by a physician "
        "in correlation with clinical and radiologic findings."
    )
    story.append(Paragraph(disclaimer_text, value_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("<b>Authorized Signatories</b>", section_style))
    signatory_lines = [
        "Dr. Mubashir Ahmad - MBBS, M.Phil (Biochemistry), Consultant Pathologist",
        "Dr. Muhammad Munaim Tahir - MBBS, M.Phil (Hematology), In-Charge Pathologist",
    ]
    signatory_table = Table(
        [[Paragraph(line, value_style)] for line in signatory_lines],
        colWidths=[available_width],
    )
    signatory_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(signatory_table)

    def _draw_header(canvas_obj, doc_obj):
        canvas_obj.saveState()
        cursor_y = page_size[1] - top_margin
        for flowable in header_flowables:
            flow_width, flow_height = flowable.wrap(available_width, page_size[1])
            cursor_y -= flow_height
            flowable.drawOn(canvas_obj, left_margin, cursor_y)
        canvas_obj.restoreState()

    # Build PDF with repeated header + page numbers
    doc.build(
        story,
        onFirstPage=_draw_header,
        onLaterPages=_draw_header,
        canvasmaker=lambda *args, **kwargs: PageNumCanvas(
            *args, **kwargs, bottom_margin=bottom_margin, right_margin=right_margin
        ),
    )
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
