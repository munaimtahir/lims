from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
from apps.orders.models import Order


def generate_pdf_report(order_id):
    """
    Generate a PDF report for a given order.

    This function creates a simple PDF with the order details and test results.

    Args:
        order_id (int): The ID of the order to generate the report for.

    Returns:
        bytes: The content of the generated PDF file.

    Raises:
        ValueError: If the order is not found.
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise ValueError("Order not found")

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "Laboratory Report")

    p.setFont("Helvetica", 12)
    p.drawString(100, 780, f"Order ID: {order.order_id}")
    p.drawString(100, 760, f"Patient: {order.patient.get_full_name()}")
    p.drawString(100, 740, f"Date: {order.created_at.strftime('%Y-%m-%d')}")

    # Results
    y = 700
    p.drawString(100, y, "Test Results:")
    y -= 20

    for item in order.items.all():
        test_name = item.test.test_name if item.test else item.panel.panel_name
        p.setFont("Helvetica-Bold", 10)
        p.drawString(100, y, f"- {test_name}")
        y -= 15

        for result in item.results.all():
            p.setFont("Helvetica", 10)
            param = result.test_parameter
            text = f"{param.parameter_name}: {result.result_value} {param.unit} ({result.flag})"
            p.drawString(120, y, text)
            y -= 15

    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()
    return pdf
