from io import BytesIO
from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, CondPageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from apps.orders.models import Order, OrderItem
from apps.results.models import TestResult
from apps.laboratory.models import Test, TestPanel
from apps.laboratory.ranges import pick_reference_range
from apps.reports.models import Report, ReportStatus

def collect_report_blockers(order_id):
    """
    Check if an order is eligible for report generation.
    Returns a list of blocking reasons.
    """
    try:
        order = Order.objects.prefetch_related(
            'items__test',
            'items__panel',
            'items__results__test_parameter'
        ).get(id=order_id)
    except Order.DoesNotExist:
        return [{"reason_code": "ORDER_NOT_FOUND", "detail": "Order does not exist."}]

    blockers = []

    # 1. NOT_VERIFIED
    if order.status not in ["VERIFIED", "PUBLISHED"]:
        blockers.append({
            "reason_code": "NOT_VERIFIED",
            "detail": f"Order status is {order.status}. Report generation starts at VERIFIED state."
        })

    # 2. MISSING_REQUIRED_RESULTS
    from apps.results.services.transitions import PLACEHOLDER_VALUES
    
    for item in order.items.all():
        for res in item.results.all():
            if res.test_parameter.is_required_for_verification:
                value = res.result_value
                is_absent = value is None or str(value).strip() == "" or str(value).lower() in PLACEHOLDER_VALUES
                if is_absent:
                    blockers.append({
                        "reason_code": "MISSING_REQUIRED_RESULTS",
                        "detail": f"Required result missing for {res.test_parameter.effective_parameter_name}",
                        "order_item_id": item.id,
                        "test_name": str(item),
                        "parameter_name": res.test_parameter.effective_parameter_name
                    })

    # 3. NO_PRINTABLE_ROWS
    # This will be more accurately checked in build_order_report_context,
    # but we can do a quick check here.
    has_printable = False
    for item in order.items.all():
        # Check if item has any printable results
        results_count = item.results.filter(
            test_parameter__is_printable=True,
            result_value__isnull=False
        ).count()
        
        config = item.test or item.panel
        print_if_any = getattr(config, 'print_if_any_result_present', True)
        
        if results_count > 0 or not print_if_any:
            has_printable = True
            break
    
    if not has_printable:
        blockers.append({
            "reason_code": "NO_PRINTABLE_ROWS",
            "detail": "No results are marked as printable or present for this order."
        })

    return blockers

def build_order_report_context(order_id):
    """
    Assemble deterministic report data context.
    """
    order = Order.objects.select_related('patient', 'ordered_by').prefetch_related(
        'items__test',
        'items__panel',
        'items__results__test_parameter',
        'items__results__test_parameter__parameter',
        'items__results__test_parameter__reference_ranges',
    ).get(id=order_id)
    
    patient = order.patient
    
    blocks = []
    for item in order.items.all():
        config = item.test or item.panel
        if not config:
            continue
            
        # Extract printing config
        print_group = getattr(config, 'print_group', None) or "General"
        print_priority = getattr(config, 'print_priority', 1000)
        force_separate_page = getattr(config, 'force_separate_page', False)
        footer_comments_static = getattr(config, 'footer_comments_static', None)
        omit_blank = getattr(config, 'omit_blank_parameters', True)
        print_if_any = getattr(config, 'print_if_any_result_present', True)
        
        # Build rows
        rows = []
        results = item.results.filter(test_parameter__is_printable=True).order_by('test_parameter__display_order')
        
        for res in results:
            if omit_blank and res.result_value is None:
                continue
                
            range_info = pick_reference_range(res.test_parameter, patient)
            
            rows.append({
                "name": res.test_parameter.effective_parameter_name,
                "result": res.result_value or "",
                "unit": res.test_parameter.unit,
                "reference_range": range_info.get("display", ""),
                "flag": res.flag,
                "is_abnormal": res.flag in ["H", "L", "C"]
            })
            
        if not rows and print_if_any:
            continue
            
        blocks.append({
            "id": item.id,
            "title": config.test_name if hasattr(config, 'test_name') else config.panel_name,
            "rows": rows,
            "print_group": print_group,
            "print_priority": print_priority,
            "force_separate_page": force_separate_page,
            "footer_comments_static": footer_comments_static
        })
        
    return {
        "order": order,
        "patient": patient,
        "blocks": blocks
    }

