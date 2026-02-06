# Patient Registration Number System

## Overview

The LIMS now supports a **unique permanent registration number** system for patients. Each patient receives a unique Medical Record Number (MRN) that remains constant throughout all their visits.

## Key Features

### 1. Unique Registration Numbers (MRN)
- **Format**: `PAT-YYYYMMDD-NNNN`
  - Example: `PAT-20260206-0001`
- **Auto-generated**: System automatically generates sequential MRN for each new patient
- **Permanent**: Once assigned, the MRN never changes
- **Unique**: Each patient has exactly one MRN

### 2. Multiple Patients Per Mobile Number
- **One mobile number can be associated with multiple patient records**
- Common use cases:
  - Husband and wife sharing the same mobile number
  - Family members using a single contact number
  - Parents registering children under their mobile number

### 3. Visit Tracking
- Each visit generates a new **Lab Number / Order ID**
- Format: `ORD-YYYYMMDD-NNNN`
- All visits are linked to the patient's permanent MRN
- Complete visit history accessible via patient's MRN

## User Workflow

### Registration Process

1. **Enter Mobile Number**
   - Type the patient's mobile number in the registration form
   - System automatically searches for existing patients with that number

2. **Review Existing Patients**
   - If patients exist with that mobile number, they are displayed in a dropdown
   - Each suggestion shows:
     - Patient's full name
     - **Registration Number (MRN)** - prominently displayed
     - Gender and age
     - Last visit date
     - Total number of orders

3. **Choose Action**
   - **Option A: Select Existing Patient**
     - Click on a patient from the dropdown
     - Patient details auto-fill in the form
     - Proceed to add tests for a new visit
   
   - **Option B: Create New Patient**
     - Click "➕ Create New Patient" at the bottom of the dropdown
     - OR press Tab/Escape to close the dropdown
     - Continue filling in the new patient's details
     - System will create a new patient with a new unique MRN

### Keyboard Navigation

- **Arrow Down/Up**: Navigate through patient suggestions
- **Enter**: Select highlighted patient or "Create New Patient" option
- **Tab**: Close suggestions and move to next field
- **Escape**: Close suggestions dropdown

## Database Schema

### Patient Model
```python
class Patient(models.Model):
    # Unique identifiers
    patient_id = CharField(unique=True)  # MRN (backward compatibility)
    mrn = CharField(unique=True)         # Medical Record Number
    
    # Contact (NOT unique - multiple patients can share)
    phone = CharField()  # No unique constraint
    
    # Demographics
    full_name = CharField()
    gender = CharField()
    date_of_birth = DateField()
    # ... other fields
```

### Order Model
```python
class Order(models.Model):
    order_id = CharField(unique=True)    # Lab Number/Visit ID
    patient = ForeignKey(Patient)        # Links to patient's MRN
    # ... other fields
```

## API Endpoints

### Patient Lookup by Mobile
```
GET /api/v1/patients/lookup/?mobile=03001234567

Response:
{
  "success": true,
  "data": [
    {
      "id": 123,
      "patient_id": "PAT-20260206-0001",
      "full_name": "John Doe",
      "phone": "03001234567",
      "age": 35,
      "gender": "Male",
      "last_visit": "2026-02-01T10:30:00Z",
      "total_orders": 5
    },
    {
      "id": 124,
      "patient_id": "PAT-20260206-0002",
      "full_name": "Jane Doe",
      "phone": "03001234567",
      "age": 32,
      "gender": "Female",
      "last_visit": "2026-01-15T14:20:00Z",
      "total_orders": 3
    }
  ]
}
```

## Benefits

1. **Data Integrity**
   - Each patient has a unique, permanent identifier
   - No confusion between different patients with same mobile number
   - Complete visit history maintained per patient

2. **Family-Friendly**
   - Families can share contact numbers
   - Each family member maintains separate medical records
   - Easy to register multiple family members

3. **Audit Trail**
   - Every visit tracked against permanent MRN
   - Historical data always accessible
   - Compliance with medical record-keeping standards

4. **User Experience**
   - Quick patient lookup by mobile number
   - Clear visual distinction between different patients
   - Easy to create new patient or select existing one

## Migration Notes

### Existing Data
- All existing patients already have unique `patient_id` and `mrn` fields
- No data migration required
- Phone field already supports non-unique values

### Backward Compatibility
- `patient_id` field maintained for backward compatibility
- Both `patient_id` and `mrn` contain the same value
- Existing integrations continue to work

## Testing Scenarios

### Scenario 1: New Patient Registration
1. Enter mobile number: `03001234567`
2. No existing patients found
3. Fill in patient details
4. Save → New MRN generated: `PAT-20260206-0001`

### Scenario 2: Existing Patient Visit
1. Enter mobile number: `03001234567`
2. One patient found: "John Doe - MRN: PAT-20260206-0001"
3. Select patient from dropdown
4. Patient details auto-fill
5. Add tests and create order → New Lab Number: `ORD-20260206-0001`

### Scenario 3: Multiple Patients Same Mobile
1. Enter mobile number: `03001234567`
2. Two patients found:
   - "John Doe - MRN: PAT-20260206-0001"
   - "Jane Doe - MRN: PAT-20260206-0002"
3. Select correct patient OR create new patient
4. Proceed with visit

### Scenario 4: New Family Member
1. Enter mobile number: `03001234567` (already used by John Doe)
2. Existing patient shown: "John Doe - MRN: PAT-20260206-0001"
3. Click "➕ Create New Patient"
4. Fill in new patient details (Jane Doe)
5. Save → New MRN generated: `PAT-20260206-0002`
6. Both patients now share mobile `03001234567` but have different MRNs

## Future Enhancements

1. **Patient Relationship Tracking**
   - Link family members (husband/wife, parent/child)
   - Show relationships in patient lookup

2. **Bulk Family Registration**
   - Register multiple family members in one flow
   - Automatically link relationships

3. **Mobile Number Verification**
   - SMS verification for patient identity
   - Reduce duplicate registrations

4. **Advanced Search**
   - Search by MRN, name, CNIC, etc.
   - Filter by relationship, age group, etc.
