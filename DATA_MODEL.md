# Laboratory Information Management System
## Data Model & Database Design

This document outlines the database structure for the LIMS, including all tables, columns, relationships, and initial data seeding plan based on LOINC (Logical Observation Identifiers Names and Codes) standards.

---

## Core Database Tables

### 1. Patients

Stores patient demographic information.

**Table Name:** `patients`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique patient identifier |
| patient_id | String(20) | UNIQUE, NOT NULL | Display ID (e.g., P-2024-00001) |
| first_name | String(100) | NOT NULL | Patient's first name |
| last_name | String(100) | NOT NULL | Patient's last name |
| date_of_birth | Date | NOT NULL | Date of birth |
| age | Integer | Calculated | Age in years |
| gender | String(10) | NOT NULL | Male/Female/Other |
| phone | String(20) | NOT NULL | Contact number |
| email | String(100) | NULLABLE | Email address |
| national_id | String(50) | NULLABLE | ID/Passport number |
| address | Text | NULLABLE | Complete address |
| created_at | DateTime | NOT NULL | Registration timestamp |
| updated_at | DateTime | NOT NULL | Last update timestamp |

**Indexes:** patient_id, phone, national_id

---

### 2. Test Categories

Groups tests into logical categories.

**Table Name:** `test_categories`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| name | String(100) | UNIQUE, NOT NULL | Category name |
| description | Text | NULLABLE | Category description |
| display_order | Integer | DEFAULT 0 | Sort order for display |

**Example Categories:**
- Hematology
- Clinical Chemistry
- Immunology
- Microbiology
- Hormone Tests
- Tumor Markers

---

### 3. Test Panels

Groups of tests commonly ordered together.

**Table Name:** `test_panels`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| panel_code | String(20) | UNIQUE, NOT NULL | Panel code (e.g., CBC, LFT) |
| panel_name | String(200) | NOT NULL | Panel display name |
| category_id | Integer | FOREIGN KEY | Links to test_categories |
| price | Decimal(10,2) | NOT NULL | Panel price |
| sample_type | String(50) | NOT NULL | Required sample type |
| turnaround_time | Integer | NOT NULL | Expected TAT in hours |
| is_active | Boolean | DEFAULT TRUE | Active status |

**Relationship:** Many-to-One with `test_categories`

---

### 4. Tests

Individual laboratory tests.

**Table Name:** `tests`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| test_code | String(20) | UNIQUE, NOT NULL | Test code |
| test_name | String(200) | NOT NULL | Test display name |
| loinc_code | String(20) | NULLABLE | LOINC code for standardization |
| category_id | Integer | FOREIGN KEY | Links to test_categories |
| price | Decimal(10,2) | NOT NULL | Test price |
| sample_type | String(50) | NOT NULL | Blood/Urine/Stool/etc. |
| sample_volume | String(20) | NULLABLE | Required volume |
| turnaround_time | Integer | NOT NULL | Expected TAT in hours |
| is_active | Boolean | DEFAULT TRUE | Active status |
| method | String(100) | NULLABLE | Testing methodology |

**Relationship:** Many-to-One with `test_categories`

---

### 5. Test Parameters

Individual measurable components within tests.

**Table Name:** `test_parameters`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| test_id | Integer | FOREIGN KEY | Links to tests |
| parameter_name | String(200) | NOT NULL | Parameter name |
| loinc_code | String(20) | NULLABLE | LOINC code |
| unit | String(20) | NOT NULL | SI unit (mg/dL, mmol/L, etc.) |
| reference_min_male | Decimal(10,3) | NULLABLE | Male lower limit |
| reference_max_male | Decimal(10,3) | NULLABLE | Male upper limit |
| reference_min_female | Decimal(10,3) | NULLABLE | Female lower limit |
| reference_max_female | Decimal(10,3) | NULLABLE | Female upper limit |
| critical_low | Decimal(10,3) | NULLABLE | Critical low value |
| critical_high | Decimal(10,3) | NULLABLE | Critical high value |
| decimal_places | Integer | DEFAULT 2 | Decimal precision |
| display_order | Integer | DEFAULT 0 | Display sequence |

**Relationship:** Many-to-One with `tests`

---

### 6. Panel Test Mapping

Links tests to panels.

**Table Name:** `panel_test_mapping`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| panel_id | Integer | FOREIGN KEY | Links to test_panels |
| test_id | Integer | FOREIGN KEY | Links to tests |

**Relationship:** Many-to-Many bridge between `test_panels` and `tests`

