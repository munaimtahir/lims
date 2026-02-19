#!/bin/bash

# Script to create GitHub issues from workflow audit findings
# Usage: ./create_issues.sh

REPO="munaimtahir/lims"
ISSUES_DIR="_audit_evidence/workflow_audit/github_issues"

echo "Creating GitHub issues for LIMS Workflow Audit findings..."
echo ""

# Priority 1 Issues
echo "Creating Priority 1 (Critical) issues..."

# Issue 1: Dual Order Status Paths
echo "  - Creating Issue 1: Consolidate Dual Order Status Write Paths"
gh issue create \
  --repo "$REPO" \
  --title "[P1 Critical] Consolidate Dual Order Status Write Paths" \
  --label "bug,priority:critical,workflow,backend" \
  --body-file "$ISSUES_DIR/issue_p1_1_dual_order_status_paths.md"

# Issue 2: Direct Status Writes
echo "  - Creating Issue 2: Replace Direct Status Writes with Service Calls"
gh issue create \
  --repo "$REPO" \
  --title "[P1 Critical] Replace Direct Status Writes with Service Calls" \
  --label "bug,priority:critical,workflow,backend,audit-trail" \
  --body-file "$ISSUES_DIR/issue_p1_2_direct_status_writes.md"

# Issue 3: Frontend Status Mapping
echo "  - Creating Issue 3: Fix Frontend Status Mapping to Preserve Granularity"
gh issue create \
  --repo "$REPO" \
  --title "[P1 Critical] Fix Frontend Status Mapping to Preserve Granularity" \
  --label "bug,priority:high,frontend,backend,serializer,ui/ux" \
  --body-file "$ISSUES_DIR/issue_p1_3_frontend_status_mapping.md"

echo ""
echo "Creating Priority 2 (High) issues..."

# Issue 4: OrderItem Consistency
echo "  - Creating Issue 4: Add OrderItem Status Consistency Check and Auto-Sync"
gh issue create \
  --repo "$REPO" \
  --title "[P2 High] Add OrderItem Status Consistency Check and Auto-Sync" \
  --label "enhancement,priority:high,workflow,backend,data-integrity" \
  --body-file "$ISSUES_DIR/issue_p2_1_orderitem_consistency.md"

# Issue 5: Dispatch Service
echo "  - Creating Issue 5: Create Dispatch Status Transition Service for Audit Trail"
gh issue create \
  --repo "$REPO" \
  --title "[P2 High] Create Dispatch Status Transition Service for Audit Trail" \
  --label "enhancement,priority:high,workflow,backend,audit-trail" \
  --body-file "$ISSUES_DIR/issue_p2_2_dispatch_service.md"

echo ""
echo "✅ All issues created successfully!"
echo ""
echo "Summary:"
echo "  - 3 Priority 1 (Critical) issues created"
echo "  - 2 Priority 2 (High) issues created"
echo "  - Total effort estimate: 20 hours (~2.5 dev days)"
echo ""
echo "View all issues at: https://github.com/$REPO/issues"
