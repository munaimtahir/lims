# Expected Results (Tests + Panels)

Result entry depends on deterministic expected rows for each `OrderItem`.

## Expected Parameters
For a given `OrderItem`:
- **Single Test**: use `Test.parameters` ordered by `display_order`, then `id`.
- **Panel**: iterate tests in the panel (stable `test_name`, `id` ordering) and append
  each test’s parameters in the same deterministic order.
- Each expected row includes a `reference_display` computed from the shared range selector.

## Ensure Rows
The `/api/v1/results/ensure/?order_item_id=...` endpoint creates missing `TestResult`
rows using the expected parameter list and **never overwrites** existing results. It is
safe to call repeatedly (idempotent).

## Smoke Checks
1. Create a test with parameters and add `ReferenceRange` rows (age + gender).
2. Place an order for that test or a panel that contains it.
3. Open result entry for the order item → expected rows appear immediately.
4. Enter an out-of-range value → flag shows `L`, `H`, or `C`.
5. Generate the PDF report → the same reference range display is shown.
