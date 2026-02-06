# Patient Registration - Quick Reference Guide

## For Reception Staff

### When Registering a Patient

#### Step 1: Enter Mobile Number
- Type the patient's mobile number
- **Wait for suggestions to appear** (if any existing patients found)

#### Step 2: Check for Existing Patients

**If you see existing patients:**
```
┌─────────────────────────────────────────────────────┐
│ Found 2 existing patients with this number         │
├─────────────────────────────────────────────────────┤
│ ● John Doe                    MRN: PAT-20260206-0001│
│   Male • 35 years • Last visit: 01/02/2026          │
├─────────────────────────────────────────────────────┤
│ ● Jane Doe                    MRN: PAT-20260206-0002│
│   Female • 32 years • Last visit: 15/01/2026        │
├─────────────────────────────────────────────────────┤
│ ➕ Create New Patient                               │
│   Register a new patient with this mobile number    │
└─────────────────────────────────────────────────────┘
```

**Ask the patient:**
- "Is this you?" (point to the name and details)
- Check the **MRN (Registration Number)** if patient has their card
- Verify with **last visit date** if available

#### Step 3: Choose Action

**Option A: Patient Already Registered**
1. Click on the patient's name in the list
2. Details will auto-fill
3. Verify the information is correct
4. Click "Update & Proceed to Tests"
5. Add tests and create order

**Option B: New Patient (First Visit)**
1. Click "➕ Create New Patient" at the bottom
2. Fill in all patient details
3. Click "Save Patient & Proceed"
4. Add tests and create order

### Important Notes

✅ **DO:**
- Always verify patient identity before selecting
- Check the MRN if patient has their registration card
- Ask patient to confirm their details after selection
- Create a new patient if you're not 100% sure

❌ **DON'T:**
- Don't assume first patient in list is correct
- Don't select wrong patient just because mobile matches
- Don't worry about "duplicate" mobile numbers - this is normal!

### Common Scenarios

#### Scenario 1: Husband and Wife
```
Mobile: 03001234567

Existing patients:
- Ahmed Khan (MRN: PAT-20260201-0015)
- Fatima Khan (MRN: PAT-20260201-0016)

Action: Ask "Who is visiting today?" and select correct patient
```

#### Scenario 2: New Family Member
```
Mobile: 03001234567

Existing patient:
- Ahmed Khan (MRN: PAT-20260201-0015)

Patient says: "I'm his wife, first time here"

Action: Click "Create New Patient" and register Fatima Khan
        She will get new MRN: PAT-20260206-0025
```

#### Scenario 3: Return Visit
```
Mobile: 03001234567

Existing patient:
- Ahmed Khan (MRN: PAT-20260201-0015)
  Last visit: 15/01/2026

Patient says: "I was here last month"

Action: Click on Ahmed Khan, verify details, proceed to tests
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ↓ (Arrow Down) | Move down in patient list |
| ↑ (Arrow Up) | Move up in patient list |
| Enter | Select highlighted patient |
| Tab | Skip to next field (create new patient) |
| Esc | Close patient list |

### Troubleshooting

**Q: I don't see any patients but I know they visited before**
- Check if mobile number is typed correctly
- Try searching by name in the top-right search box
- Patient might have used different mobile number

**Q: Patient has two different MRNs**
- This might be a duplicate registration
- Note both MRNs and inform supervisor
- Use the most recent one for now

**Q: Can I change a patient's mobile number?**
- Yes! Select the patient, update mobile number, click "Update & Proceed"
- This won't affect their MRN or history

**Q: What if I select the wrong patient by mistake?**
- Before creating the order: Clear the form (refresh page) and start again
- After creating the order: Inform supervisor immediately

### Remember

🔑 **MRN (Medical Record Number) is permanent**
- Each patient gets ONE unique MRN
- MRN never changes
- All visits are tracked under this MRN

📱 **Mobile numbers can be shared**
- Multiple patients can have the same mobile number
- This is normal and expected
- Always verify patient identity

🎫 **Lab Number changes every visit**
- Each visit gets a new Lab Number (Order ID)
- Format: ORD-YYYYMMDD-NNNN
- This is printed on the receipt

### Need Help?

Contact IT Support or your supervisor if:
- System is not showing expected patients
- You suspect duplicate registrations
- Patient claims wrong MRN on their card
- Any technical issues with registration
