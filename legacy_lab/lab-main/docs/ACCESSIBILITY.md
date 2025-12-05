# Accessibility (a11y) Guidelines

## Overview

The Al-Shifa LIMS follows WCAG 2.1 Level AA standards to ensure accessibility for all users.

## Implemented Features

### Keyboard Navigation
- **Modal Dialogs**: All modals can be closed with ESC key
- **Mobile Menu**: Hamburger menu closes with ESC key
- **Form Navigation**: Tab order follows logical flow
- **Focus Management**: Focus trapped within modals when open

### ARIA Labels
- **Buttons**: All action buttons have descriptive aria-labels
  - "Toggle menu" for hamburger button
  - "Toggle mobile menu" with aria-expanded state
  - "Enter result", "Verify result", "Publish result" for action buttons
- **Status Indicators**: Status badges include semantic meaning
- **Navigation**: Role-based navigation with proper ARIA roles

### Visual Indicators
- **Focus States**: Clear focus indicators on all interactive elements
- **Color Contrast**: All text meets WCAG AA contrast ratios
  - Red badges for rejected samples (high contrast)
  - Blue for informational messages
  - Green for success states
- **Status Communication**: Not relying solely on color
  - Text labels accompany all status indicators
  - Icons supplement color coding

### Responsive Design
- **Touch Targets**: Minimum 44x44px on mobile (iOS HIG standard)
- **Spacing**: Adequate spacing between interactive elements
- **Font Sizes**: Responsive text sizing (text-2xl sm:text-3xl)
- **Viewport**: Works well at all viewport sizes from 320px up

### Forms
- **Labels**: All form fields have associated labels
- **Required Fields**: Marked with asterisk (*) and aria-required
- **Error Messages**: Associated with fields via aria-describedby
- **Validation**: Client-side validation with clear error messages

## Components with Accessibility Features

### Sample Rejection Modal
```tsx
- Modal title properly labeled
- Textarea has associated label "Rejection Reason *"
- Required field validation
- ESC key closes modal
- Focus returns to trigger button on close
```

### Order Cancellation Dialog
```tsx
- Confirmation dialog with clear messaging
- Cancel/Confirm buttons with distinct styling
- ESC key support
- Prevents accidental actions
```

### Mobile Navigation
```tsx
- Hamburger button: aria-label="Toggle mobile menu"
- Expanded state: aria-expanded={isMobileMenuOpen}
- Menu auto-closes on route change
- ESC key closes menu
- Focus management on open/close
```

### Result Entry Forms
```tsx
- Clear role indicators
- Action prompts for next steps
- Status badges with text labels
- Role-based filtering reduces cognitive load
```

## Testing Checklist

### Manual Testing
- [ ] Tab through all interactive elements
- [ ] Test ESC key on all modals
- [ ] Verify focus visible on all elements
- [ ] Test with keyboard only (no mouse)
- [ ] Verify all images have alt text

### Screen Reader Testing
- [ ] Test with NVDA (Windows)
- [ ] Test with JAWS (Windows)
- [ ] Test with VoiceOver (macOS/iOS)
- [ ] Verify all announcements are meaningful
- [ ] Check form validation announcements

### Automated Testing
- [ ] Run axe DevTools in browser
- [ ] Check with Lighthouse accessibility audit
- [ ] Validate HTML structure
- [ ] Test color contrast ratios

## Known Issues and Future Improvements

### Current Limitations
- E2E accessibility tests not yet implemented (Playwright can add these)
- Screen reader testing not automated

### Planned Improvements
- Add comprehensive Playwright accessibility tests
- Implement live regions for dynamic content updates
- Add skip navigation links
- Enhanced keyboard shortcuts for power users

## Resources
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Resources](https://webaim.org/resources/)
