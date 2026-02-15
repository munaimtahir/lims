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
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    CondPageBreak,
    HRFlowable,
)

from apps.core.models import (
    PrintTemplate,
    SystemSettings,
    default_print_template_config,
)
from apps.core.pdf_utils import add_report_image
from apps.laboratory.ranges import pick_reference_range
from apps.orders.models import Order
from apps.reports.models import Report


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


def fmt_date(value):
    if not value:
        return "—"
    try:
        return value.strftime("%d/%m/%Y")
    except Exception:
        return "—"


class PanelTable(Table):
    """Table that rewrites its panel header when a split occurs."""

    def __init__(self, *args, panel_name=None, panel_header_style=None, **kwargs):
        self.panel_name = safe_text(panel_name)
        self.panel_header_style = panel_header_style
        super().__init__(*args, **kwargs)

    def split(self, availWidth, availHeight):
        parts = super().split(availWidth, availHeight)
        if len(parts) <= 1:
            return parts

        continued_label = self.panel_name
        if continued_label and continued_label != "—":
            continued_label = f"{continued_label} (continued)"

        for idx, table in enumerate(parts):
            if idx == 0:
                continue
            try:
                table._cellvalues[0][0] = Paragraph(
                    continued_label, self.panel_header_style
                )
            except Exception:
                # If anything goes wrong, fall back to default content
                continue
        return parts


def build_patient_identity_table(data, available_width, label_style, value_style):
    """Render compact 2-column patient grid (5 rows per column)."""

    left = [
        ("Ref No", data.get("ref_no")),
        ("MR No", data.get("mr_no")),
        ("Mobile", data.get("mobile")),
        ("Booking Date/Time", data.get("booking_dt")),
        ("Sample", data.get("sample")),
    ]
    right = [
        ("Patient Name", data.get("name")),
        ("Age / Gender", data.get("age_gender")),
        ("Consultant", data.get("consultant")),
        ("Reporting Date/Time", data.get("reporting_dt")),
        ("Ref By", data.get("ref_by")),
    ]

    grid_rows = []
    for idx in range(len(left)):
        l_label, l_value = left[idx]
        r_label, r_value = right[idx]
        grid_rows.append(
            [
                Paragraph(l_label, label_style),
                Paragraph(safe_text(l_value), value_style),
                Paragraph(r_label, label_style),
                Paragraph(safe_text(r_value), value_style),
            ]
        )

    col_widths = [
        available_width * 0.18,
        available_width * 0.32,
        available_width * 0.18,
        available_width * 0.32,
    ]

    table = Table(grid_rows, colWidths=col_widths, rowHeights=[0.28 * inch] * 5)
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _format_result_value(result, range_info):
    raw_value = safe_text(getattr(result, "result_value", None))
    flag = safe_text(getattr(result, "flag", ""))
    direction = None

    ref_min = range_info.get("ref_min")
    ref_max = range_info.get("ref_max")

    # Try to derive direction from numeric comparison
    try:
        from decimal import Decimal

        value = Decimal(str(raw_value).replace(",", "").strip())
        if ref_max is not None and value > ref_max:
            direction = "high"
        elif ref_min is not None and value < ref_min:
            direction = "low"
    except Exception:
        direction = None

    if flag.upper() == "H":
        direction = direction or "high"
    elif flag.upper() == "L":
        direction = direction or "low"

    arrow = ""
    if direction == "high":
        arrow = " ↑"
    elif direction == "low":
        arrow = " ↓"

    emphasize = bool(direction)
    return raw_value + arrow, emphasize


