# Laboratory Information Management System
## API Design Specification

---

## API Overview

**Base URL**: `http://your-domain.com/api/v1/`  
**Protocol**: HTTPS  
**Format**: JSON  
**Authentication**: JWT (JSON Web Tokens)

---

## Authentication Endpoints

### 1. Login

**Endpoint**: `POST /auth/login/`

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "john_doe",
      "full_name": "John Doe",
      "email": "john@example.com",
      "role": "Lab Technician"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "Login successful"
}
```

---

### 2. Logout

**Endpoint**: `POST /auth/logout/`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

### 3. Refresh Token

**Endpoint**: `POST /auth/refresh/`

**Request Body**:
```json
{
  "refresh_token": "string"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "access_token": "new_access_token_here"
  }
}
```

---

## Patient Management Endpoints

### 1. List Patients

**Endpoint**: `GET /patients/`

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `search` (string): Search by name, phone, or patient ID
- `ordering` (string): Sort field (e.g., `-created_at` for descending)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "count": 150,
    "next": "http://api/patients/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "patient_id": "P-2024-00001",
        "first_name": "Ahmed",
        "last_name": "Khan",
        "date_of_birth": "1990-05-15",
        "age": 34,
        "gender": "Male",
        "phone": "+92-300-1234567",
        "email": "ahmed@example.com",
        "created_at": "2024-11-25T10:30:00Z"
      }
    ]
  }
}
```

---

### 2. Get Patient Detail

**Endpoint**: `GET /patients/{id}/`

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "patient_id": "P-2024-00001",
    "first_name": "Ahmed",
    "last_name": "Khan",
    "date_of_birth": "1990-05-15",
    "age": 34,
    "gender": "Male",
    "phone": "+92-300-1234567",
    "email": "ahmed@example.com",
    "national_id": "12345-1234567-1",
    "address": "House 123, Street 45, Islamabad",
    "created_at": "2024-11-25T10:30:00Z",
    "updated_at": "2024-11-25T10:30:00Z",
    "total_orders": 5,
    "last_visit": "2024-11-20T14:00:00Z"
  }
}
```

---

### 3. Create Patient

**Endpoint**: `POST /patients/`

**Request Body**:
```json
{
  "first_name": "Ahmed",
  "last_name": "Khan",
  "date_of_birth": "1990-05-15",
  "gender": "Male",
  "phone": "+92-300-1234567",
  "email": "ahmed@example.com",
  "national_id": "12345-1234567-1",
  "address": "House 123, Street 45, Islamabad"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "patient_id": "P-2024-00001",
    "first_name": "Ahmed",
    "last_name": "Khan",
    ...
  },
  "message": "Patient registered successfully"
}
```

---

### 4. Update Patient

**Endpoint**: `PATCH /patients/{id}/`

**Request Body** (partial update):
```json
{
  "phone": "+92-300-7654321",
  "address": "New Address"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "patient_id": "P-2024-00001",
    ...updated fields
  },
  "message": "Patient updated successfully"
}
```

---

### 5. Get Patient History

**Endpoint**: `GET /patients/{id}/history/`

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "patient": {
      "id": 1,
      "patient_id": "P-2024-00001",
      "full_name": "Ahmed Khan"
    },
    "orders": [
      {
        "order_id": "ORD-2024-00123",
        "order_date": "2024-11-20T14:00:00Z",
        "total_amount": 2500,
        "status": "Completed",
        "tests": ["CBC", "LFT", "RFT"]
      }
    ],
    "test_comparisons": {
      "Hemoglobin": [
        {"date": "2024-11-20", "value": 14.5, "unit": "g/dL"},
        {"date": "2024-10-15", "value": 14.2, "unit": "g/dL"},
        {"date": "2024-09-10", "value": 14.8, "unit": "g/dL"}
      ]
    }
  }
}
```

---

## Test Catalog Endpoints

### 1. List Test Categories

**Endpoint**: `GET /laboratory/categories/`

