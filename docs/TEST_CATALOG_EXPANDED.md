# LIMS Comprehensive Test Catalog
## Category B Laboratory - Complete Test List with LOINC Codes

This document provides the complete expanded test catalog for a Category B laboratory covering all routine and special departments.

---

## Table of Contents

1. [Routine Hematology](#routine-hematology)
2. [Routine Biochemistry](#routine-biochemistry)
3. [Special Biochemistry](#special-biochemistry)
4. [Routine Microbiology](#routine-microbiology)
5. [Immunology & Serology](#immunology--serology)
6. [Hormone Analysis](#hormone-analysis)  
7. [Coagulation Studies](#coagulation-studies)
8. [Urinalysis & Body Fluids](#urinalysis--body-fluids)

---

## 1. Routine Hematology

### 1.1 Complete Blood Count (CBC) - Already Documented
See DATA_MODEL.md for full details.

### 1.2 Erythrocyte Sedimentation Rate (ESR) - Already Documented
See DATA_MODEL.md for full details.

### 1.3 Peripheral Blood Film (PBF)

**Test Code:** PBF  
**Sample Type:** EDTA Blood  
**Price:** 500 PKR  
**TAT:** 4 hours

**Parameters:**
- RBC Morphology (Descriptive)
- WBC Morphology (Descriptive)
- Platelet Morphology (Descriptive)
- Parasite Screening (Negative)
- Abnormal Cells (None)

### 1.4 Reticulocyte Count

**Test Code:** RETIC  
**LOINC Code:** 4679-7  
**Sample Type:** EDTA Blood  
**Price:** 600 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Reticulocyte Count | 4679-7 | % | 0.5 - 2.5 |
| Absolute Reticulocyte | 40665-2 | ×10⁹/L | 25 - 100 |

### 1.5 Blood Group & Rh

**Test Code:** BG-RH  
**LOINC Code:** 882-1, 10331-7  
**Sample Type:** EDTA Blood  
**Price:** 400 PKR

**Parameters:**
- ABO Group (A/B/AB/O)
- Rh Factor (Positive/Negative)

### 1.6 Complete Coagulation Profile

See Section 7 for coagulation tests.

---

## 2. Routine Biochemistry

### 2.1 Liver Function Tests (LFT) - Already Documented
See DATA_MODEL.md

### 2.2 Kidney Function Tests (RFT/KFT) - Already Documented
See DATA_MODEL.md

### 2.3 Lipid Profile - Already Documented
See DATA_MODEL.md

### 2.4 Blood Glucose Tests - Already Documented
See DATA_MODEL.md

### 2.5 Serum Calcium

**Test Code:** Ca  
**LOINC Code:** 17861-6  
**Sample Type:** Serum  
**Price:** 400 PKR

| Parameter | LOINC Code | Unit | Reference Range | Critical Low | Critical High |
|-----------|-----------|------|-----------------|--------------|---------------|
| Calcium | 17861-6 | mg/dL | 8.5 - 10.5 | <7.0 | >13.0 |

### 2.6 Serum Phosphorus

**Test Code:** PHOS  
**LOINC Code:** 2777-1  
**Sample Type:** Serum  
**Price:** 400 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Phosphorus | 2777-1 | mg/dL | 2.5 - 4.5 |

### 2.7 Serum Magnesium

**Test Code:** Mg  
**LOINC Code:** 19123-9  
**Sample Type:** Serum  
**Price:** 500 PKR

| Parameter | LOINC Code | Unit | Reference Range | Critical Low |
|-----------|-----------|------|-----------------|--------------|
| Magnesium | 19123-9 | mg/dL | 1.7 - 2.4 | <1.2 |

### 2.8 Serum Iron Studies Panel

**Panel Code:** IRON  
**Sample Type:** Serum (Fasting)  
**Price:** 1800 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference |
|-----------|-----------|------|----------------|------------------|
| Serum Iron | 2498-4 | μg/dL | 65 - 175 | 50 - 170 |
| TIBC | 2500-7 | μg/dL | 250 - 450 | 250 - 450 |
| Transferrin Saturation | 2502-3 | % | 20 - 50 | 15 - 50 |
| Ferritin | 2518-9 | ng/mL | 30 - 400 | 15 - 150 |

### 2.9 Serum Lactate Dehydrogenase (LDH)

**Test Code:** LDH  
**LOINC Code:** 2532-0  
**Sample Type:** Serum  
**Price:** 600 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| LDH | 2532-0 | U/L | 140 - 280 |

### 2.10 Serum Creatine Kinase (CK)

**Test Code:** CK  
**LOINC Code:** 2157-6  
**Sample Type:** Serum  
**Price:** 700 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference |
|-----------|-----------|------|----------------|------------------|
| Total CK | 2157-6 | U/L | 38 - 174 | 26 - 140 |

### 2.11 CK-MB

**Test Code:** CKMB  
**LOINC Code:** 13969-1  
**Sample Type:** Serum  
**Price:** 900 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| CK-MB | 13969-1 | ng/mL | <5.0 |

### 2.12 Serum Amylase

**Test Code:** AMY  
**LOINC Code:** 1798-8  
**Sample Type:** Serum  
**Price:** 600 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Amylase | 1798-8 | U/L | 28 - 100 |

### 2.13 Serum Lipase

**Test Code:** LIPA  
**LOINC Code:** 3040-3  
**Sample Type:** Serum  
**Price:** 700 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Lipase | 3040-3 | U/L | 13 - 60 |

---

## 3. Special Biochemistry

### 3.1 Glycated Hemoglobin (HbA1c) - Already Documented
See DATA_MODEL.md

### 3.2 Serum Vitamin B12

**Test Code:** VIT-B12  
**LOINC Code:** 2132-9  
**Sample Type:** Serum  
**Price:** 1500 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Vitamin B12 | 2132-9 | pg/mL | 200 - 900 |

### 3.3 Serum Folate

**Test Code:** FOLATE  
**LOINC Code:** 2284-8  
**Sample Type:** Serum  
**Price:** 1500 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Folate | 2284-8 | ng/mL | 3.0 - 17.0 |

### 3.4 Serum Vitamin D (25-OH)

**Test Code:** VIT-D  
**LOINC Code:** 1989-3  
**Sample Type:** Serum  
**Price:** 2500 PKR

| Parameter | LOINC Code | Unit | Deficient | Insufficient | Sufficient |
|-----------|-----------|------|-----------|--------------|------------|
| Vitamin D | 1989-3 | ng/mL | <20 | 20-30 | 30-100 |

### 3.5 Troponin I (High Sensitivity)

**Test Code:** TROP-I  
**LOINC Code:** 10839-9  
**Sample Type:** Serum  
**Price:** 2000 PKR

| Parameter | LOINC Code | Unit | Normal | Abnormal |
|-----------|-----------|------|--------|----------|
| Troponin I | 10839-9 | ng/mL | <0.04 | ≥0.04 |

### 3.6 C-Reactive Protein (CRP)

**Test Code:** CRP  
**LOINC Code:** 1988-5  
**Sample Type:** Serum  
**Price:** 800 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| CRP | 1988-5 | mg/L | <6.0 |

### 3.7 High-Sensitivity CRP (hs-CRP)

**Test Code:** HS-CRP  
**LOINC Code:** 30522-7  
**Sample Type:** Serum  
**Price:** 1200 PKR

| Parameter | LOINC Code | Unit | Low Risk | Moderate Risk | High Risk |
|-----------|-----------|------|----------|---------------|-----------|
| hs-CRP | 30522-7 | mg/L | <1.0 | 1.0-3.0 | >3.0 |

### 3.8 Serum Copper

**Test Code:** Cu  
**LOINC Code:** 5631-7  
**Sample Type:** Serum  
**Price:** 1800 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Copper | 5631-7 | μg/dL | 70 - 140 |

### 3.9 Serum Zinc

**Test Code:** Zn  
**LOINC Code:** 5671-3  
**Sample Type:** Serum  
**Price:** 1800 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Zinc | 5671-3 | μg/dL | 70 - 120 |

### 3.10 Homocysteine

**Test Code:** HCYST  
**LOINC Code:** 13965-9  
**Sample Type:** Plasma (EDTA)  
**Price:** 2500 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Homocysteine | 13965-9 | μmol/L | 5 - 15 |

### 3.11 Procalcitonin (PCT)

**Test Code:** PCT  
**LOINC Code:** 33959-8  
**Sample Type:** Serum  
**Price:** 3000 PKR

| Parameter | LOINC Code | Unit | Normal | Bacterial Infection |
|-----------|-----------|------|--------|-------------------|
| Procalcitonin | 33959-8 | ng/mL | <0.05 | >0.5 |

### 3.12 Microalbumin (Urine)

**Test Code:** M-ALB  
**LOINC Code:** 14957-5  
**Sample Type:** Random Urine  
**Price:** 1000 PKR

| Parameter | LOINC Code | Unit | Normal | Microalbuminuria |
|-----------|-----------|------|--------|-----------------|
| Microalbumin | 14957-5 | mg/L | <30 | 30-300 |

### 3.13 Serum Protein Electrophoresis

**Test Code:** SPE  
**Sample Type:** Serum  
**Price:** 2500 PKR

**Parameters:**
- Total Protein (g/dL): 6.0-8.3
- Albumin (%): 55-65
- Alpha-1 Globulin (%): 1-3
- Alpha-2 Globulin (%): 6-10
- Beta Globulin (%): 8-14
- Gamma Globulin (%): 12-20

### 3.14 Arterial Blood Gas (ABG)

**Test Code:** ABG  
**Sample Type:** Arterial Blood  
**Price:** 1500 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| pH | 2744-1 | - | 7.35 - 7.45 |
| pCO2 | 2019-8 | mmHg | 35 - 45 |
| pO2 | 2703-7 | mmHg | 80 - 100 |
| HCO3 | 1960-4 | mmol/L | 22 - 28 |
| Base Excess | 1925-7 | mmol/L | -2 to +2 |
| O2 Saturation | 2708-6 | % | 95 - 100 |

---

## 4. Routine Microbiology

### 4.1 Urine Culture & Sensitivity

**Test Code:** U-CS  
**Sample Type:** Midstream Urine  
**Price:** 1200 PKR  
**TAT:** 48-72 hours

**Parameters:**
- Organism Identification (Descriptive)
- Colony Count (CFU/mL)
- Antibiotic Sensitivity (Sensitive/Resistant)

### 4.2 Blood Culture & Sensitivity

**Test Code:** B-CS  
**Sample Type:** Blood (Aerobic & Anaerobic bottles)  
**Price:** 1800 PKR  
**TAT:** 5-7 days

**Parameters:**
- Organism Identification (Descriptive)
- Antibiotic Sensitivity (Sensitive/Resistant)

### 4.3 Stool Culture & Sensitivity

**Test Code:** ST-CS  
**Sample Type:** Fresh Stool  
**Price:** 1500 PKR  
**TAT:** 48-72 hours

**Parameters:**
- Organism Identification (Descriptive)
- Antibiotic Sensitivity (Sensitive/Resistant)

### 4.4 Throat Swab Culture

**Test Code:** THR-CS  
**Sample Type:** Throat Swab  
**Price:** 1000 PKR  
**TAT:** 48 hours

### 4.5 Sputum Culture & Sensitivity

**Test Code:** SPU-CS  
**Sample Type:** Sputum  
**Price:** 1500 PKR  
**TAT:** 48-72 hours

### 4.6 Wound Swab Culture & Sensitivity

**Test Code:** WND-CS  
**Sample Type:** Wound Swab  
**Price:** 1200 PKR  
**TAT:** 48 hours

### 4.7 Sputum AFB (TB Smear)

**Test Code:** AFB  
**Sample Type:** Sputum (3 samples)  
**Price:** 500 PKR  
**TAT:** 24 hours

**Parameter:**
- AFB Result (Negative / Positive with grading)

### 4.8 Gram Stain

**Test Code:** GRAM  
**Sample Type:** Various  
**Price:** 400 PKR  
**TAT:** 2 hours

**Parameter:**
- Gram Stain Result (Descriptive)

### 4.9 Stool for Ova & Parasites

**Test Code:** STOOL-OP  
**Sample Type:** Fresh Stool  
**Price:** 500 PKR

**Parameters:**
- Ova (Present/Absent)
- Parasites (Present/Absent - type if present)
- Cysts (Present/Absent)

### 4.10 Fungal Culture

**Test Code:** FUNG-CS  
**Sample Type:** Various  
**Price:** 1500 PKR  
**TAT:** 7-14 days

---

## 5. Immunology & Serology

### 5.1 HBsAg - Already Documented
See DATA_MODEL.md

### 5.2 Anti-HCV - Already Documented
See DATA_MODEL.md

### 5.3 Complete Hepatitis Panel

**Panel Code:** HEP-PANEL  
**Sample Type:** Serum  
**Price:** 3500 PKR

| Test | LOINC Code | Result Type |
|------|-----------|-------------|
| HBsAg | 5196-1 | Positive/Negative |
| Anti-HBs | 5193-8 | Positive/Negative |
| Anti-HBc Total | 16933-4 | Positive/Negative |
| Anti-HBc IgM | 31204-1 | Positive/Negative |
| HBeAg | 5191-2 | Positive/Negative |
| Anti-HBe | 5189-6 | Positive/Negative |
| Anti-HCV | 16128-1 | Positive/Negative |
| Anti-HAV IgM | 22314-9 | Positive/Negative |

### 5.4 HIV Screening (Anti-HIV)

**Test Code:** HIV  
**LOINC Code:** 7917-8  
**Sample Type:** Serum  
**Price:** 1200 PKR

| Parameter | LOINC Code | Result Type |
|-----------|-----------|-------------|
| HIV 1 & 2 | 7917-8 | Reactive/Non-Reactive |

### 5.5 VDRL (Syphilis Screening)

**Test Code:** VDRL  
**LOINC Code:** 5292-8  
**Sample Type:** Serum  
**Price:** 500 PKR

| Parameter | LOINC Code | Result Type |
|-----------|-----------|-------------|
| VDRL | 5292-8 | Reactive/Non-Reactive |

### 5.6 Widal Test (Typhoid)

**Test Code:** WIDAL  
**Sample Type:** Serum  
**Price:** 600 PKR

**Parameters:**
- S. Typhi O (Titer)
- S. Typhi H (Titer)
- S. Paratyphi AH (Titer)
- S. Paratyphi BH (Titer)

### 5.7 Dengue NS1 Antigen

**Test Code:** DENG-NS1  
**LOINC Code:** 54086-7  
**Sample Type:** Serum  
**Price:** 1500 PKR

| Parameter | LOINC Code | Result Type |
|-----------|-----------|-------------|
| Dengue NS1 | 54086-7 | Positive/Negative |

### 5.8 Dengue IgM/IgG

**Test Code:** DENG-AB  
**Sample Type:** Serum  
**Price:** 1500 PKR

| Parameter | LOINC Code | Result Type |
|-----------|-----------|-------------|
| Dengue IgM | 6385-5 | Positive/Negative |
| Dengue IgG | 6384-8 | Positive/Negative |

### 5.9 Malaria Parasite (ICT)

**Test Code:** MP-ICT  
**Sample Type:** Blood  
**Price:** 800 PKR

**Parameters:**
- Pf (P. falciparum): Positive/Negative
- Pv (P. vivax): Positive/Negative

### 5.10 Helicobacter Pylori IgG

**Test Code:** H-PYLORI  
**LOINC Code:** 13282-9  
**Sample Type:** Serum  
**Price:** 1500 PKR

| Parameter | LOINC Code | Result Type |
|-----------|-----------|-------------|
| H. Pylori IgG | 13282-9 | Positive/Negative |

### 5.11 Rheumatoid Factor (RF)

**Test Code:** RF  
**LOINC Code:** 11572-5  
**Sample Type:** Serum  
**Price:** 800 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| RF | 11572-5 | IU/mL | <20 |

### 5.12 Antistreptolysin O (ASO)

**Test Code:** ASO  
**LOINC Code:** 5370-2  
**Sample Type:** Serum  
**Price:** 800 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| ASO Titer | 5370-2 | IU/mL | <200 |

### 5.13 Anti-Nuclear Antibody (ANA)

**Test Code:** ANA  
**LOINC Code:** 5048-4  
**Sample Type:** Serum  
**Price:** 2000 PKR

| Parameter | LOINC Code | Result Type |
|-----------|-----------|-------------|
| ANA | 5048-4 | Positive/Negative + Pattern |

---

## 6. Hormone Analysis

### 6.1 Thyroid Function Tests - Already Documented
See DATA_MODEL.md (TSH, Free T3, Free T4)

### 6.2 Complete Thyroid Panel

**Panel Code:** THYROID-FULL  
**Sample Type:** Serum  
**Price:** 4000 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| TSH | 3016-3 | μIU/mL | 0.4 - 4.0 |
| Free T3 | 3026-2 | pg/mL | 2.3 - 4.2 |
| Free T4 | 3024-7 | ng/dL | 0.8 - 1.8 |
| Total T3 | 3053-6 | ng/dL | 80 - 200 |
| Total T4 | 3051-0 | μg/dL | 4.5 - 12.0 |
| Anti-TPO | 8099-6 | IU/mL | <35 |
| Anti-Thyroglobulin | 8098-8 | IU/mL | <40 |

### 6.3 Parathyroid Hormone (PTH)

**Test Code:** PTH  
**LOINC Code:** 2731-8  
**Sample Type:** Serum  
**Price:** 2500 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| PTH | 2731-8 | pg/mL | 15 - 65 |

### 6.4 Serum Cortisol

**Test Code:** CORTISOL  
**LOINC Code:** 2143-6  
**Sample Type:** Serum  
**Price:** 1500 PKR

| Parameter | LOINC Code | Unit | AM (8am) | PM (4pm) |
|-----------|-----------|------|----------|----------|
| Cortisol | 2143-6 | μg/dL | 5-25 | 3-12 |

### 6.5 Testosterone (Total)

**Test Code:** TESTO-T  
**LOINC Code:** 2986-8  
**Sample Type:** Serum  
**Price:** 1800 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference |
|-----------|-----------|------|----------------|------------------|
| Total Testosterone | 2986-8 | ng/dL | 300-1000 | 15-70 |

### 6.6 Free Testosterone

**Test Code:** TESTO-F  
**LOINC Code:** 2990-0  
**Sample Type:** Serum  
**Price:** 2500 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference |
|-----------|-----------|------|----------------|------------------|
| Free Testosterone | 2990-0 | pg/mL | 50-200 | 1.0-8.5 |

### 6.7 Prolactin

**Test Code:** PRL  
**LOINC Code:** 2842-3  
**Sample Type:** Serum  
**Price:** 1500 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference |
|-----------|-----------|------|----------------|------------------|
| Prolactin | 2842-3 | ng/mL | 2-18 | 2-29 |

### 6.8 Luteinizing Hormone (LH)

**Test Code:** LH  
**LOINC Code:** 10501-5  
**Sample Type:** Serum  
**Price:** 1500 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference |
|-----------|-----------|------|----------------|------------------|
| LH | 10501-5 | mIU/mL | 1.5-9.3 | Varies by cycle |

### 6.9 Follicle Stimulating Hormone (FSH)

**Test Code:** FSH  
**LOINC Code:** 15067-2  
**Sample Type:** Serum  
**Price:** 1500 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference |
|-----------|-----------|------|----------------|------------------|
| FSH | 15067-2 | mIU/mL | 1.4-18.1 | Varies by cycle |

### 6.10 Estradiol (E2)

**Test Code:** E2  
**LOINC Code:** 2243-4  
**Sample Type:** Serum  
**Price:** 1800 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference |
|-----------|-----------|------|----------------|------------------|
| Estradiol | 2243-4 | pg/mL | 10-40 | Varies by cycle |

### 6.11 Progesterone

**Test Code:** PROG  
**LOINC Code:** 2839-9  
**Sample Type:** Serum  
**Price:** 1500 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Progesterone | 2839-9 | ng/mL | Varies by cycle/phase |

### 6.12 Beta-HCG (Pregnancy Test - Quantitative)

**Test Code:** B-HCG  
**LOINC Code:** 2119-6  
**Sample Type:** Serum  
**Price:** 1000 PKR

| Parameter | LOINC Code | Unit | Non-Pregnant | Pregnant |
|-----------|-----------|------|--------------|----------|
| Beta-HCG | 2119-6 | mIU/mL | <5 | >25 |

### 6.13 Growth Hormone (GH)

**Test Code:** GH  
**LOINC Code:** 2963-7  
**Sample Type:** Serum  
**Price:** 2000 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| GH | 2963-7 | ng/mL | <10 |

### 6.14 Insulin (Fasting)

**Test Code:** INSULIN  
**LOINC Code:** 2333-3  
**Sample Type:** Serum (Fasting)  
**Price:** 1500 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Insulin | 2333-3 | μIU/mL | 2-25 |

### 6.15 DHEA-S

**Test Code:** DHEA-S  
**LOINC Code:** 2193-1  
**Sample Type:** Serum  
**Price:** 2000 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference |
|-----------|-----------|------|----------------|------------------|
| DHEA-S | 2193-1 | μg/dL | 80-560 | 35-430 |

---

## 7. Coagulation Studies

### 7.1 Prothrombin Time (PT)

**Test Code:** PT  
**LOINC Code:** 5902-2  
**Sample Type:** Citrated Plasma  
**Price:** 600 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| PT | 5902-2 | seconds | 11-13 |
| PT INR | 6301-6 | ratio | 0.8-1.2 |

### 7.2 Activated Partial Thromboplastin Time (APTT)

**Test Code:** APTT  
**LOINC Code:** 3173-2  
**Sample Type:** Citrated Plasma  
**Price:** 600 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| APTT | 3173-2 | seconds | 25-35 |

### 7.3 D-Dimer

**Test Code:** D-DIMER  
**LOINC Code:** 48065-7  
**Sample Type:** Citrated Plasma  
**Price:** 1500 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| D-Dimer | 48065-7 | ng/mL FEU | <500 |

### 7.4 Fibrinogen

**Test Code:** FIBR  
**LOINC Code:** 3255-7  
**Sample Type:** Citrated Plasma  
**Price:** 1200 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Fibrinogen | 3255-7 | mg/dL | 200-400 |

### 7.5 Bleeding Time

**Test Code:** BT  
**Sample Type:** Capillary Blood  
**Price:** 300 PKR

| Parameter | Unit | Reference Range |
|-----------|------|-----------------|
| Bleeding Time | minutes | 2-7 |

### 7.6 Clotting Time

**Test Code:** CT  
**Sample Type:** Venous Blood  
**Price:** 300 PKR

| Parameter | Unit | Reference Range |
|-----------|------|-----------------|
| Clotting Time | minutes | 5-10 |

---

## 8. Urinalysis & Body Fluids

### 8.1 Complete Urine Examination - Already Documented
See DATA_MODEL.md

### 8.2 24-Hour Urine Protein

**Test Code:** 24H-PROT  
**LOINC Code:** 2889-4  
**Sample Type:** 24-hour Urine Collection  
**Price:** 800 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| 24h Urine Protein | 2889-4 | mg/24h | <150 |

### 8.3 24-Hour Urine Creatinine

**Test Code:** 24H-CREAT  
**LOINC Code:** 2162-6  
**Sample Type:** 24-hour Urine Collection  
**Price:** 600 PKR

| Parameter | LOINC Code | Unit | Male Reference | Female Reference |
|-----------|-----------|------|----------------|------------------|
| 24h Urine Creatinine | 2162-6 | mg/24h | 800-2000 | 600-1800 |

### 8.4 Urine Calcium

**Test Code:** U-CA  
**LOINC Code:** 14443-6  
**Sample Type:** Random Urine  
**Price:** 600 PKR

| Parameter | LOINC Code | Unit | Reference Range |
|-----------|-----------|------|-----------------|
| Urine Calcium | 14443-6 | mg/dL | Varies |

### 8.5 Cerebrospinal Fluid (CSF) Analysis

**Test Code:** CSF  
**Sample Type:** CSF  
**Price:** 1500 PKR

**Parameters:**
- Appearance (Clear/Turbid/Bloody)
- Color (Colorless/Xanthochromic)
- Cell Count (cells/μL)
- Protein (mg/dL): 15-45
- Glucose (mg/dL): 40-70
- Chloride (mmol/L): 118-132

### 8.6 Pleural Fluid Analysis

**Test Code:** PLE-FLUID  
**Sample Type:** Pleural Fluid  
**Price:** 1500 PKR

**Parameters:**
- Appearance
- Cell Count
- Protein
- LDH
- Glucose

### 8.7 Ascitic Fluid Analysis

**Test Code:** ASC-FLUID  
**Sample Type:** Ascitic Fluid  
**Price:** 1500 PKR

**Parameters:**
- Appearance
- Cell Count
- Protein
- Albumin
- SAAG Gradient

### 8.8 Semen Analysis

**Test Code:** SEMEN  
**Sample Type:** Semen  
**Price:** 1200 PKR

**Parameters:**
- Volume (mL): 1.5-5.0
- pH: 7.2-8.0
- Sperm Count (million/mL): >15
- Motility (%): >40
- Morphology (% normal): >4
- Liquefaction Time (min): <60

---

## Summary Statistics

### Test Count by Department

| Department | Number of Tests/Panels | Est. Annual Revenue (PKR) |
|------------|----------------------|-------------------------|
| Routine Hematology | 6 | High volume |
| Routine Biochemistry | 13 | Very High volume |
| Special Biochemistry | 14 | High value |
| Routine Microbiology | 10 | Medium volume |
| Immunology & Serology | 13 | High volume |
| Hormone Analysis | 15 | High value |
| Coagulation Studies | 6 | Medium volume |
| Urinalysis & Body Fluids | 8 | High volume |
| **TOTAL** | **85+ Tests** | **Category B Comprehensive** |

### Price Range Summary

- **Basic Tests (PKR 200-500)**: 15 tests
- **Standard Tests (PKR 600-1000)**: 25 tests
- **Advanced Tests (PKR 1200-1800)**: 30 tests
- **Specialty Tests (PKR 2000-3000)**: 15 tests
- **Panels (PKR 800-4000)**: 10 panels

### Sample Type Distribution

- Serum: 60%
- Whole Blood (EDTA): 15%
- Plasma: 5%
- Urine: 10%
- Culture Specimens: 5%
- Body Fluids: 5%

---

## Data Seeding Priority

### Phase 1 (MVP Seeding - Week 2)
1. All Routine Hematology tests (6)
2. All Routine Biochemistry tests (13)
3. Top 5 Immunology tests (HBsAg, HCV, HIV, VDRL, Dengue)
4. Basic Thyroid tests (TSH, T3, T4)
5. Basic Microbiology (Urine C/S, Blood C/S)

**Total MVP Tests: ~30 tests**

### Phase 2 (Extended Seeding - Week 9)
1. All Special Biochemistry tests (14)
2. All Hormone Analysis tests (15)
3. All Coagulation Studies (6)
4. Remaining Immunology tests (8)
5. Remaining Microbiology tests (8)

**Total Phase 2 Addition: ~50 tests**

### Phase 3 (Complete Catalog - Week 14)
1. All Body Fluid Analysis tests (8)
2. Specialized panels
3. Custom test additions

**Grand Total: 85+ tests covering complete Category B laboratory**

---

## Notes

1. **LOINC Codes**: Provided where available for international standardization
2. **Prices**: Placeholder estimates in PKR, adjustable via admin panel
3. **Reference Ranges**: Based on international guidelines, should be validated for local population
4. **TAT**: Turnaround times are estimates and may vary
5. **Units**: All units are SI units unless otherwise specified
6. **Critical Values**: Defined for life-threatening results requiring immediate action

This comprehensive catalog enables the LIMS to function as a complete Category B laboratory management system.