---

### 7. Orders

Patient test orders.

**Table Name:** `orders`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| order_id | String(30) | UNIQUE, NOT NULL | Display order ID |
| patient_id | Integer | FOREIGN KEY | Links to patients |
| order_date | DateTime | NOT NULL | Order creation time |
| referring_doctor | String(200) | NULLABLE | Doctor name |
| priority | String(20) | DEFAULT 'Routine' | Routine/Urgent/STAT |
| special_instructions | Text | NULLABLE | Additional notes |
| total_amount | Decimal(10,2) | NOT NULL | Total charges |
| discount_amount | Decimal(10,2) | DEFAULT 0 | Discount applied |
| final_amount | Decimal(10,2) | NOT NULL | Payable amount |
| status | String(50) | NOT NULL | Order status |
| created_by | Integer | FOREIGN KEY | User who created |
| created_at | DateTime | NOT NULL | Creation timestamp |

**Status Values:** Pending, Sample Collected, In Progress, Results Entered, Verified, Completed, Cancelled

**Relationship:** Many-to-One with `patients`

---

### 8. Order Items

Individual tests/panels in an order.

**Table Name:** `order_items`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| order_id | Integer | FOREIGN KEY | Links to orders |
| item_type | String(20) | NOT NULL | Test/Panel |
| test_id | Integer | FOREIGN KEY NULLABLE | Links to tests |
| panel_id | Integer | FOREIGN KEY NULLABLE | Links to test_panels |
| item_name | String(200) | NOT NULL | Item name (denormalized) |
| price | Decimal(10,2) | NOT NULL | Item price |
| status | String(50) | NOT NULL | Item status |

**Relationship:** Many-to-One with `orders`

---

### 9. Sample Collection

Tracks sample collection events.

**Table Name:** `sample_collections`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| order_id | Integer | FOREIGN KEY | Links to orders |
| sample_type | String(50) | NOT NULL | Blood/Urine/etc. |
| collection_date | DateTime | NOT NULL | Collection timestamp |
| collected_by | Integer | FOREIGN KEY | User who collected |
| barcode | String(50) | NULLABLE | Sample barcode |
| notes | Text | NULLABLE | Collection notes |

**Relationship:** Many-to-One with `orders`

---

### 10. Test Results

Stores laboratory test results.

**Table Name:** `test_results`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| order_id | Integer | FOREIGN KEY | Links to orders |
| test_id | Integer | FOREIGN KEY | Links to tests |
| parameter_id | Integer | FOREIGN KEY | Links to test_parameters |
| result_value | String(100) | NOT NULL | Result value |
| unit | String(20) | NOT NULL | Unit of measurement |
| reference_range | String(50) | NULLABLE | Applied reference range |
| flag | String(20) | NULLABLE | Normal/High/Low/Critical |
| entered_by | Integer | FOREIGN KEY | Technician who entered |
| entered_at | DateTime | NOT NULL | Entry timestamp |
| verified_by | Integer | FOREIGN KEY NULLABLE | Pathologist who verified |
| verified_at | DateTime | NULLABLE | Verification timestamp |
| comments | Text | NULLABLE | Technical comments |

**Relationship:** Many-to-One with `orders`, `tests`, `test_parameters`

---

### 11. Payments

Tracks patient payments.

**Table Name:** `payments`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| order_id | Integer | FOREIGN KEY | Links to orders |
| receipt_number | String(30) | UNIQUE, NOT NULL | Receipt number |
| payment_date | DateTime | NOT NULL | Payment timestamp |
| amount_paid | Decimal(10,2) | NOT NULL | Amount received |
| payment_method | String(50) | NOT NULL | Cash/Card/Transfer/etc. |
| received_by | Integer | FOREIGN KEY | User who received |
| notes | Text | NULLABLE | Payment notes |

**Relationship:** Many-to-One with `orders`

---

### 12. Reports

Generated PDF reports.

**Table Name:** `reports`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| order_id | Integer | FOREIGN KEY | Links to orders |
| report_number | String(30) | UNIQUE, NOT NULL | Report number |
| generated_at | DateTime | NOT NULL | Generation timestamp |
| generated_by | Integer | FOREIGN KEY | User who generated |
| file_path | String(500) | NOT NULL | PDF file location |
| delivered_at | DateTime | NULLABLE | Delivery timestamp |
| delivered_to | String(200) | NULLABLE | Recipient name |

**Relationship:** Many-to-One with `orders`

---

### 13. Users