**Response** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Hematology",
      "description": "Blood cell analysis",
      "test_count": 15
    },
    {
      "id": 2,
      "name": "Clinical Chemistry",
      "description": "Biochemical analysis",
      "test_count": 35
    }
  ]
}
```

---

### 2. List Tests

**Endpoint**: `GET /laboratory/tests/`

**Query Parameters**:
- `category` (int): Filter by category ID
- `search` (string): Search by test name or code
- `is_active` (bool): Filter active tests

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "count": 100,
    "results": [
      {
        "id": 1,
        "test_code": "CBC",
        "test_name": "Complete Blood Count",
        "loinc_code": "58410-2",
        "category": "Hematology",
        "price": 800,
        "sample_type": "EDTA Blood",
        "sample_volume": "3-5 mL",
        "turnaround_time": 4,
        "is_active": true,
        "parameter_count": 14
      }
    ]
  }
}
```

---

### 3. Get Test Detail with Parameters

**Endpoint**: `GET /laboratory/tests/{id}/`

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "test_code": "CBC",
    "test_name": "Complete Blood Count",
    "loinc_code": "58410-2",
    "category": {
      "id": 1,
      "name": "Hematology"
    },
    "price": 800,
    "sample_type": "EDTA Blood",
    "sample_volume": "3-5 mL",
    "turnaround_time": 4,
    "parameters": [
      {
        "id": 1,
        "parameter_name": "Hemoglobin",
        "loinc_code": "718-7",
        "unit": "g/dL",
        "reference_min_male": 13.5,
        "reference_max_male": 17.5,
        "reference_min_female": 12.0,
        "reference_max_female": 15.5,
        "critical_low": 7.0,
        "critical_high": 20.0,
        "decimal_places": 1
      }
    ]
  }
}
```

---

### 4. List Test Panels

**Endpoint**: `GET /laboratory/panels/`

**Response** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "panel_code": "LFT",
      "panel_name": "Liver Function Test",
      "category": "Clinical Chemistry",
      "price": 1200,
      "sample_type": "Serum",
      "turnaround_time": 4,
      "tests": [
        {"test_code": "BILT", "test_name": "Total Bilirubin"},
        {"test_code": "BILD", "test_name": "Direct Bilirubin"},
        {"test_code": "ALT", "test_name": "ALT (SGPT)"}
      ],
      "is_active": true
    }
  ]
}
```

---

## Order Management Endpoints

### 1. Create Order

**Endpoint**: `POST /orders/`

**Request Body**:
```json
{
  "patient_id": 1,
  "priority": "Routine",
  "referring_doctor": "Dr. Ali Ahmed",
  "special_instructions": "Patient is fasting",
  "items": [
    {
      "item_type": "Panel",
      "panel_id": 1
    },
    {
      "item_type": "Test",
      "test_id": 15
    }
  ],
  "discount_amount": 0
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": 123,
    "order_id": "ORD-2024-00123",
    "patient": {
      "id": 1,
      "patient_id": "P-2024-00001",
      "full_name": "Ahmed Khan"
    },
    "order_date": "2024-11-25T14:30:00Z",
    "priority": "Routine",
    "status": "Pending Payment",
    "items": [
      {
        "id": 1,
        "item_type": "Panel",
        "item_name": "Liver Function Test",
        "price": 1200
      },
      {
        "id": 2,
        "item_type": "Test",
        "item_name": "Thyroid Profile",
        "price": 2500
      }
    ],
    "total_amount": 3700,
    "discount_amount": 0,
    "final_amount": 3700,
    "amount_paid": 0,
    "balance_due": 3700
  },
  "message": "Order created successfully"
}
```

---

### 2. List Orders

**Endpoint**: `GET /orders/`

