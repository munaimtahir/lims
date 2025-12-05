# Data Model

## Core Entities

### User
- `id` (PK)
- `username` (unique)
- `email`
- `password` (hashed)
- `role` (ADMIN, RECEPTION, PHLEBOTOMY, TECHNOLOGIST, PATHOLOGIST)
- `phone`
- `first_name`, `last_name`
- `is_active`, `is_staff`, `is_superuser`
- `date_joined`, `last_login`

### Patient
- `id` (PK)
- `mrn` (unique, auto-generated: PAT-YYYYMMDD-NNNN)
- `full_name`
- `father_name`
- `dob` (Date of Birth)
- `sex` (M/F/O)
- `phone` (validated Pakistani format)
- `cnic` (unique, format: #####-#######-#)
- `address`
- `created_at`, `updated_at`

**Indexes:** mrn, cnic, phone

### TestCatalog
- `id` (PK)
- `code` (unique)
- `name`
- `description`
- `category` (Hematology, Biochemistry, etc.)
- `sample_type`
- `price` (decimal)
- `turnaround_time_hours`
- `is_active`
- `created_at`, `updated_at`

**Indexes:** code, category

### Order
- `id` (PK)
- `order_no` (unique, auto-generated: ORD-YYYYMMDD-NNNN)
- `patient_id` (FK to Patient)
- `priority` (ROUTINE, URGENT, STAT)
- `status` (NEW, COLLECTED, IN_PROCESS, VERIFIED, PUBLISHED)
- `notes`
- `created_at`, `updated_at`

**Indexes:** order_no, patient, status

### OrderItem
- `id` (PK)
- `order_id` (FK to Order)
- `test_id` (FK to TestCatalog)
- `status` (NEW, COLLECTED, IN_PROCESS, VERIFIED, PUBLISHED)
- `created_at`, `updated_at`

**Relationship:** One Order has many OrderItems

### Sample
- `id` (PK)
- `order_item_id` (FK to OrderItem)
- `sample_type`
- `barcode` (unique, auto-generated: SAM-YYYYMMDD-NNNN)
- `collected_at`, `collected_by_id` (FK to User)
- `received_at`, `received_by_id` (FK to User)
- `status` (PENDING, COLLECTED, RECEIVED, REJECTED)
- `rejection_reason`
- `notes`
- `created_at`, `updated_at`

**Indexes:** barcode, status

### Result
- `id` (PK)
- `order_item_id` (FK to OrderItem)
- `value`
- `unit`
- `reference_range`
- `flags` (H=High, L=Low, N=Normal)
- `status` (DRAFT, ENTERED, VERIFIED, PUBLISHED)
- `entered_by_id` (FK to User), `entered_at`
- `verified_by_id` (FK to User), `verified_at`
- `published_at`
- `notes`
- `created_at`, `updated_at`

**Indexes:** status

### Report
- `id` (PK)
- `order_id` (FK to Order, one-to-one)
- `pdf_file` (FileField)
- `generated_at`
- `generated_by_id` (FK to User)

## Relationships

```
User (1) ─────< (many) Patient [created by]
Patient (1) ───< (many) Order
Order (1) ─────< (many) OrderItem
OrderItem (1) ─< (1) Sample
OrderItem (1) ─< (many) Result
Order (1) ─────< (1) Report

TestCatalog (1) < (many) OrderItem

User (1) ───< (many) Sample [collected_by, received_by]
User (1) ───< (many) Result [entered_by, verified_by]
User (1) ───< (many) Report [generated_by]
```

## State Machines

### Order Status Flow
NEW → COLLECTED → IN_PROCESS → VERIFIED → PUBLISHED

### Sample Status Flow
PENDING → COLLECTED → RECEIVED
                   ↘ REJECTED

### Result Status Flow
DRAFT → ENTERED → VERIFIED → PUBLISHED

**Enforcement:** State transitions are validated and require appropriate user roles.

## Validation Rules

### Patient
- CNIC: Must match format `^\d{5}-\d{7}-\d$`
- Phone: Must match `^(\+92|0)?3\d{9}$`
- DOB: Cannot be in future

### Sample
- Barcode: Auto-generated, unique per day
- Collection: Only PHLEBOTOMY or ADMIN
- Receiving: Only TECHNOLOGIST, PATHOLOGIST, or ADMIN

### Result
- Entry: Only TECHNOLOGIST or ADMIN
- Verification: Only PATHOLOGIST or ADMIN (requires ENTERED status)
- Publishing: Only PATHOLOGIST or ADMIN (requires VERIFIED status)

### Report
- Generation: Only PATHOLOGIST or ADMIN
- Requirement: All OrderItem results must be PUBLISHED

