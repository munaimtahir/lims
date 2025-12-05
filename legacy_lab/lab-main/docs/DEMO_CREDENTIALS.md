# LIMS Demo Credentials & API Verification

## Quick Start with Demo Credentials

### Main Demo Accounts (Recommended)

These are the primary accounts for demonstration purposes:

#### 1. 🔑 Administrator Account
**Full system access for configuration and management**
```
Username: admin
Password: admin123
Role: ADMIN

Access to:
- All frontend pages and features
- User management
- Test catalog management
- System settings
- Complete workflow access
```

#### 2. 👥 Multi-Role Staff Account
**For reception, phlebotomy, and result entry workflows**
```
Username: staff
Password: staff123
Role: RECEPTION (with extended permissions)

Can perform:
- Patient registration
- Order creation
- Sample collection (phlebotomy)
- Sample receiving
- Basic result entry tasks
```

#### 3. ✅ Verification Account
**For pathologists to verify and publish results**
```
Username: verifier
Password: verify123
Role: PATHOLOGIST

Can perform:
- Result verification
- Result publishing
- Report generation
- Report download
```

---

## Additional Individual Role Accounts

For testing specific role-based access:

| Username | Password | Role | Primary Functions |
|----------|----------|------|-------------------|
| reception | reception123 | RECEPTION | Patient registration, Order creation |
| phlebotomy | phlebotomy123 | PHLEBOTOMY | Sample collection only |
| tech | tech123 | TECHNOLOGIST | Sample receiving, Result entry |
| pathologist | path123 | PATHOLOGIST | Result verification, Publishing, Reports |

---

## Setting Up Demo Data

### 1. Run the Seed Data Command

```bash
# Using Docker Compose
docker compose exec backend python manage.py seed_data

# Or directly in backend directory
cd backend
python manage.py seed_data
```

This command creates:
- ✓ All demo user accounts
- ✓ 5 test catalog items (CBC, LFT, RFT, Lipid Profile, HbA1c)
- ✓ 2 sample patients

### 2. Verify API Connections

Run the verification script to ensure all frontend-backend connections work:

```bash
# Using Docker
docker compose exec backend python verify_api_connections.py

# Or directly
cd backend
python verify_api_connections.py
```

This verifies:
- ✓ User authentication and roles
- ✓ Patient API endpoints and payloads
- ✓ Test catalog API
- ✓ Order management API
- ✓ Sample workflow API
- ✓ Result management API
- ✓ Report generation API
- ✓ All payload structures match frontend types

---

## Complete Workflow Test

### Test the entire LIMS workflow with demo credentials:

#### Step 1: Patient Registration (use `staff` account)
1. Login as `staff / staff123`
2. Go to **Lab** → **New Lab Slip**
3. Enter patient details:
   - CNIC: 12345-1234567-3
   - Phone: 03001112233
   - Full Name: Ali Hassan
   - Age: 30 years
   - Gender: Male
4. Select tests: CBC, LFT
5. Click **Create Order**

#### Step 2: Sample Collection (use `staff` account)
1. Navigate to **Phlebotomy**
2. Find the pending sample
3. Click **Collect** to mark as collected

#### Step 3: Sample Receiving (use `staff` or `tech` account)
1. In **Phlebotomy** page
2. Find the collected sample
3. Click **Receive** to accept in lab

#### Step 4: Result Entry (use `tech` account)
1. Login as `tech / tech123` (or use `staff`)
2. Go to **Result Entry**
3. Select a result from the list
4. Enter values:
   - Value: 14.5
   - Unit: g/dL
   - Reference Range: 13-17
5. Click **Enter Result**

#### Step 5: Result Verification (use `verifier` account)
1. Login as `verifier / verify123`
2. Go to **Verification**
3. Review the result
4. Check reference ranges
5. Click **Verify Result**

#### Step 6: Result Publishing (use `verifier` account)
1. Go to **Publishing**
2. Select verified results
3. Click **Publish Selected**

#### Step 7: Report Generation (use `verifier` account)
1. Go to **Reports**
2. Select the order with published results
3. Click **Generate Report**
4. Click **Download PDF**

---

## API Endpoint Verification

### Backend API Base URL

- **Development:** `http://localhost:8000/api`
- **Production (with nginx):** `http://localhost/api`

### Key API Endpoints

#### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/logout/` - User logout

#### Patients
- `GET /api/patients/` - List patients
- `POST /api/patients/` - Create patient
- `GET /api/patients/{id}/` - Get patient details