**Query Parameters**:
- `status` (string): Filter by status
- `patient` (int): Filter by patient ID
- `date_from` (date): Filter from date
- `date_to` (date): Filter to date
- `priority` (string): Filter by priority
- `search` (string): Search by order ID

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "count": 50,
    "results": [
      {
        "id": 123,
        "order_id": "ORD-2024-00123",
        "patient": {
          "patient_id": "P-2024-00001",
          "full_name": "Ahmed Khan"
        },
        "order_date": "2024-11-25T14:30:00Z",
        "priority": "Routine",
        "status": "Sample Collected",
        "final_amount": 3700,
        "amount_paid": 3700,
        "balance_due": 0,
        "item_count": 2
      }
    ]
  }
}
```

---

### 3. Get Order Detail

**Endpoint**: `GET /orders/{id}/`

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": 123,
    "order_id": "ORD-2024-00123",
    "patient": {
      "id": 1,
      "patient_id": "P-2024-00001",
      "full_name": "Ahmed Khan",
      "age": 34,
      "gender": "Male",
      "phone": "+92-300-1234567"
    },
    "order_date": "2024-11-25T14:30:00Z",
    "priority": "Routine",
    "referring_doctor": "Dr. Ali Ahmed",
    "special_instructions": "Patient is fasting",
    "status": "Results Entered",
    "items": [...],
    "total_amount": 3700,
    "discount_amount": 0,
    "final_amount": 3700,
    "payments": [
      {
        "id": 1,
        "receipt_number": "RCP-2024-00123",
        "amount_paid": 3700,
        "payment_method": "Cash",
        "payment_date": "2024-11-25T14:35:00Z",
        "received_by": "Cashier Name"
      }
    ],
    "sample_collection": {
      "collected_at": "2024-11-25T14:40:00Z",
      "collected_by": "Phlebotomist Name",
      "barcode": "BC-2024-00123"
    },
    "created_by": "Reception Staff",
    "created_at": "2024-11-25T14:30:00Z"
  }
}
```

---

### 4. Update Order Status

**Endpoint**: `PATCH /orders/{id}/status/`

**Request Body**:
```json
{
  "status": "Sample Collected"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": 123,
    "order_id": "ORD-2024-00123",
    "status": "Sample Collected"
  },
  "message": "Order status updated"
}
```

---

### 5. Cancel Order

**Endpoint**: `POST /orders/{id}/cancel/`

**Request Body**:
```json
{
  "reason": "Patient requested cancellation",
  "refund_amount": 3700
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "order_id": "ORD-2024-00123",
    "status": "Cancelled",
    "refund_amount": 3700
  },
  "message": "Order cancelled successfully"
}
```

---

## Payment Endpoints

### 1. Record Payment

**Endpoint**: `POST /payments/`

**Request Body**:
```json
{
  "order_id": 123,
  "amount_paid": 3700,
  "payment_method": "Cash",
  "notes": ""
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "receipt_number": "RCP-2024-00123",
    "order": {
      "order_id": "ORD-2024-00123"
    },
    "amount_paid": 3700,
    "payment_method": "Cash",
    "payment_date": "2024-11-25T14:35:00Z",
    "received_by": {
      "id": 5,
      "full_name": "Cashier Name"
    },
    "receipt_url": "/media/receipts/RCP-2024-00123.pdf"
  },
  "message": "Payment recorded successfully"
}
```

---

### 2. Get Receipt

**Endpoint**: `GET /payments/{id}/receipt/`

**Response**: PDF file download

---

## Sample Collection Endpoints

### 1. Record Sample Collection

**Endpoint**: `POST /samples/`

**Request Body**:
```json
{
  "order_id": 123,
  "sample_type": "EDTA Blood",
  "barcode": "BC-2024-00123",
  "notes": "Sample collected successfully"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "order_id": 123,
    "sample_type": "EDTA Blood",
    "collection_date": "2024-11-25T14:40:00Z",
    "collected_by": {
      "id": 7,
      "full_name": "Phlebotomist Name"
    },
    "barcode": "BC-2024-00123"
  },
  "message": "Sample collection recorded"
}
```

---

### 2. Get Pending Collections

**Endpoint**: `GET /samples/pending/`

