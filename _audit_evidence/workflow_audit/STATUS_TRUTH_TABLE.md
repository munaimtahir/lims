# Status Truth Table

This table maps internal statuses across models and evaluates consistency.

| Step | Order Status | Sample Status | OrderItem Status | TestResult Status | Source of Truth |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Registration** | `NEW` | `PENDING` | `NEW` | N/A | `OrderSerializer` |
| **Payment** | `NEW` | `PENDING` | `NEW` | N/A | `OrderSerializer` |
| **Collection** | `COLLECTED` | `COLLECTED` | `NEW` | N/A | `OrderWorkflowService` |
| **Receipt/Accession** | `IN_PROCESS` | `RECEIVED` | `IN_PROCESS` | `READY` (or null) | `OrderWorkflowService` |
| **Result Entry (Draft)** | `IN_PROCESS` | `RECEIVED` | `IN_PROCESS` | `DRAFT` | `TestResultViewSet.bulk_entry` |
| **Result Entry (Comp)** | `IN_PROCESS` | `RECEIVED` | `IN_PROCESS` | `ENTERED` | `TestResultViewSet.bulk_entry` |
| **Verification** | `VERIFIED` | `RECEIVED` | `VERIFIED` | `VERIFIED` | `OrderWorkflowService` |
| **Publishing** | `PUBLISHED` | `RECEIVED` | `VERIFIED` | `FINAL` | `OrderWorkflowService` |

## Mismatch Evaluation

1. **OrderItem vs Order Consistency**:
   - `OrderItem.status` is updated via `update_order_item_status`.
   - `Order.status` is updated via `OrderWorkflowService._recalculate_order_status`.
   - **Risk**: If `update_order_item_status` is called without propagating to the order, they can get out of sync. Current code seems to propagate (mostly).

2. **Sample Skip Path**:
   - UI (`CollectionWorklistPage.tsx`) often moves samples directly from `PENDING` to `RECEIVED`.
   - `OrderWorkflowService` handles this by promoting order to `IN_PROCESS`.

3. **Status Aggregation Logic**:
   - `OrderWorkflowService._recalculate_order_status` is the central point.
   - However, `TestResultViewSet.worklist` implements its own logic (using annotates/aggregates) to determine what "needs results". This is a duplication of the "completion" logic.

4. **Missing Aggregate Updates**:
   - If a `TestResult` is deleted (though not common in normal workflow), does the order status revert?
   - If a `Sample` is rejected/deleted, does the order status revert?
   - `transition_sample_state` and `transition_result_state` both trigger recalculations, but bulk operations or direct DB writes (if any) might bypass this.
