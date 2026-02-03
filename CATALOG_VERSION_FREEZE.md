# Catalog Version Freeze

- **Version Identifier:** catalog-core-freeze cd11511 (2026-02-03)
- **Status:** Production-stable, feature-frozen.

## What Is Frozen
- Catalog business logic, data models, API contracts, and import/export semantics.
- Endpoint surface and request/response shapes.
- Catalog data schemas and validations.

## What Changes Are Allowed
- Operational configuration only (environment variables, secrets rotation, domain/origin lists).
- Infrastructure and deployment plumbing (volumes, logging destinations, TLS/proxy configuration).
- Security patches that do not alter catalog behavior or contracts.
- Test tooling parity and CI configuration.

## Change Approval
- Product/Engineering lead sign-off required for any exception to the freeze.
- Platform/Ops may adjust infrastructure config within the allowed scope above without product approval.
- Any proposal impacting catalog logic or API contracts requires joint approval from Product + Engineering + QA.

## Notes
- Host backup paths for durability: `./lims-backend/media` (user assets) and `./logs` (application logs). Ensure these are included in backup policy alongside database and Redis persistence volumes.
- Freeze remains in effect until superseded by a formal unfreeze or new tagged release.