def build_panel_block(
    panel_name,
    rows,
    styles,
    available_width,
    opts,
):
    """Return flowables for a single panel with safe page-break handling."""

    col_widths = [
        available_width * 0.42,
        available_width * 0.18,
        available_width * 0.12,
        available_width * 0.28,
    ]

    table_data = [
        [
            Paragraph(safe_text(panel_name).upper(), styles["panel_header"]),
            "",
            "",
            "",
        ],
        [
            Paragraph("Test/Parameter", styles["results_header"]),
            Paragraph("Result", styles["results_header"]),
            Paragraph("Unit", styles["results_header"]),
            Paragraph("Reference Range", styles["results_header"]),
        ],
    ]

    for row in rows:
        result_text, emphasize = _format_result_value(row["result"], row["range_info"])

        critical_note = ""
        if opts.get("show_critical_annotations") and safe_text(getattr(row["result"], "flag", "")) == "C":
            critical_note = "CRITICAL – "
            emphasize = True

        result_para = Paragraph(
            f"{'<b>' if emphasize else ''}{critical_note}{result_text}{'</b>' if emphasize else ''}",
            styles["cell_value"],
        )

        test_lines = [row["test"]]
        if opts.get("show_specimen_details") and row.get("specimen"):
            test_lines.append(f"<font size=8 color='#6b7280'>{row['specimen']}</font>")
        if opts.get("show_method_info") and row.get("method"):
            test_lines.append(f"<font size=8 color='#6b7280'>Method: {row['method']}</font>")

        ref_lines = [row["ref_range"]]
        if opts.get("show_decision_limits") and row.get("decision_limit"):
            ref_lines.append(f"<font size=8 color='#6b7280'>{row['decision_limit']}</font>")

        table_data.append(
            [
                Paragraph("<br/>".join(test_lines), styles["cell_text"]),
                result_para,
                Paragraph(row["unit"], styles["cell_muted"]),
                Paragraph("<br/>".join(ref_lines), styles["cell_muted"]),
            ]
        )

    panel_table = PanelTable(
        table_data,
        panel_name=safe_text(panel_name).upper(),
        panel_header_style=styles["panel_header"],
        colWidths=col_widths,
        repeatRows=2,
    )
    panel_table.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (-1, 0)),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#e5e7eb")),
                ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#111827")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#d1d5db")),
                ("LINEAFTER", (0, 0), (-1, 0), 0, colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 2), (2, -1), "CENTER"),
                ("ALIGN", (3, 2), (3, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 1), (-1, -1), 0.35, colors.HexColor("#e5e7eb")),
            ]
        )
    )

    # Ensure header + first row stay together at page bottom
    min_height_hint = 0.9 * inch
    return [CondPageBreak(min_height_hint), panel_table]