**Response** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "order_id": "ORD-2024-00123",
      "patient_name": "Ahmed Khan",
      "required_samples": ["EDTA Blood", "Serum"],
      "priority": "Routine",
      "order_time": "2024-11-25T14:30:00Z"
    }
  ]
}
```

---

## Result Entry Endpoints

### 1. Get Work List

**Endpoint**: `GET /results/worklist/`

**Query Parameters**:
- `status` (string): Filter by status (e.g., "Pending", "In Progress")
- `test_category` (int): Filter by test category

**Response** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "order_id": "ORD-2024-00123",
      "patient": {
        "patient_id": "P-2024-00001",
        "full_name": "Ahmed Khan",
        "age": 34,
        "gender": "Male"
      },
      "tests": [
        {
          "test_id": 1,
          "test_name": "Complete Blood Count",
          "sample_type": "EDTA Blood",
          "parameter_count": 14,
          "result_status": "Pending"
        }
      ],
      "sample_collected_at": "2024-11-25T14:40:00Z",
      "priority": "Routine"
    }
  ]
}
```

---

### 2. Enter Results

**Endpoint**: `POST /results/entry/`

**Request Body**:
```json
{
  "order_id": 123,
  "test_id": 1,
  "results": [
    {
      "parameter_id": 1,
      "result_value": "14.5"
    },
    {
      "parameter_id": 2,
      "result_value": "4.8"
    }
  ],
  "comments": "All parameters within normal limits"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "order_id": "ORD-2024-00123",
    "test_id": 1,
    "results_entered": 14,
    "flags": {
      "critical": 0,
      "high": 1,
      "low": 0
    },
    "entered_by": "Tech Name",
    "entered_at": "2024-11-25T16:00:00Z",
    "status": "Pending Verification"
  },
  "message": "Results entered successfully"
}
```

---

### 3. Get Results for Verification

**Endpoint**: `GET /results/pending-verification/`

**Response** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "order_id": "ORD-2024-00123",
      "patient": {
        "patient_id": "P-2024-00001",
        "full_name": "Ahmed Khan",
        "age": 34,
        "gender": "Male"
      },
      "tests": [
        {
          "test_name": "Complete Blood Count",
          "entered_by": "Tech Name",
          "entered_at": "2024-11-25T16:00:00Z",
          "has_critical_values": false,
          "has_abnormal_values": true
        }
      ]
    }
  ]
}
```

---

### 4. Verify Results

**Endpoint**: `POST /results/verify/`

**Request Body**:
```json
{
  "order_id": 123,
  "test_id": 1,
  "verification_status": "Approved",
  "pathologist_comments": "Results reviewed and approved",
  "digital_signature": "base64_encoded_signature_image"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "order_id": "ORD-2024-00123",
    "test_id": 1,
    "verification_status": "Approved",
    "verified_by": "Dr. Pathologist Name",
    "verified_at": "2024-11-25T17:00:00Z"
  },
  "message": "Results verified successfully"
}
```

---

### 5. Request Retest

**Endpoint**: `POST /results/retest/`

**Request Body**:
```json
{
  "order_id": 123,
  "test_id": 1,
  "reason": "Questionable hemoglobin value, please repeat"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "order_id": "ORD-2024-00123",
    "test_id": 1,
    "status": "Retest Requested",
    "reason": "Questionable hemoglobin value, please repeat"
  },
  "message": "Retest requested"
}
```

---

## Report Generation Endpoints

### 1. Generate Report

**Endpoint**: `POST /reports/generate/`

**Request Body**:
```json
{
  "order_id": 123
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "report_number": "RPT-2024-00123",
    "order_id": "ORD-2024-00123",
    "generated_at": "2024-11-25T17:05:00Z",
    "generated_by": "Pathologist Name",
    "report_url": "/media/reports/RPT-2024-00123.pdf"
  },
  "message": "Report generated successfully"
}
```

---

### 2. Get Report List

**Endpoint**: `GET /reports/`

**Query Parameters**:
- `date_from`, `date_to`: Date range
- `patient`: Patient ID
- `search`: Search by report number

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "count": 100,
    "results": [
      {
        "id": 1,
        "report_number": "RPT-2024-00123",
        "order": {
          "order_id": "ORD-2024-00123"
        },
        "patient": {
          "patient_id": "P-2024-00001",
          "full_name": "Ahmed Khan"
        },
        "generated_at": "2024-11-25T17:05:00Z",
        "delivered_at": null,
        "report_url": "/media/reports/RPT-2024-00123.pdf"
      }
    ]
  }
}
```

