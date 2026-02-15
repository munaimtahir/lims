# Results Workflow Fixes

- Updated `VERIFICATION_STATUS` to include 'ENTERED'.
- Enabled editing for DRAFT and ENTERED statuses.
- Implemented 'Return to Entry' functionality.
- Relaxed required fields check for non-required parameters.
- Grouped verification queue by Order.

## Verification Rules
- Absent results (empty/placeholder) do not block verification if parameter is not required.
- Only required parameters block verification.

## Return Behavior
- Return action moves status to ENTERED.
- Unlocks editing.
- Reverts Order Item status to IN_PROCESS if previously VERIFIED.
