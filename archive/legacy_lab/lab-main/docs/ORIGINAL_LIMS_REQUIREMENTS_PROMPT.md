
🌟 MASTER AI DEVELOPER PROMPT – FULL SYSTEM OVERHAUL FOR LIMS (LAB APP)

A fully structured, deeply explained, step-by-step engineering blueprint for completing and refining the entire application.


---

🔰 INTRODUCTION

You are the AI software engineer responsible for completing and refining a LIMS (Lab Information Management System) located in this repository:

Repository Source:
/mnt/data/lab-main (9).zip (local path provided by user)

This system has:

A Django backend (organized by modular apps for orders, samples, results, patients, catalog, dashboard, and settings).

A React + TypeScript + Vite frontend built with pages for registration, phlebotomy, result entry, verification, publishing, catalog management, reporting, and settings.

An early-stage workflow configuration system.

A static, non-functional Lab Dashboard.

Workflow issues (orders not progressing).

Permission inconsistencies.

Missing UX components in registration and search.


Your job:
Fix, complete, unify, and elevate this entire system into a fully working production-grade LIMS.

This prompt explains exactly what to do and why.


---

🧭 GLOBAL GOALS (What must be true after your work)

By the end of all tasks:

1. The lab workflow must run end-to-end without any missing stage.


2. All users—regardless of role—must temporarily receive full access (for testing and simplicity).


3. Admin panel must become a real system for:

Workflow configuration

Permission management

Test & parameter catalog management

Price management



4. Registration must be fast and keyboard friendly.


5. Patient search must be universal, fast, and autofill registration correctly.


6. Lab Dashboard must become a real analytics-driven, elegant home screen, not a static mockup.


7. All new features must respect existing architecture:

Use existing backend apps (settings, dashboard, catalog)

Do NOT duplicate models or create parallel logic.



8. Code must be cleaned, documented, and consistent.




---

📌 SECTION 1 — TEMPORARY FULL ACCESS MODE

(Complete role permission override, with explanation)

Why?

Right now roles (reception/phlebotomist/tech/pathologist) each have access to only one part of the system.
This makes testing impossible, workflow debugging impossible, and development slow.

What to do:

Step 1

Backend has model RolePermission with Boolean fields (can_register, can_collect, etc.).

For every role, set ALL booleans to true.

Step 2

Ensure current_user_permissions API returns full-access values for all roles.

Step 3

Frontend uses:

useWorkflowSettings

settingsService.currentUserPermissions


Ensure all permission checks read from this API and allow access everywhere.

Step 4

Add comments clearly marking:

> TEMPORARY FULL PERMISSION OVERRIDE — REMOVE LATER WHEN FINE-GRAINED PERMISSIONS ARE ACTIVATED.



Outcome

Any user → full access to all screens until full development is done.


---

📌 SECTION 2 — FIX ORDER WORKFLOW BREAKAGE

(Repair entire lifecycle of order → sample → result → verification)

Current Issue

After registration → order goes to phlebotomy (OK).

After accepting sample → order never appears in result entry.

Result entry says “Create new order”, which is WRONG.


Explanation of Expected Logic

A correct LIMS workflow is:

1. Registration creates Order + TestOrders + (maybe Sample)
2. Order moves to Phlebotomy as a pending collection task.
3. Phlebotomist collects and accepts sample → Order marked READY_FOR_RESULT_ENTRY.
4. Result Entry screen should automatically show all orders in this state.
5. After results are completed → move to verification/publishing.

What to do:

Step 1 — Review backend workflow

Check: backend/orders/
backend/samples/
backend/results/

Find how status, sample_status, or workflow_step boundaries are being set.

Step 2 — Make sample acceptance trigger proper order state

When phlebotomist hits Accept Sample:

Set Sample state = COLLECTED/RECEIVED (depending on workflow)

Set Order state = READY_FOR_RESULT_ENTRY


Step 3 — Update result-entry filtering

Front-end result entry worklist must fetch orders with state:
READY_FOR_RESULT_ENTRY

Step 4 — Test flow

Simulate:

Create order

Accept sample

Go to result entry
Order MUST appear without creating a new order.



---

📌 SECTION 3 — COMPLETE ADMIN PANEL (WORKFLOW, PERMISSIONS, CATALOG)

(Turn half-built admin settings into a fully operational control center)

Repo already contains:

Backend:

backend/settings/models.py

backend/settings/views.py

backend/settings/serializers.py


Frontend:

WorkflowSettingsPage.tsx

RolePermissionsPage.tsx


You must transform these pages into a functional LAB ADMIN PANEL.


---

3.1 Workflow Configuration (Finish Existing System)

WorkflowSettings currently has fields like:

enable_sample_collection

enable_sample_receive

enable_verification


You must:

Make these toggles control:

Which screens appear (e.g., if phlebotomy disabled → skip)

How order transitions behave

Whether verification stage is required before publish



