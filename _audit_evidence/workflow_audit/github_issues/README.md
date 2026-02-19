# GitHub Issues for Workflow Audit Findings

This directory contains GitHub issue templates for Priority 1 and Priority 2 findings from the LIMS Workflow Audit.

## Contents

- `GITHUB_ISSUES_TO_CREATE.md` - Master document with all 5 issues detailed
- `create_issues.sh` - Automated script to create all issues via GitHub CLI
- Individual issue body files for easy creation:
  - `issue_p1_1_dual_order_status_paths.md`
  - `issue_p1_2_direct_status_writes.md`
  - `issue_p1_3_frontend_status_mapping.md`
  - `issue_p2_1_orderitem_consistency.md`
  - `issue_p2_2_dispatch_service.md`

## Issues Summary

### Priority 1 (Critical) - 3 issues, 13 hours total

1. **[P1 Critical] Consolidate Dual Order Status Write Paths** (4 hours)
   - Labels: `bug`, `priority:critical`, `workflow`, `backend`
   - Two different service functions write Order.status inconsistently

2. **[P1 Critical] Replace Direct Status Writes with Service Calls** (6 hours)
   - Labels: `bug`, `priority:critical`, `workflow`, `backend`, `audit-trail`
   - Multiple locations bypass transition services and audit trail

3. **[P1 Critical] Fix Frontend Status Mapping to Preserve Granularity** (3 hours)
   - Labels: `bug`, `priority:high`, `frontend`, `backend`, `serializer`, `ui/ux`
   - Status mapping loses distinction between DRAFT/ENTERED and VERIFIED/FINAL

### Priority 2 (High) - 2 issues, 7 hours total

4. **[P2 High] Add OrderItem Status Consistency Check and Auto-Sync** (4 hours)
   - Labels: `enhancement`, `priority:high`, `workflow`, `backend`, `data-integrity`
   - OrderItem status may fall out of sync with results

5. **[P2 High] Create Dispatch Status Transition Service for Audit Trail** (3 hours)
   - Labels: `enhancement`, `priority:high`, `workflow`, `backend`, `audit-trail`
   - Missing service layer for dispatch status transitions

## How to Create Issues

### Option 1: Automated Creation (Recommended)

```bash
cd _audit_evidence/workflow_audit/github_issues
./create_issues.sh
```

**Prerequisites:**
- GitHub CLI (`gh`) installed and authenticated
- Write access to the repository

### Option 2: Manual Creation via GitHub UI

1. Go to https://github.com/munaimtahir/lims/issues/new
2. Copy the title from the list above
3. Copy the content from the corresponding `.md` file
4. Add the specified labels
5. Submit the issue

### Option 3: Individual Creation via CLI

```bash
# Example for Issue 1
gh issue create \
  --repo "munaimtahir/lims" \
  --title "[P1 Critical] Consolidate Dual Order Status Write Paths" \
  --label "bug,priority:critical,workflow,backend" \
  --body-file "issue_p1_1_dual_order_status_paths.md"
```

Repeat for each issue file.

## Labels Used

Make sure these labels exist in your repository:
- `bug` - Bug report
- `enhancement` - Enhancement/feature request
- `priority:critical` - Critical priority (P1)
- `priority:high` - High priority (P2)
- `workflow` - Workflow-related
- `backend` - Backend code
- `frontend` - Frontend code
- `audit-trail` - Audit trail related
- `data-integrity` - Data integrity concern
- `serializer` - Django serializer related
- `ui/ux` - User interface/experience

## References

All issues reference the complete audit documentation:
- `_audit_evidence/workflow_audit/FINDINGS_AND_FIX_PLAN.md` - Detailed fix plans
- `_audit_evidence/workflow_audit/STATUS_TRUTH_TABLE.md` - Status analysis
- `_audit_evidence/workflow_audit/WORKFLOW_CALL_GRAPH.md` - Complete workflow trace

## Notes

- These issues were generated from a comprehensive workflow audit conducted on 2026-02-19
- Total estimated effort: 20 hours (~2.5 developer days)
- All issues include detailed problem descriptions, evidence, proposed fixes, and verification checklists
- Issues are prioritized based on severity and impact
