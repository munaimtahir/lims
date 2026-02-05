# Print Templates Guide

Print templates let admins configure report and receipt layouts from the UI without code changes.
Templates are managed in **Settings → Print Templates**.

## What Can Be Edited in the UI
- Template selection (Report or Receipt)
- Active template (one active per type)
- Paper size (A4 or Letter)
- Margins (inches)
- Font scale (0.5–2.0)
- Show/hide:
  - Logo
  - Header image
  - Footer image
  - Disclaimer
  - Signatures
- Disclaimer text
- Signatories list (name, title, registration no.)

## How Templates Affect PDFs
Report/receipt generation uses the **active** template for its type:
- **Margins** control page layout.
- **Font scale** adjusts all text sizing proportionally.
- **Show logo/header/footer** toggles use:
  - Logo: `SystemSettings.lab_logo`
  - Header/Footer images: `SystemSettings.report_header_image` / `SystemSettings.report_footer_image`
- **Disclaimer text** is printed only when enabled.
- **Signatories** render as signature blocks when enabled.

If optional images or signatories are missing, PDFs still render successfully.

## Default Templates
On first migration, the system seeds:
- `report_default` (active)
- `receipt_default` (active)

## Notes
- Only admins can edit templates.
- Changes apply immediately to newly generated PDFs.
