# Report v2 Layout Update

## Summary
- Implemented locked A4 Lab Report v2 layout in `lims-backend/apps/reports/utils.py` with compact demographics grid and panelized results table.
- Added helper builders: `build_patient_identity_table`, `build_results_flowables`, `build_panel_block`, and custom `PanelTable` to manage continued headers.
- Abnormal results now bold with directional arrows (↑/↓) when outside reference range or flagged.
- Page-break safety: panel header + first row kept together; continued pages repeat header with "(continued)" label; rows are not split.
- Impression remains conditional; locked footer, signatories, and page numbering preserved.
- Compliance toggles added to PrintTemplate config and UI (Settings → Print Templates → Compliance & Flags): patient DOB, repeat IDs per page, specimen details, ordering/verified lines, method/decision limits, critical annotations, QC/confidentiality statements, and revision banner.

## Evidence
- Reduced patient block height; results start higher on page 1.
- Multipage panel shows repeated header with "(continued)" and no orphaned headers.
- Generated PDFs:
  - `DEPLOY_RUNS/REPORT_V2_FORMAT/report_single.pdf`
  - `DEPLOY_RUNS/REPORT_V2_FORMAT/report_multipanel.pdf`

## Notes on page-break enforcement
- Uses `CondPageBreak` to ensure space before each panel.
- `PanelTable.split` rewrites headers on splits to append "(continued)".
- `repeatRows=2` for panel tables so column headers repeat on subsequent pages.