def build_page_plan(blocks):
    """
    Deterministic pagination and grouping plan.
    """
    # 1. Sort blocks by print_group, then print_priority, then title
    blocks.sort(key=lambda b: (b['print_group'], b['print_priority'], b['title']))
    
    pages = []
    current_page_blocks = []
    
    # MVP height limit: row count based
    # Header + patient info takes some space.
    # We'll use a simple threshold.
    MAX_LINES_PER_PAGE = 30 
    current_line_count = 0
    
    for block in blocks:
        block_lines = len(block['rows']) + 2 # Header + spacer
        if block['footer_comments_static']:
            block_lines += 2
            
        if block['force_separate_page']:
            # If we have something on current page, push it and start new
            if current_page_blocks:
                pages.append(current_page_blocks)
                current_page_blocks = []
                current_line_count = 0
            
            # This block gets its own page
            pages.append([block])
            continue
            
        # Check if block fits in current page
        if current_line_count + block_lines > MAX_LINES_PER_PAGE and current_page_blocks:
            pages.append(current_page_blocks)
            current_page_blocks = []
            current_line_count = 0
            
        current_page_blocks.append(block)
        current_line_count += block_lines
        
    if current_page_blocks:
        pages.append(current_page_blocks)
        
    return pages

def generate_v2_report(order_id):
    """
    Generate PDF using the V2 logic (printing rules, groups, pagination).
    """
    context = build_order_report_context(order_id)
    order = context['order']
    patient = context['patient']
    blocks = context['blocks']
    
    page_plan = build_page_plan(blocks)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    group_header_style = ParagraphStyle(
        "GroupHeader",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=10,
        spaceAfter=5,
        borderPadding=2,
        backColor=colors.HexColor("#f3f4f6")
    )
    block_title_style = ParagraphStyle(
        "BlockTitle",
        parent=styles["Heading3"],
        fontSize=10,
        textColor=colors.HexColor("#374151"),
        spaceBefore=6,
        spaceAfter=2
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontSize=9,
    )
    header_cell_style = ParagraphStyle(
        "HeaderCell",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold"
    )
    footer_comment_style = ParagraphStyle(
        "FooterComment",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        leftIndent=10
    )

    story = []
    
    # Simple Header
    story.append(Paragraph(f"<b>Laboratory Report - {order.lab_number}</b>", title_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Patient Info Table
    p_data = [
        [Paragraph(f"<b>Patient:</b> {patient.full_name}", cell_style), Paragraph(f"<b>Age/Gender:</b> {patient.age} / {patient.gender}", cell_style)],
        [Paragraph(f"<b>MRN:</b> {patient.mrn or patient.patient_id}", cell_style), Paragraph(f"<b>Visit ID:</b> {order.order_id}", cell_style)],
        [Paragraph(f"<b>Referred By:</b> {order.referred_by or 'Self'}", cell_style), Paragraph(f"<b>Date:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}", cell_style)]
    ]
    p_table = Table(p_data, colWidths=[3.5 * inch, 3.5 * inch])
    p_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1, -1), colors.whitesmoke),
    ]))
    story.append(p_table)
    story.append(Spacer(1, 0.2 * inch))

    last_group = None
    for page_index, page_blocks in enumerate(page_plan):
        if page_index > 0:
            story.append(PageBreak())
            
        for block in page_blocks:
            # Group Header if changed
            if block['print_group'] != last_group:
                story.append(Paragraph(block['print_group'], group_header_style))
                last_group = block['print_group']
            
            # Block Title
            story.append(Paragraph(block['title'], block_title_style))
            
            # Results Table
            t_data = [
                [Paragraph("Parameter", header_cell_style), Paragraph("Result", header_cell_style), Paragraph("Unit", header_cell_style), Paragraph("Ref Range", header_cell_style)]
            ]
            for row in block['rows']:
                res_val = row['result']
                if row['is_abnormal']:
                    res_val = f"<b>{res_val} ({row['flag']})</b>"
                
                t_data.append([
                    Paragraph(row['name'], cell_style),
                    Paragraph(str(res_val), cell_style),
                    Paragraph(row['unit'] or "", cell_style),
                    Paragraph(row['reference_range'] or "", cell_style)
                ])
                
            res_table = Table(t_data, colWidths=[2.5 * inch, 1.5 * inch, 1.0 * inch, 2.0 * inch])
            res_table.setStyle(TableStyle([
                ('INNERGRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
                ('BOX', (0,0), (-1,-1), 0.25, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (0,0), (-1, 0), colors.HexColor("#e5e7eb")),
            ]))
            story.append(res_table)
            
            # Static Footer Comment
            if block['footer_comments_static']:
                story.append(Spacer(1, 0.05 * inch))
                story.append(Paragraph(f"Note: {block['footer_comments_static']}", footer_comment_style))
                
            story.append(Spacer(1, 0.15 * inch))

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