---

### 3. Download Report

**Endpoint**: `GET /reports/{id}/download/`

**Response**: PDF file download

---

### 4. Mark Report as Delivered

**Endpoint**: `POST /reports/{id}/deliver/`

**Request Body**:
```json
{
  "delivered_to": "Ahmed Khan",
  "delivery_method": "In Person"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "report_number": "RPT-2024-00123",
    "delivered_at": "2024-11-26T10:00:00Z",
    "delivered_to": "Ahmed Khan"
  },
  "message": "Report delivery recorded"
}
```

---

## Dashboard & Statistics Endpoints

### 1. Get Dashboard Data

**Endpoint**: `GET /dashboard/`

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "today": {
      "total_orders": 25,
      "pending_collections": 5,
      "pending_results": 8,
      "pending_verification": 3,
      "completed": 9,
      "total_revenue": 45000
    },
    "this_month": {
      "total_orders": 450,
      "total_revenue": 825000,
      "average_turnaround_time": 5.2
    },
    "pending_actions": {
      "collections": 5,
      "result_entry": 8,
      "verification": 3,
      "report_delivery": 2
    },
    "top_tests": [
      {"test_name": "Complete Blood Count", "count": 150},
      {"test_name": "Liver Function Test", "count": 120}
    ]
  }
}
```

---

### 2. Get Revenue Report

**Endpoint**: `GET /reports/revenue/`

**Query Parameters**:
- `date_from`, `date_to`: Date range
- `group_by`: "day" | "week" | "month"

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "total_revenue": 825000,
    "total_orders": 450,
    "average_order_value": 1833,
    "breakdown": [
      {
        "date": "2024-11-01",
        "orders": 15,
        "revenue": 27500
      },
      {
        "date": "2024-11-02",
        "orders": 18,
        "revenue": 33000
      }
    ],
    "payment_methods": {
      "Cash": 650000,
      "Card": 150000,
      "Bank Transfer": 25000
    }
  }
}
```

---

### 3. Get Test Statistics

**Endpoint**: `GET /reports/test-statistics/`

**Query Parameters**:
- `date_from`, `date_to`: Date range

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "most_ordered_tests": [
      {
        "test_name": "Complete Blood Count",
        "order_count": 150,
        "revenue": 120000
      }
    ],
    "least_ordered_tests": [...],
    "average_turnaround_by_test": [
      {
        "test_name": "CBC",
        "avg_hours": 4.2
      }
    ]
  }
}
```

---

## User Management Endpoints (Admin Only)

### 1. List Users

**Endpoint**: `GET /users/`

**Response** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "username": "john_doe",
      "full_name": "John Doe",
      "email": "john@example.com",
      "role": "Lab Technician",
      "is_active": true,
      "last_login": "2024-11-25T14:00:00Z"
    }
  ]
}
```

---

### 2. Create User

**Endpoint**: `POST /users/`

**Request Body**:
```json
{
  "username": "jane_smith",
  "password": "SecurePassword123!",
  "full_name": "Jane Smith",
  "email": "jane@example.com",
  "role": "Receptionist"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": 2,
    "username": "jane_smith",
    "full_name": "Jane Smith",
    "email": "jane@example.com",
    "role": "Receptionist",
    "is_active": true
  },
  "message": "User created successfully"
}
```

---

### 3. Update User

**Endpoint**: `PATCH /users/{id}/`