def build_results_flowables(items, patient, styles, available_width, opts):
    grouped = {}
    for item in items:
        if item.panel:
            key = safe_text(getattr(item.panel, "panel_name", None))
        elif item.test:
            key = safe_text(getattr(item.test, "test_name", None))
        else:
            key = "Tests"
        grouped.setdefault(key, []).append(item)

    flowables = []
    for panel_name, panel_items in grouped.items():
        rows = []
        for item in panel_items:
            results = item.results.all().order_by("test_parameter__display_order")
            for result in results:
                param = result.test_parameter
                test_label = safe_text(
                    getattr(param, "effective_parameter_name", None)
                    or getattr(param, "parameter_name", None)
                    or getattr(param, "name", None)
                )
                range_info = pick_reference_range(param, patient)
                specimen_info = "N/A"
                try:
                    sample = item.samples.first()
                    if sample:
                        collected = fmt_dt(getattr(sample, "collected_at", None)) or fmt_dt(getattr(sample, "received_at", None))
                        specimen_info = f"{safe_text(getattr(sample, 'sample_type', 'Specimen'))} · {collected}"
                except Exception:
                    specimen_info = "N/A"

                method_info = ""
                try:
                    method_info = safe_text(getattr(param.parameter, "external_code_value", None))
                except Exception:
                    method_info = "—"
                if method_info == "—":
                    method_info = ""

                decision_limit = ""
                crit_low = range_info.get("critical_low")
                crit_high = range_info.get("critical_high")
                if crit_low is not None or crit_high is not None:
                    parts = []
                    if crit_low is not None:
                        parts.append(f"Critical low: {crit_low}")
                    if crit_high is not None:
                        parts.append(f"Critical high: {crit_high}")
                    decision_limit = " · ".join(parts)

                rows.append(
                    {
                        "test": test_label,
                        "result": result,
                        "unit": safe_text(getattr(param, "unit", None)),
                        "ref_range": safe_text(range_info.get("display")),
                        "range_info": range_info,
                        "specimen": specimen_info,
                        "method": method_info,
                        "decision_limit": decision_limit,
                    }
                )
        if not rows:
            rows.append(
                {
                    "test": "—",
                    "result": safe_text(None),
                    "unit": "—",
                    "ref_range": "—",
                    "range_info": {"ref_min": None, "ref_max": None},
                    "specimen": "",
                    "method": "",
                    "decision_limit": "",
                }
            )

        flowables.extend(build_panel_block(panel_name, rows, styles, available_width, opts))
        flowables.append(Spacer(1, 0.1 * inch))

    return flowables


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
    def cfg(key, default=False):
        try:
            return bool(template_config.get(key, default))
        except Exception:
            return default

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
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor("#1f2937"),
    )
    lab_info_style = ParagraphStyle(
        "LabInfo",
        parent=styles["Normal"],
        fontSize=10 * font_scale,
        leading=13 * font_scale,
        alignment=TA_LEFT,
    )
    patient_label_style = ParagraphStyle(
        "PatientLabel",
        parent=styles["Normal"],
        fontSize=8.5 * font_scale,
        leading=10.5 * font_scale,
        textColor=colors.HexColor("#6b7280"),
    )
    patient_value_style = ParagraphStyle(
        "PatientValue",
        parent=styles["Normal"],
        fontSize=9.5 * font_scale,
        leading=11.5 * font_scale,
        textColor=colors.HexColor("#111827"),
        fontName="Helvetica-Bold",
    )
    results_header_style = ParagraphStyle(
        "ResultsHeader",
        parent=styles["Normal"],
        fontSize=9.5 * font_scale,
        leading=12 * font_scale,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#111827"),
    )
    panel_header_style = ParagraphStyle(
        "PanelHeader",
        parent=styles["Heading3"],
        fontSize=10 * font_scale,
        leading=12 * font_scale,
        textColor=colors.HexColor("#111827"),
    )
    cell_text_style = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontSize=9 * font_scale,
        leading=11.5 * font_scale,
        textColor=colors.HexColor("#111827"),
    )
    cell_muted_style = ParagraphStyle(
        "CellMuted",
        parent=styles["Normal"],
        fontSize=9 * font_scale,
        leading=11.5 * font_scale,
        textColor=colors.HexColor("#4b5563"),
    )
    cell_value_style = ParagraphStyle(
        "CellValue",
        parent=styles["Normal"],
        fontSize=9 * font_scale,
        leading=11.5 * font_scale,
        textColor=colors.HexColor("#111827"),
    )
    body_text_style = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontSize=9 * font_scale,
        leading=11.5 * font_scale,
        textColor=colors.HexColor("#111827"),
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

    # Optional revision banner
    if cfg("show_revision_banner", False):
        try:
            prior_reports = Report.objects.filter(order=order).count()
        except Exception:
            prior_reports = 0
        if prior_reports > 0:
            rev_text = f"Revised report v{prior_reports + 1} · generated {fmt_dt(timezone.now())}"
            story.append(Paragraph(f"<font size=9 color='#6b7280'>{rev_text}</font>", lab_info_style))

    # Demographics block (compact grid)
    patient = getattr(order, "patient", None)
    visit_ref = safe_text(order.order_id or order.id)
    mrn = safe_text(getattr(patient, "mrn", None) or getattr(patient, "patient_id", None))
    patient_name = safe_text(patient.get_full_name() if patient else None)
    dob_text = fmt_date(getattr(patient, "date_of_birth", None))
    mobile = safe_text(getattr(patient, "phone", None))
    consultant = safe_text(getattr(getattr(order, "ordered_by", None), "full_name", None)) if cfg("show_ordering_provider", True) else "—"
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
    sample_collected = fmt_dt(min(sample_times) if sample_times else None) if sample_times else "N/A"

    ref_by = safe_text(
        getattr(order, "referred_by", None)
        or getattr(patient, "default_referred_by", None)
    )

    repeat_id_line = ""
    if cfg("repeat_patient_id_on_pages", False):
        repeat_parts = [part for part in [patient_name, f"MR: {mrn}" if mrn else None, f"DOB: {dob_text}" if cfg("show_patient_dob", False) else None, f"Ref: {visit_ref}"] if part]
        repeat_id_line = " · ".join(repeat_parts)

    patient_block = build_patient_identity_table(
        {
            "ref_no": visit_ref,
            "mr_no": mrn,
            "mobile": mobile,
            "booking_dt": booking_dt,
            "sample": sample_collected,
            "name": patient_name,
            "age_gender": fmt_age_gender(patient)
            + (f" | DOB: {dob_text}" if cfg("show_patient_dob", False) else ""),
            "consultant": consultant,
            "reporting_dt": reporting_dt,
            "ref_by": ref_by,
        },
        available_width,
        patient_label_style,
        patient_value_style,
    )
    story.append(patient_block)
    story.append(Spacer(1, 0.12 * inch))

    if cfg("show_verified_by_line", True):
        verified_users = [r.verified_by for r in all_results if getattr(r, "verified_by", None)]
        verified_name = safe_text(verified_users[-1].get_full_name() if verified_users and hasattr(verified_users[-1], "get_full_name") else (verified_users[-1].full_name if verified_users else None))
        verified_line = f"Verified by: {verified_name} at {reporting_dt}" if verified_name != "—" else f"Reported at {reporting_dt}"
        story.append(Paragraph(f"<font size=9 color='#6b7280'>{verified_line}</font>", lab_info_style))

    # Results block
    story.append(Paragraph("<b>Results</b>", section_style))
    flowable_styles = {
        "panel_header": panel_header_style,
        "results_header": results_header_style,
        "cell_text": cell_text_style,
        "cell_muted": cell_muted_style,
        "cell_value": cell_value_style,
    }
    story.extend(
        build_results_flowables(
            items,
            patient,
            flowable_styles,
            available_width,
            {
                "show_specimen_details": cfg("show_specimen_details", False),
                "show_method_info": cfg("show_method_info", False),
                "show_decision_limits": cfg("show_decision_limits", False),
                "show_critical_annotations": cfg("show_critical_annotations", False),
            },
        )
    )

    # Impression (optional)
    interpretation = safe_text(
        getattr(order, "interpretation", None) or getattr(order, "impression", None)
    )
    if interpretation != "—":
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph("<b>Impression</b>", section_style))
        story.append(Paragraph(interpretation, body_text_style))

    # Footer
    story.append(Spacer(1, 0.25 * inch))
    disclaimer_text = (
        "Electronically verified. Laboratory results should be interpreted by a physician "
        "in correlation with clinical and radiologic findings."
    )
    story.append(Paragraph(disclaimer_text, body_text_style))
    if cfg("show_qc_statement", False):
        qc_text = "Released under ISO 15189-aligned quality system; internal QC acceptable at time of release."
        story.append(Paragraph(qc_text, body_text_style))
    if cfg("show_confidentiality_statement", False):
        conf_text = "Confidential medical record. Do not disclose without patient consent or legal authorization."
        story.append(Paragraph(conf_text, body_text_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("<b>Authorized Signatories</b>", section_style))
    signatory_lines = [
        "Dr. Mubashir Ahmad - MBBS, M.Phil (Biochemistry), Consultant Pathologist",
        "Dr. Muhammad Munaim Tahir - MBBS, M.Phil (Hematology), In-Charge Pathologist",
    ]
    signatory_table = Table(
        [[Paragraph(line, body_text_style)] for line in signatory_lines],
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
        if repeat_id_line:
            canvas_obj.setFont("Helvetica", 8 * font_scale)
            canvas_obj.setFillColor(colors.HexColor("#6b7280"))
            canvas_obj.drawString(left_margin, cursor_y - 8, repeat_id_line)
            canvas_obj.setFillColor(colors.black)
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
