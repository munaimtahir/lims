# Template Update Report

## What changed
- Replaced the report layout in `lims-backend/apps/reports/utils.py` inside `generate_pdf_report()` with the locked "Al Shifa Diagnostic Laboratory" A4 template.
- Added helper functions `safe_text()`, `fmt_dt()`, and `fmt_age_gender()` to avoid crashes on missing optional fields.
- Added page numbering "Page X of Y" using a custom canvas.
- Preserved PrintTemplate margin configuration while keeping sane defaults.

## Field mapping
- Header
  - Lab name: `SystemSettings.lab_name` (fallback "Al Shifa Diagnostic Laboratory")
  - Address: `SystemSettings.lab_address` (fallback "Circular Road, Jaranwala")
  - Phone: `SystemSettings.lab_phone` (fallback "041-4312286")
  - Logo: `SystemSettings.lab_logo`
  - Optional header image: `SystemSettings.report_header_image`
- Report title
  - Single test: `"{test.test_name} Report"`
  - Single panel: `"{panel.panel_name} Report"`
  - Otherwise: `"Laboratory Report"`
- Demographics (two-column table, exact rows)
  - Ref #: `Order.order_id` (fallback `Order.id`)
  - MR #: `Patient.mrn` (fallback `Patient.patient_id`)
  - Patient Name: `Patient.get_full_name()`
  - Age/Gender: `Patient.age_years` (fallback `Patient.age`) + `Patient.gender`
  - Mobile: `Patient.phone`
  - Consultant: `Order.ordered_by.full_name`
  - Booking Date/Time: `Order.created_at`
  - Reporting Date/Time: latest `Result.verified_at` (fallback `timezone.now()`)
  - Sample Collected: earliest `Sample.collected_at` (fallback `Sample.received_at`)
  - Ref By: `Order.referred_by` (fallback `Patient.default_referred_by`)
- Results table
  - Source: `Order.items` -> `OrderItem.results`
  - Columns: Test | Result | Unit | Reference Range
  - Reference Range: `pick_reference_range(test_parameter, patient)`
- Impression (optional)
  - Uses `Order.interpretation` or `Order.impression` when present; omitted if empty.
- Footer
  - Disclaimer text set to the required exact string.
  - Signatories listed in required order.
  - Page numbering enabled on every page.

## Commands run + outputs
- Tests (host)
  - Command: `pytest lims-backend/apps/reports/tests -q`
  - Output: `/bin/bash: line 1: pytest: command not found`

- Tests (backend container)
  - Command: `docker compose exec -T backend pytest apps/reports/tests -q`
  - Output (error summary): `django.db.utils.ProgrammingError: relation "parameters_active_idx" does not exist`

- PDF generation (dev DB)
  - Command (inside container):
    `docker compose exec -T backend python - <<'PY' ... generate_pdf_report ... PY`
  - Output excerpt:
    - `Order: 9 ORD-20260207-0003 NEW`
    - `Wrote: /tmp/report_sample.pdf bytes: 16708`

- Copy artifact
  - `docker cp lims_backend:/tmp/report_sample.pdf DEPLOY_RUNS/TEMPLATE_UPDATE/report_sample.pdf`
  - `cp DEPLOY_RUNS/TEMPLATE_UPDATE/report_sample.pdf output/pdf/report_sample.pdf`

- Rendered PNGs (Poppler installed in container)
  - `docker compose exec -T --user root backend apt-get update`
  - `docker compose exec -T --user root backend apt-get install -y poppler-utils`
  - `docker compose exec -T backend sh -lc 'pdftoppm -png /tmp/report_sample.pdf /tmp/report_sample_pages/report_sample_page'`
  - `docker cp lims_backend:/tmp/report_sample_pages DEPLOY_RUNS/TEMPLATE_UPDATE/report_sample_pages`

## Verification
- Text extraction (pdfplumber) confirms:
  - Header values (lab name/address/phone)
  - Demographics rows present
  - Results table headers
  - Disclaimer text
  - Both signatories
  - Page numbering "Page X of Y"
- Rendered PNGs for visual inspection:
  - `DEPLOY_RUNS/TEMPLATE_UPDATE/report_sample_pages/report_sample_page-1.png`
  - `DEPLOY_RUNS/TEMPLATE_UPDATE/report_sample_pages/report_sample_page-2.png`

## Artifacts
- Sample PDF: `DEPLOY_RUNS/TEMPLATE_UPDATE/report_sample.pdf`
- Copy for convenience: `output/pdf/report_sample.pdf`
- Page renders: `DEPLOY_RUNS/TEMPLATE_UPDATE/report_sample_pages/`