System users (staff).

**Table Name:** `users`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| username | String(50) | UNIQUE, NOT NULL | Login username |
| password_hash | String(255) | NOT NULL | Hashed password |
| full_name | String(200) | NOT NULL | Full name |
| email | String(100) | UNIQUE, NOT NULL | Email address |
| role | String(50) | NOT NULL | User role |
| is_active | Boolean | DEFAULT TRUE | Active status |
| created_at | DateTime | NOT NULL | Creation timestamp |
| last_login | DateTime | NULLABLE | Last login time |

**Roles:** Admin, Receptionist, Cashier, Phlebotomist, Technician, Pathologist, Manager

---

## Entity Relationship Diagram

```
Patients (1) ──────── (M) Orders (1) ──────── (M) Order_Items
                           │                         │
                           │                         ├── (M) Tests
                           │                         └── (M) Test_Panels
                           │
                           ├── (M) Sample_Collections
                           ├── (M) Test_Results ──── (M) Test_Parameters
                           ├── (M) Payments
                           └── (1) Reports

Tests (M) ──────── (1) Test_Categories
      │
      └── (M) Test_Parameters

Test_Panels (M) ──────── (1) Test_Categories
            │
            └── (M) Panel_Test_Mapping (M) ──── Tests

Users ──── Creates/Verifies ──── Multiple Tables
```

---

## LOINC-Based Test Catalog for Data Seeding

### Hematology Tests

#### Complete Blood Count (CBC Panel)

**Panel Code:** CBC  
**LOINC Panel Code:** 58410-2  
**Sample Type:** EDTA Blood (3-5 mL)  
**Price:** 800 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference | Critical Low | Critical High |
|-----------|-----------|------|----------------|------------------|--------------|---------------|
| Hemoglobin | 718-7 | g/dL | 13.5 - 17.5 | 12.0 - 15.5 | <7.0 | >20.0 |
| RBC Count | 789-8 | ×10⁶/μL | 4.5 - 5.5 | 4.0 - 5.0 | <2.5 | >6.5 |
| WBC Count | 6690-2 | ×10³/μL | 4.0 - 11.0 | 4.0 - 11.0 | <2.0 | >30.0 |
| Platelet Count | 777-3 | ×10³/μL | 150 - 400 | 150 - 400 | <50 | >1000 |
| Hematocrit | 4544-3 | % | 40 - 52 | 36 - 46 | <20 | >60 |
| MCV | 787-2 | fL | 80 - 100 | 80 - 100 | - | - |
| MCH | 785-6 | pg | 27 - 32 | 27 - 32 | - | - |
| MCHC | 786-4 | g/dL | 32 - 36 | 32 - 36 | - | - |
| RDW | 788-0 | % | 11.5 - 14.5 | 11.5 - 14.5 | - | - |
| Neutrophils | 770-8 | % | 40 - 75 | 40 - 75 | - | - |
| Lymphocytes | 736-9 | % | 20 - 45 | 20 - 45 | - | - |
| Monocytes | 5905-5 | % | 2 - 10 | 2 - 10 | - | - |
| Eosinophils | 713-8 | % | 1 - 6 | 1 - 6 | - | - |
| Basophils | 706-2 | % | 0 - 2 | 0 - 2 | - | - |

---

#### Erythrocyte Sedimentation Rate (ESR)

**Test Code:** ESR  
**LOINC Code:** 4537-7  
**Sample Type:** EDTA Blood (2 mL)  
**Price:** 300 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference |
|-----------|-----------|------|----------------|------------------|
| ESR | 4537-7 | mm/hr | 0 - 15 | 0 - 20 |

---

### Clinical Chemistry Tests

#### Liver Function Test (LFT Panel)

**Panel Code:** LFT  
**LOINC Panel Code:** 24325-3  
**Sample Type:** Serum (3 mL)  
**Price:** 1200 PKR

| Parameter | LOINC Code | Unit | Reference Range | Critical Low | Critical High |
|-----------|-----------|------|-----------------|--------------|---------------|
| Total Bilirubin | 1975-2 | mg/dL | 0.3 - 1.2 | - | >12.0 |
| Direct Bilirubin | 1968-7 | mg/dL | 0.0 - 0.3 | - | - |
| Indirect Bilirubin | - | mg/dL | 0.1 - 1.0 | - | - |
| ALT (SGPT) | 1742-6 | U/L | 7 - 56 | - | >1000 |
| AST (SGOT) | 1920-8 | U/L | 10 - 40 | - | >1000 |
| ALP | 6768-6 | U/L | 44 - 147 | - | - |
| Total Protein | 2885-2 | g/dL | 6.0 - 8.3 | - | - |
| Albumin | 1751-7 | g/dL | 3.5 - 5.5 | - | - |
| Globulin | - | g/dL | 2.0 - 3.5 | - | - |
| A/G Ratio | - | ratio | 1.0 - 2.5 | - | - |