**Request Body**:
```json
{
  "is_active": false
}
```

---

### 4. Change Password

**Endpoint**: `POST /users/change-password/`

**Request Body**:
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword123!",
  "confirm_password": "NewPassword123!"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

## Audit Trail Endpoints

### 1. Get Audit Logs

**Endpoint**: `GET /audit/logs/`

**Query Parameters**:
- `user`: User ID
- `table_name`: Table name
- `action`: INSERT | UPDATE | DELETE
- `date_from`, `date_to`: Date range

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "count": 500,
    "results": [
      {
        "id": 1,
        "table_name": "test_results",
        "record_id": 123,
        "action": "UPDATE",
        "user": {
          "id": 5,
          "full_name": "Tech Name"
        },
        "old_value": {"result_value": "14.2"},
        "new_value": {"result_value": "14.5"},
        "timestamp": "2024-11-25T16:05:00Z",
        "ip_address": "192.168.1.100"
      }
    ]
  }
}
```

---

## Configuration Endpoints (Admin Only)

### 1. Get System Settings

**Endpoint**: `GET /config/settings/`

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "lab_name": "ABC Medical Laboratory",
    "lab_address": "123 Main Street, Islamabad",
    "lab_phone": "+92-51-1234567",
    "lab_email": "info@abclab.com",
    "report_footer": "This is a computer-generated report",
    "currency": "PKR",
    "tax_rate": 0,
    "default_turnaround_time": 24
  }
}
```

---

### 2. Update System Settings

**Endpoint**: `PATCH /config/settings/`

**Request Body**:
```json
{
  "lab_name": "ABC Medical Laboratory",
  "lab_phone": "+92-51-7654321"
}
```

---

## Error Responses

### Validation Error (400 Bad Request)

```json
{
  "success": false,
  "data": null,
  "message": "Validation failed",
  "errors": {
    "phone": ["This field is required"],
    "email": ["Enter a valid email address"]
  }
}
```

---

### Authentication Error (401 Unauthorized)

```json
{
  "success": false,
  "message": "Authentication credentials were not provided",
  "errors": null
}
```

---

### Permission Error (403 Forbidden)

```json
{
  "success": false,
  "message": "You do not have permission to perform this action",
  "errors": null
}
```

---

### Not Found Error (404 Not Found)

```json
{
  "success": false,
  "message": "Resource not found",
  "errors": null
}
```

---

### Server Error (500 Internal Server Error)

```json
{
  "success": false,
  "message": "An unexpected error occurred",
  "errors": null
}
```

---

## Rate Limiting

- **Rate Limit**: 100 requests per minute per user
- **Response Header**: `X-RateLimit-Remaining: 95`
- **429 Response** (Too Many Requests):
```json
{
  "success": false,
  "message": "Rate limit exceeded. Please try again in 60 seconds."
}
```

---

## Pagination

All list endpoints support pagination:

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Response Structure**:
```json
{
  "count": 150,
  "next": "http://api/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Filtering & Searching

**Common Filters**:
- `search`: Full-text search
- `ordering`: Sort field (prefix with `-` for descending)
- Date filters: `created_at__gte`, `created_at__lte`

**Example**:
```
GET /orders/?search=ahmed&status=Pending&ordering=-order_date
```

---

## Versioning

API versioning is handled via URL:
- Current version: `/api/v1/`
- Future versions: `/api/v2/`

---

## WebSocket Support (Future - Phase 3)

Real-time updates for:
- Order status changes
- Critical value alerts
- Dashboard updates

**Connection**: `wss://your-domain.com/ws/`

---

## External Integration Endpoints (Placeholder - Phase 2)

### Analyzer Integration

**Endpoint**: `POST /integration/analyzer-results/`

**Request Body** (HL7 Message):
```json
{
  "message_type": "ORU^R01",
  "order_id": "ORD-2024-00123",
  "test_results": [...]
}
```

This comprehensive API design provides all necessary endpoints for the LIMS application with clear request/response structures.