Add logic:

If sample collection is disabled:
Registration immediately creates READY_FOR_RESULT_ENTRY state.

If verification is disabled:
Publishing becomes the next stage after result entry.


---

3.2 Permission Management (UI + Backend Integration)

Finish RolePermissionsPage:

Load all RolePermission entries

Allow toggling (checkboxes)

Save updates through settingsService

Reflect permissions in frontend behavior (later)



---

3.3 Test & Parameter Catalog Management

Use backend apps:

catalog/tests

catalog/parameters

catalog/reference ranges


Build UI to manage:

List of Tests

Mapping tests → parameters

Reference ranges

Adding new parameters

Setting test prices

Deactivating tests


All of these must integrate:

Registration test search

Result entry field generation

Report structures



---

📌 SECTION 4 — REGISTRATION PAGE: FAST, KEYBOARD-OPTIMIZED UX

(High-speed registration: the heart of any LIMS)

Required UX Enhancements

✔ Tab Navigation

Every field must behave like a form:
Tab → next field, nothing weird.

✔ Test Search (Type-Ahead Search with Pagination)

When typing a test name:

Query backend with debounce

Show dropdown results

Allow arrow up/down selection

Press Enter → select test

After selection:

Add test to order list

Cursor returns to test search input automatically



This must be fast enough to handle 500+ tests.


---

📌 SECTION 5 — PATIENT SEARCH POPUP (UNIVERSAL SEARCH)

(Modern clinics require fast registration of existing patients)

Add a "Search Patient" button in the registration form.

Popup Requirements

Searchable fields:

Name

Mobile number

MR number

CNIC (if present)

Address

Any field in patient model


Features:

Arrow-key navigation

Enter to select

Auto-fill ALL fields (name, age, gender, mobile, address, MR number)

Must also link patient ID to new order request



---

📌 SECTION 6 — TESTING & CLEANUP

(Stabilize and modernize the repo)

Tasks:

1. Create/extend unit tests for:

Workflow transitions

Result entry progression

Patient search API

Test search API



2. Delete/archive dead code
(Anything leftover from initial design or unused components.)


3. Ensure compatibility:

Frontend typed interfaces

Backend serializers

Shared naming conventions





---

📌 SECTION 7 — ELITE NEW LAB HOME DASHBOARD

(Replace static mockup with real analytics + navigation)

Your current dashboard is visually okay but functionally dead.

You must BUILD a new modern dashboard:


---

7.1 Dashboard Should Show LIVE Analytics

Use backend/dashboard/views.py analytics service.

Tiles should include:

Today’s orders

Pending phlebotomy

Pending result entry

Pending verification

Pending publishing

Pending refunds

Number of tests run today


Each tile → navigates to filtered list.


---

7.2 Functional Action Tiles

Every tile must work:

New Lab Slip → registration

Due Lab Slip → pending orders

Refund Lab Slip → refund page

Modify Lab Slip → order search/edit module

Test Results Saving → result entry

Results Upload Bulk → bulk upload screen

Manage Lab Tests → catalog admin



---

7.3 Reports Section

Fully functional links:

Daily reports

Monthly summary

Department-wise performance


If backend reports don’t exist:

Create placeholders

Add minimal backend endpoints



---

7.4 Workflow Settings Tile

Add a visible tile linking to admin settings.


---

7.5 Clean Routing

Use React Router, not dummy # hyperlinks.


---

📌 SECTION 8 — CRITICAL: ALIGN WITH EXISTING ARCHITECTURE (NO DUPLICATION)

Before writing any code:

YOU MUST UNDERSTAND:

This repository already has:

A dashboard backend

A settings backend

A workflow settings page

A permissions page

A catalog backend

A partially implemented home dashboard

A complete React structure for lab modules


Your job is:

Finish the system, not rewrite it.

Explicit Instructions

Do not create new “workflow” models → use WorkflowSettings.

Do not create new “permission” logic → use RolePermission.

Do not create new dashboard endpoints → extend existing /dashboard/analytics.

Do not create separate “test catalog” logic → use catalog app.

Do not duplicate patient models or logic → use existing patients app.



---

📌 SECTION 9 — FINAL DELIVERABLES

🟢 Backend Deliverables

Fully working workflow transitions

Fully working patient search API

Fully working test search API

Extended dashboard analytics

Clean & unified RolePermission + WorkflowSettings logic

Test suite updated

Dead code removed

Proper documentation everywhere


🔵 Frontend Deliverables

New Lab Home Dashboard

Admin workflow panel

Admin permission panel

Catalog management pages

Registration UX upgrade

Patient search modal

Test selection type-ahead search

Polished routing & navigation

Error handling & loading states


🟣 Architectural Deliverables

No duplication

Centralized logic for workflow & permissions

Centralized dashboard analytics

Clear code organization



---

✔️ END OF FULL EXPANDED PROMPT