---

#### Kidney Function Test (KFT/RFT Panel)

**Panel Code:** RFT  
**LOINC Panel Code:** 24362-6  
**Sample Type:** Serum (3 mL)  
**Price:** 1000 PKR

| Parameter | LOINC Code | Unit | Reference Range | Critical Low | Critical High |
|-----------|-----------|------|-----------------|--------------|---------------|
| Blood Urea | 3094-0 | mg/dL | 15 - 45 | - | >100 |
| Creatinine | 2160-0 | mg/dL | 0.7 - 1.3 | - | >5.0 |
| Uric Acid | 3084-1 | mg/dL | 3.5 - 7.2 (M), 2.6 - 6.0 (F) | - | - |
| Sodium | 2951-2 | mmol/L | 136 - 145 | <120 | >160 |
| Potassium | 2823-3 | mmol/L | 3.5 - 5.1 | <2.5 | >6.5 |
| Chloride | 2075-0 | mmol/L | 98 - 107 | - | - |

---

#### Lipid Profile

**Panel Code:** LIPID  
**LOINC Panel Code:** 57698-3  
**Sample Type:** Serum (2 mL) - Fasting  
**Price:** 1500 PKR

| Parameter | LOINC Code | Unit | Desirable | Borderline | High Risk |
|-----------|-----------|------|-----------|------------|-----------|
| Total Cholesterol | 2093-3 | mg/dL | <200 | 200-239 | ≥240 |
| Triglycerides | 2571-8 | mg/dL | <150 | 150-199 | ≥200 |
| HDL Cholesterol | 2085-9 | mg/dL | >40 (M), >50 (F) | - | - |
| LDL Cholesterol | 2089-1 | mg/dL | <100 | 100-159 | ≥160 |
| VLDL Cholesterol | 13457-7 | mg/dL | <30 | - | - |
| Cholesterol/HDL Ratio | 9830-1 | ratio | <5.0 | - | - |

---

#### Blood Glucose Tests

**Test Code:** FBS  
**LOINC Code:** 1558-6  
**Sample Type:** Plasma (Fluoride) - Fasting  
**Price:** 250 PKR

| Parameter | LOINC Code | Unit | Normal | Prediabetes | Diabetes |
|-----------|-----------|------|--------|-------------|----------|
| Fasting Blood Sugar | 1558-6 | mg/dL | 70 - 100 | 100 - 125 | ≥126 |

**Test Code:** RBS  
**LOINC Code:** 2345-7  
**Price:** 200 PKR

| Parameter | LOINC Code | Unit | Reference | Critical Low | Critical High |
|-----------|-----------|------|-----------|--------------|---------------|
| Random Blood Sugar | 2345-7 | mg/dL | 70 - 140 | <40 | >400 |

**Test Code:** HBA1C  
**LOINC Code:** 4548-4  
**Sample Type:** EDTA Blood  
**Price:** 1800 PKR

| Parameter | LOINC Code | Unit | Normal | Prediabetes | Diabetes |
|-----------|-----------|------|--------|-------------|----------|
| HbA1c | 4548-4 | % | <5.7 | 5.7 - 6.4 | ≥6.5 |

---

### Thyroid Function Tests

#### Thyroid Profile

**Panel Code:** TFT  
**Sample Type:** Serum (2 mL)  
**Price:** 2500 PKR

| Parameter | LOINC Code | Unit | Reference Range | Critical Low | Critical High |
|-----------|-----------|------|-----------------|--------------|---------------|
| TSH | 3016-3 | μIU/mL | 0.4 - 4.0 | <0.1 | >10.0 |
| Free T3 | 3026-2 | pg/mL | 2.3 - 4.2 | - | - |
| Free T4 | 3024-7 | ng/dL | 0.8 - 1.8 | - | - |

---

### Immunology/Serology Tests

#### Hepatitis Screening

**Test Code:** HBsAg  
**LOINC Code:** 5196-1  
**Sample Type:** Serum  
**Price:** 600 PKR

