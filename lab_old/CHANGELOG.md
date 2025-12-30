# Changelog

All notable changes to the Al-Shifa Laboratory Information Management System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Sample Rejection Feature
- Added ability to reject samples with documented reasons
- New `POST /api/samples/{id}/reject/` endpoint
- Requires rejection reason input via modal dialog
- Rejected samples display with red badge in UI
- Only lab staff (Technologist, Pathologist, Admin) can reject samples
- Can only reject samples in PENDING, COLLECTED, or RECEIVED status
- Rejected samples are excluded from downstream processing

#### Order Cancellation Feature
- Added ability to cancel orders before sample collection
- New `POST /api/orders/{id}/cancel/` endpoint
- Only Admin and Reception roles can cancel orders
- Cancel button appears in Order Detail page for NEW orders
- Confirmation dialog prevents accidental cancellations
- Cannot cancel orders after samples have been collected
- Cancellation updates order and all related items to CANCELLED status
- Database migration: Added CANCELLED status to Order and OrderItem models

#### Order Test Editing Feature
- Added ability to edit tests in orders before samples/results exist
- New `PATCH /api/orders/{id}/edit-tests/` endpoint
- Request body: `{tests_to_add?: number[], tests_to_remove?: number[]}`
- Only Admin and Reception roles can edit tests
- "Edit Tests" button in Order Detail page with modal interface
- Modal shows current tests with remove checkboxes
- Modal shows available tests with add checkboxes
- Summary preview of changes before saving
- Cannot edit after samples or results created
- Cannot edit cancelled orders
- Cannot remove all tests without adding new ones
- 10 comprehensive backend tests added
- 100% test coverage for new functionality

#### Mobile Navigation
- Responsive hamburger menu for screens < 768px (tablet/mobile)
- Auto-closes menu on route change for better UX
- Auto-closes menu when ESC key is pressed
- Maintains role-based navigation filtering
- Smooth transitions and proper ARIA labels for accessibility

#### Responsive Layout Improvements
- All forms and tables optimized for 768px tablet screens
- Implemented Tailwind responsive utilities throughout UI
- Tab navigation scrollable on mobile devices
- Buttons stack vertically on mobile for better touch interaction
- Headers and action buttons use flex-col on mobile, flex-row on desktop
- No horizontal scrolling (except intentional table overflow)
- Responsive font sizes and padding adjustments

#### Result Workflow UX Enhancements
- Added role indicator showing user's workflow responsibility
  - "Result Entry" for Technologists
  - "Verification & Publishing" for Pathologists
- Enhanced status badges with next-action indicators:
  - "→ Action: Enter Result" for DRAFT status
  - "→ Action: Verify" for ENTERED status
  - "→ Action: Publish" for VERIFIED status
  - "✓ Complete" for PUBLISHED status
- Role-specific informational messages:
  - Pathologists see waiting message when result is in DRAFT
  - Technologists see confirmation when result is ENTERED
- Role-based UI filtering:
  - Technologists only see result entry fields
  - Pathologists only see verification/publish actions
- Toast notifications for all status changes

### Changed
- Updated API documentation with new endpoints and permissions
- Improved mobile menu user experience with better state management
- Enhanced result entry workflow with clearer visual indicators

### Fixed
- Resolved merge conflicts with main branch
- Fixed mobile menu state variable naming inconsistency
- Fixed test mocking issues in reports.test.ts
- Improved test coverage to 99.02% (exceeds 99% requirement)

### Technical
- Added database migration for CANCELLED order status
- Integrated Toast component for better notification UX
- Added comprehensive test coverage (140 backend tests, 98 frontend tests)
- All GitHub Actions workflows passing
- No security vulnerabilities detected

## [1.0.0] - 2025-01-XX - Initial Release

### Features
- Patient registration and management
- Test catalog management
- Order creation and tracking
- Sample collection workflow
- Result entry and verification
- PDF report generation with signatures
- Role-based access control (RBAC)
- User management and authentication
