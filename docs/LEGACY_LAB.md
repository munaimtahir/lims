# Legacy Lab Reference

## Status

Legacy application code and phase artifacts are no longer stored in this repository to keep the production codebase clean and focused. If you need historical artifacts (legacy database dumps, seed spreadsheets, or previous implementation notes), retrieve them from your external backups or archival storage outside this repo.

## When You Still Need Legacy Data

If you need legacy data to bootstrap or compare behavior:

1. **Locate the archive outside this repository** (backup drive, artifact store, or shared archive).
2. **Extract the legacy test catalog** (Excel or CSV exports).
3. **Use the modern import workflow**:
   - Review the import guide in [`docs/catalog/README.md`](./catalog/README.md)
   - Use the template workflow from [`docs/catalog/templates/README.md`](./catalog/templates/README.md)

## What NOT to Do

❌ **Do not reintroduce legacy code into this repo**
- It increases attack surface and confusion.
- It makes production audits harder.

❌ **Do not run legacy services alongside this stack**
- Ports, dependencies, and schemas are not compatible.
- It risks breaking or contaminating the production environment.

## Modern Implementation References

All active code is in:
- **Backend**: `lims-backend/` (Django 5 + DRF)
- **Frontend**: `frontend/` (React 18 + TypeScript + Vite)

For architecture and workflows:
- [`docs/architecture/ARCHITECTURE.md`](./architecture/ARCHITECTURE.md)
- [`docs/WORKFLOW.md`](./WORKFLOW.md)
- [`docs/DATA_MODEL.md`](./DATA_MODEL.md)

## Questions?

Open an issue with:
- The legacy artifact you need (file name / system)
- The reason you need it
- Whether the modern import tooling can cover the same need