#### Orders
- `GET /api/orders/` - List orders
- `POST /api/orders/` - Create order
- `GET /api/orders/{id}/` - Get order details
- `POST /api/orders/{id}/cancel/` - Cancel order

#### Samples
- `GET /api/samples/` - List samples
- `POST /api/samples/{id}/collect/` - Mark sample as collected
- `POST /api/samples/{id}/receive/` - Mark sample as received
- `POST /api/samples/{id}/reject/` - Reject sample

#### Results
- `GET /api/results/` - List results
- `POST /api/results/{id}/enter/` - Mark result as entered
- `POST /api/results/{id}/verify/` - Verify result
- `POST /api/results/{id}/publish/` - Publish result

#### Reports
- `GET /api/reports/` - List reports
- `POST /api/reports/generate/{order_id}/` - Generate report
- `GET /api/reports/{id}/download/` - Download PDF

#### Dashboard
- `GET /api/dashboard/analytics/` - Get analytics data

---

## Payload Examples

### Patient Creation Payload
```json
{
  "full_name": "Ali Hassan",
  "father_name": "Hassan Ahmed",
  "sex": "M",
  "phone": "03001112233",
  "cnic": "12345-1234567-3",
  "age_years": 30,
  "age_months": 0,
  "age_days": 0
}
```

### Order Creation Payload
```json
{
  "patient": 1,
  "test_ids": [1, 2],
  "priority": "ROUTINE",
  "notes": "Fasting required"
}
```

### Result Entry Payload
```json
{
  "value": "14.5",
  "unit": "g/dL",
  "reference_range": "13-17",
  "notes": "Normal hemoglobin level"
}
```

---

## Frontend-Backend Connection Checklist

### ✅ Verified Connections

- [x] **Authentication:** JWT login, refresh, logout
- [x] **Patient API:** List, create, detail with correct payload structure
- [x] **Order API:** Create orders with test_ids array
- [x] **Sample API:** Collect, receive, reject with status updates
- [x] **Result API:** Entry, verification, publishing workflow
- [x] **Report API:** Generation and PDF download
- [x] **Dashboard API:** Analytics with date range filtering
- [x] **User API:** User management and role assignment
- [x] **Test Catalog API:** List and manage tests

### Payload Compatibility

All frontend TypeScript types match backend Django serializer fields:

- ✓ Patient interface matches PatientSerializer
- ✓ Order interface matches OrderSerializer
- ✓ Sample interface matches SampleSerializer
- ✓ Result interface matches ResultSerializer
- ✓ Report interface matches ReportSerializer

---

## Troubleshooting

### Issue: Cannot login with demo credentials

**Solution:**
```bash
# Re-run seed data command
docker compose exec backend python manage.py seed_data
```

### Issue: API returns 401 Unauthorized

**Solution:**
- Check that JWT tokens are being sent in Authorization header
- Verify token hasn't expired (auto-refresh should handle this)
- Try logging out and logging back in

### Issue: Order creation fails

**Solution:**
- Ensure test catalog has items (run `seed_data`)
- Verify patient exists or provide patient data
- Check that `test_ids` is an array of valid test IDs

### Issue: Sample status not updating

**Solution:**
- Verify user has correct role (PHLEBOTOMY, TECHNOLOGIST, or ADMIN)
- Check that sample is in correct state for the action
- Ensure backend API is running

### Issue: Report generation fails

**Solution:**
- Verify all results for the order are in PUBLISHED status
- Check that user has PATHOLOGIST or ADMIN role
- Ensure PDF generation library is installed in backend

---

## Testing with cURL

### Test Authentication
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Test Patient List (with token)
```bash
curl -X GET http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Test Order Creation
```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"patient":1,"test_ids":[1,2],"priority":"ROUTINE"}'
```

---

## Security Notes

⚠️ **Important:** These demo credentials are for development and testing only.

**For Production Deployment:**

1. **Change all passwords** immediately
2. Use `python manage.py createsuperuser` to create secure admin
3. Disable or remove demo accounts
4. Use strong, unique passwords
5. Enable HTTPS/TLS
6. Configure proper CORS settings
7. Set up proper JWT token expiry times

---

## Support

For issues or questions:

1. Run verification script: `python verify_api_connections.py`
2. Check backend logs: `docker compose logs backend`
3. Check frontend console in browser DevTools
4. Review API documentation: `docs/API.md`
5. Check frontend documentation: `docs/FRONTEND_RUN.md`

---

*Last Updated: November 2025*  
*Al Shifa Laboratory LIMS - Demo Credentials & API Verification Guide*
