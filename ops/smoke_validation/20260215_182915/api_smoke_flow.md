# API Smoke Flow

Curl-based verification of the LIMS workflow. Run with:

```bash
./scripts/smoke_flow.sh
```

Or set `BASE_URL` for a different target:

```bash
BASE_URL=http://localhost:8012 ./scripts/smoke_flow.sh
```

## Steps

1. **Login** – POST `/api/v1/auth/login/` with username/password
2. **Create Patient** – POST `/api/v1/patients/` with first_name, last_name, gender, phone, date_of_birth
3. **Get Tests** – GET `/api/v1/laboratory/tests/`
4. **Create Order** – POST `/api/v1/orders/orders/` with patient, test_ids
5. **Record Payment** – POST `/api/v1/payments/` with order, amount, payment_method
6. **Sample Collection** – PATCH `/api/v1/samples/{id}/` with status=COLLECTED
7. **Result Entry** – POST `/api/v1/results/bulk_entry/` with order_item, test_parameter, result_value
8. **Verify Result** – POST `/api/v1/results/{id}/verify/`
9. **Report** – POST `/api/v1/reports/generate/` with order_id, is_final; GET `/api/v1/reports/{id}/download/`
10. **Receipt** – GET `/api/v1/payments/{id}/receipt/`
