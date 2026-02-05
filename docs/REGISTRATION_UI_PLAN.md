# Registration & Order UI Overhaul Plan

This document tracks the progress of the major UI updates requested for the Registration and Test Ordering workflows.

## 1. Registration Page Overhaul
**Goal:** Make patient registration comprehensive yet efficient, with smart age/date syncing.

- [x] **Comprehensive Patient Fields**
  - Added `Father/Husband Name`, `CNIC/National ID`, `Email`, `Address`.
  - Ensured only `Mobile`, `Full Name`, and `Gender` are mandatory.
- [x] **Age & DOB Sync**
  - Implemented bi-directional synchronization between `Date of Birth` and `Age (Years/Months/Days)`.
  - Changing one updates the other automatically.
- [x] **Layout Improvements**
  - Moved to a clean grid layout.
  - Added "Global Patient Search" in the header for quick lookup.

## 2. Test Ordering Redesign
**Goal:** Replace the legacy test list with a modern, search-driven experience.

- [x] **Search-First Interface**
  - Removed static list.
  - Added a large, focused search bar (`Command+K` style feel).
  - Implemented `Arrow Key` navigation and `Enter` to select tests.
- [x] **Shopping Cart Experience**
  - Selected tests appear in a clear "Added Tests" table with prices.
  - Easy removal of tests.
  - Total calculation updates instantly.

## 3. Payment & Billing Logic
**Goal:** Simplify payment entry and ensure accuracy.

- [x] **Dynamic Calculations**
  - Real-time updates for `Total`, `Discount`, `Net Payable`, `Paid`, and `Due`.
  - Supports both **Percentage** and **Fixed Amount** discounts.
- [x] **Smart Defaults**
  - `Paid Amount` auto-fills to match `Net Payable` (for full payment workflows) but remains fully editable.
  - `Due Amount` is automatically calculated based on the entered `Paid Amount`.

## 4. Receipt & Completion
**Goal:** Provide immediate feedback and print options.

- [x] **Completion Workflow**
  - "Create Order" saves data and immediately triggers a success state.
- [x] **Receipt Modal**
  - Displays the generated **Lab Number / Order ID**.
  - Provides a prominent **Print Receipt** button used to open the print view.
  - Backed by a beautiful modal overlay (Glassmorphism).

## 5. Printing
**Goal:** Professional receipt printing with dual A4 support.

- [x] **Print Receipt Page** (`/print/receipt/:id`)
  - [x] **A4 Dual Mode**: Prints two copies (Patient/Office) on one A4 sheet with a cut line, roughly 48% height each.
  - [x] **Thermal Mode**: Supports 80mm width printing.
  - [x] **Data Integration**: Fetches full patient and order details along with lab settings (Layout, Logo) dynamically.
  - [x] **Financials**: Clearly lists Total, Discount, Net, Paid, and Due balance.

## 6. Verification & Next Steps
- [x] **Backend Compatibility Check**
- [ ] **User Verification**
  - Run the application (`npm run dev`) and test the flow end-to-end.