| Parameter | LOINC Code | Unit | Result Type |
|-----------|-----------|------|-------------|
| HBsAg | 5196-1 | - | Positive/Negative |

**Test Code:** Anti-HCV  
**LOINC Code:** 16128-1  
**Price:** 800 PKR

| Parameter | LOINC Code | Unit | Result Type |
|-----------|-----------|------|-------------|
| Anti-HCV | 16128-1 | - | Positive/Negative |

---

### Urine Tests

#### Complete Urine Examination

**Test Code:** URINE-RE  
**Sample Type:** Random Urine (30 mL)  
**Price:** 400 PKR

**Physical Examination:**
- Color
- Appearance
- Specific Gravity (1.005 - 1.030)
- pH (5.0 - 8.0)

**Chemical Examination:**
- Protein (Negative)
- Glucose (Negative)
- Ketones (Negative)
- Blood (Negative)
- Bilirubin (Negative)
- Urobilinogen (Normal)
- Nitrite (Negative)
- Leukocyte Esterase (Negative)

**Microscopic Examination:**
- RBCs (0-3 /HPF)
- WBCs (0-5 /HPF)
- Epithelial Cells (Few)
- Casts (Absent)
- Crystals (Occasional)
- Bacteria (Absent)

---

## Data Seeding Plan

### Phase 1: Master Data

1. **Test Categories** (6 categories)
   - Hematology
   - Clinical Chemistry
   - Immunology/Serology
   - Microbiology
   - Urinalysis
   - Hormone Tests

2. **Tests** (15-20 individual tests)
   - Seed all tests listed above
   - Include LOINC codes where available
   - Set appropriate prices and sample types

3. **Test Parameters** (100+ parameters)
   - Seed all parameters for each test
   - Include reference ranges by gender
   - Set critical values
   - Assign SI units

4. **Test Panels** (5-8 panels)
   - CBC, LFT, RFT, Lipid Profile, TFT
   - Create panel-test mappings

### Phase 2: System Data

5. **Users** (5-10 sample users)
   - Admin user
   - Reception staff (2)
   - Lab technician (2)
   - Pathologist (1)
   - Manager (1)

### Phase 3: Sample Data (Optional for Testing)

6. **Sample Patients** (10-20)
   - Diverse demographics
   - Different age groups and genders

7. **Sample Orders** (5-10)
   - Various test combinations
   - Different statuses for testing workflows

---

## Database Indexes Strategy

**Primary Indexes:**
- All primary keys (auto-indexed)
- Foreign keys for join performance

**Additional Indexes:**
- `patients.patient_id` (unique search)
- `patients.phone` (search by phone)
- `orders.order_id` (unique search)
- `orders.order_date` (date range queries)
- `orders.status` (status filtering)
- `test_results.order_id` (result lookups)
- `payments.receipt_number` (receipt search)

---

## Data Validation Rules

1. **Patient Age Calculation:**
   - Auto-calculate from date_of_birth
   - Update dynamically on query

2. **Order Amount Calculation:**
   - Sum of all order items
   - Subtract discount
   - Prevent negative amounts

3. **Result Flagging:**
   - Auto-flag based on reference ranges
   - Consider gender-specific ranges
   - Mark critical values

4. **Sample Type Validation:**
   - Ensure sample type matches test requirements
   - Alert for incompatible samples

5. **Status Transitions:**
   - Enforce valid status progression
   - Prevent backward transitions (except cancellation)

---

## Audit Trail Requirements

Track the following for compliance:

- All result entries and modifications
- Result verifications
- Report generations
- Payment transactions
- Order cancellations
- Sample rejections
- User logins and critical actions

**Audit Table Structure:**

| Column | Description |
|--------|-------------|
| audit_id | Unique identifier |
| table_name | Affected table |
| record_id | Affected record |
| action | INSERT/UPDATE/DELETE |
| old_value | Previous data (JSON) |
| new_value | New data (JSON) |
| user_id | User who made change |
| timestamp | When change occurred |
| ip_address | User's IP address |

---

## Notes on International Standards

1. **LOINC Integration:**
   - LOINC codes provided for standardization
   - Enables data exchange with other systems
   - Supports clinical decision support

2. **SI Units:**
   - All measurements use SI units (International System of Units)
   - Common conversions provided where applicable

3. **Reference Ranges:**
   - Based on international guidelines
   - Age and gender-specific where appropriate
   - Laboratory should validate for local population

4. **Critical Values:**
   - Based on common critical value policies
   - Should be customized per facility protocol
   - Require immediate notification

