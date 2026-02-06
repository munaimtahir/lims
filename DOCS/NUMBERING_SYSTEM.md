# Locking/Guardrails for LIMS Numbering System (V2)

## Overview
This document describes the finalized, production-grade numbering system for Patient Registration and Lab Visits (Tube Labels). This system is **LOCKED** (V2) and must not be altered without a strict migration and safety review.

**Status:** LOCKED
**As of:** Feb 2026
**Concurrency:** Enforced via DB row-locking

---

## 1. Patient Registration Number (MRN)

This number uniquely identifies a patient in the system.

**Format:** `YYMM-CC-SSSS`
- **YY**: Last 2 digits of the year (e.g., `26` for 2026).
- **MM**: 2-digit month (01–12).
- **CC**: 2-digit Collection Center Code (00 = Head Office).
- **SSSS**: 4-digit monthly serial number (0001–9999).

**Reset Rule:**
- Serial `SSSS` resets to `0001` at the start of every month **per center**.
- Uniqueness scope: `(Year, Month, Center)`.

**Example:**
- `2602-00-0001`: First patient in Feb 2026 at Center 00.
- `2602-00-0002`: Second patient...

---

## 2. Lab Number (Tube Label)

This number identifies a "Visit" or "Order" purely for lab workflow purposes. It is short enough to write on tubes manually if needed.

**Format:** `MDD-XXX`
- **M**: Month Letter (A=Jan, B=Feb, ..., L=Dec).
- **DD**: 2-digit Day of Month (01–31).
- **XXX**: Daily serial number (001–999).

**Reset Rule:**
- Serial `XXX` resets to `001` every day **per center**.
- Uniqueness enforcement: `(Center, Lab Date, Daily Serial)`.
- Note: The label `MDD-XXX` itself is NOT unique across years or centers physically (unless stickers include center/year), but logically in the system, it is unique per day/center.

**Month Codes:**
| Month | Code | Month | Code |
|-------|------|-------|------|
| Jan   | A    | Jul   | G    |
| Feb   | B    | Aug   | H    |
| Mar   | C    | Sep   | I    |
| Apr   | D    | Oct   | J    |
| May   | E    | Nov   | K    |
| Jun   | F    | Dec   | L    |

**Example:**
- `B07-001`: Feb 7th, 1st patient of the day.

---

## 3. Concurrency & Safety

To prevent duplicate numbers during high-volume registration:
1.  **Atomic Counters:** We do not use `MAX(id) + 1`. We use dedicated counter tables (`RegistrationCounter`, `LabDailyCounter`).
2.  **Row-Level Locking:** All increments use `SELECT ... FOR UPDATE` (database locking) to serialize access to the counter row for a specific scope (Month/Center or Day/Center).
3.  **Uniqueness Constraints:** Database constraints prevent duplicates even if locking fails (which it shouldn't).

## 4. Center Codes
- **00**: Head Office (Default)
- **01-99**: Franchise / Specific Collection Centers.

## 5. Changes
- **No Deletion:** numbers are permanent once generated.
- **No Edits:** UI prevents editing these numbers.
