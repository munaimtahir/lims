# Voice Registration Specification

## Overview
The LIMS voice registration system allows healthcare workers to register patients and enter data using voice commands in English and Urdu. The system automatically extracts structured data from voice transcripts with confidence scoring.

## Supported Languages
- **English**: Full support for medical terminology and common phrases
- **Urdu**: Support for common registration keywords (naam, umr, mard, aurat, etc.)
- **Mixed**: System handles code-switching between English and Urdu

## Confidence Scoring System

### Confidence Levels
1. **High Confidence (≥0.9)**: Auto-accepted, no user confirmation needed
2. **Medium Confidence (0.6-0.89)**: Requires user confirmation before proceeding
3. **Low Confidence (<0.6)**: Requires manual entry, voice data used as hint

### Confidence Calculation
- Overall confidence = Average of all extracted field confidences
- Each field has its own confidence score based on:
  - Keyword match strength
  - Pattern recognition quality
  - Contextual validation

## Supported Fields

### Patient Registration
| Field | Keywords (English) | Keywords (Urdu) | Example Patterns |
|-------|-------------------|-----------------|------------------|
| Name | name, patient name | naam, مریض کا نام | "Patient name is John Doe" |
| Age | age, years old, aged | umr, عمر, سال | "age 35", "45 years old" |
| Gender | male, female, man, woman | mard, aurat, مرد, عورت | "gender male", "female patient" |
| Contact | phone, contact, number | نمبر, فون | "phone 555-1234", "contact 555-9876" |
| Tests | test, tests, investigation | ٹیسٹ | "test CBC", "CBC and glucose tests" |

## Sample Utterances

### High Confidence Examples (≥0.9)
1. **English**: "Patient name is Maria Garcia age 29 female phone 555-1111"
2. **Urdu**: "naam Muhammad Ali umr 45 mard contact 555-2222"
3. **Mixed**: "Patient name John Doe umr 35 male test CBC"

### Medium Confidence Examples (0.6-0.89)
4. **Partial Info**: "Sarah aged 28 woman phone 555-3333"
5. **Ambiguous**: "John Smith 35 years test glucose"
6. **Incomplete**: "naam Fatima Khan umr 32"

### Requires Manual Entry (<0.6)
7. **Very Ambiguous**: "Patient maybe something"
8. **Unclear**: "Um someone needs test"

## Complete Sample Phrases (10 Required)

1. ✅ "Patient name is Maria Garcia age 29 female phone 555-1111"
   - Expected: name, age, gender, contact extracted with high confidence

2. ✅ "naam Muhammad Ali umr 45 mard contact 555-2222"
   - Expected: Urdu keywords recognized, all fields extracted

3. ✅ "John Doe 35 years old male test CBC"
   - Expected: name, age, gender, test extracted

4. ✅ "Patient Sarah aged 28 woman phone 555-3333 glucose test"
   - Expected: name, age, gender, contact, test extracted

5. ✅ "naam Fatima Khan umr 32 aurat"
   - Expected: Mixed language, name, age, gender extracted

6. ✅ "Patient name David Lee age 50 male contact 555-4444 test lipid profile"
   - Expected: Complete registration with test

7. ✅ "Ahmed Hassan 40 years mard phone 555-5555"
   - Expected: Mixed language with phone

8. ✅ "Patient is Jane Smith age 38 female CBC and liver function"
   - Expected: Name, age, gender, multiple tests

9. ✅ "naam Ayesha Malik umr 25 lady contact 555-6666"
   - Expected: Urdu/English mix with contact

10. ✅ "Patient Robert Brown aged 55 man test kidney function"
    - Expected: Name, age, gender, specific test

## API Endpoints

### POST /voice/map
Map voice transcript to structured patient data.

**Request Body:**
```json
{
  "transcript": "Patient name is John Doe age 35 male",
  "user": "nurse_123",
  "action_type": "registration"
}
```

**Response:**
```json
{
  "fields": {
    "name": "John Doe",
    "age": 35,
    "gender": "Male"
  },
  "confidences": {
    "name": 0.95,
    "age": 0.95,
    "gender": 0.95
  },
  "overall_confidence": 0.95,
  "requires_confirmation": false,
  "requires_manual": false
}
```

### GET /voice/events
List recent voice events for audit trail.

**Query Parameters:**
- `limit`: Number of events to return (default: 50)

**Response:**
```json
[
  {
    "id": 1,
    "user": "nurse_123",
    "transcript": "Patient name is John Doe age 35 male",
    "mapping": {"name": "John Doe", "age": 35, "gender": "Male"},
    "confidences": {"name": 0.95, "age": 0.95, "gender": 0.95},
    "timestamp": "2025-10-23T01:00:00Z",
    "action_type": "registration"
  }
]
```

## Frontend Integration

### Web Speech API
The frontend uses the Web Speech API for voice input:
```javascript
const recognition = new webkitSpeechRecognition();
recognition.lang = 'en-US'; // or 'ur-PK' for Urdu
recognition.continuous = false;
recognition.interimResults = false;

recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;
  // Send to /voice/map endpoint
};
```

### Confidence UI Display
- **≥0.9**: Green chip with "Auto-accepted" ✓
- **0.6-0.89**: Yellow chip with "Confirm?" - Show confirmation dialog
- **<0.6**: Red chip with "Manual Entry" - Pre-fill form with extracted data

## Audit Trail
All voice interactions are logged in the `voice_events` table:
- User who performed the action
- Complete transcript
- Extracted field mapping (JSON)
- Confidence scores (JSON)
- Timestamp (UTC)
- Action type (registration, result_entry, etc.)

## Error Handling
- **No speech detected**: Prompt user to try again
- **Unclear audio**: Lower confidence score, may require confirmation
- **No fields extracted**: Return empty fields with confidence 0.0
- **Invalid field values**: Filtered out (e.g., age > 150)

## Testing
See `tests/test_voice_mapping.py` for comprehensive unit tests covering:
- Individual field extraction (name, age, gender, contact, tests)
- Complete transcript mapping
- Confidence threshold validation
- Mixed language support
- Sample phrase validation

## Future Enhancements
- Support for additional languages (Arabic, Punjabi)
- Real-time voice streaming and progressive extraction
- Custom vocabulary training for lab-specific terminology
- Voice biometrics for user authentication
- Offline voice recognition capability
