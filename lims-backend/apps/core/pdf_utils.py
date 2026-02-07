"""
Shared utilities for PDF generation across the application.
"""
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Spacer


def add_report_image(story, image_field, max_width=6 * inch, spacer=0.15 * inch):
    """
    Add a header/footer image to the story with preserved aspect ratio.

    Args:
        story: The ReportLab story list to append elements to
        image_field: The image field (file or path) to render
        max_width: Maximum width for the image (default: 6 inches)
        spacer: Vertical space to add after the image (default: 0.15 inches)
    """
    if not image_field:
        return
    try:
        image_reader = ImageReader(image_field)
        img_width, img_height = image_reader.getSize()
        scale = min(max_width / img_width, 1)
        rendered = Image(
            image_reader, width=img_width * scale, height=img_height * scale
        )
        story.append(rendered)
        story.append(Spacer(1, spacer))
    except Exception:
        return
