# POLICY NOTE: Result Verification Authorization

## Rule Summary
In `apps/results/views.py`, the `verify` and `bulk_verify` actions now enforce the following permission rule:
> **Allowed for**: `is_pathologist` OR `is_admin`

## Comparison
| Action | Previous Rule | New Rule |
|--------|---------------|----------|
| `verify` | `is_staff` or `is_superuser` | `is_pathologist` or `is_admin` |
| `bulk_verify` | `is_staff` or `is_superuser` | `is_pathologist` or `is_admin` |
| `reject` | `is_pathologist` or `is_admin` | `is_pathologist` or `is_admin` |

## Analysis
The previous rule relied on Django's generic `is_staff` flag. In the context of a Laboratory Information Management System (LIMS), "verification" is a clinical quality control step that must be performed by a qualified medical professional (Pathologist).

- **Intentional Correctness**: The change is intentionally correct as it aligns with the business logic where clinical roles (Pathologist) are distinct from staff/management roles.
- **Consistency**: The change brings the `verify` endpoints in line with the `reject` endpoint, ensuring a uniform authorization policy for primary clinical result management.
- **Acceptability**: This is highly acceptable and follows best practices for domain-driven authorization in clinical software. Pathologists who may not have "staff" (admin panel) access can now perform their primary job duty (verifying results) through the application API.

## Recommendation
The current implementation is correct and should be maintained as is. No further patches are proposed for this logic.
