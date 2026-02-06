# Receipt Print System Documentation

## Overview
The LIMS receipt printing system supports two formats:
1. **Thermal Receipt** (80mm roll, default 2 copies)
2. **A4 Receipt** (210mm × 297mm, dual copy on one page)

## Supported Paper Sizes

### Thermal Printer
- **Default Width**: 80mm
- **Height**: Auto-expanding (continuous roll)
- **Recommended For**: POS thermal printers (most common)
- **Note**: 58mm printers may require manual browser scaling

### A4 Printer
- **Size**: 210mm × 297mm (standard A4)
- **Layout**: Two receipts per page (Patient Copy + Lab/Office Copy)
- **Margins**: Controlled by CSS (10mm internal padding)

## Browser Print Settings

### Required Settings (Chrome/Edge)
1. **Scale**: 100% (Do NOT use "Fit to page")
2. **Margins**: None
3. **Background graphics**: Enabled (for borders and lines)
4. **Headers and footers**: Disabled (optional but recommended)

### Step-by-Step Print Setup
1. Click the "🖨 Print Receipt" button
2. In the print dialog:
   - Set "Destination" to your printer
   - Set "Pages" to "All"
   - Set "Layout" to "Portrait"
   - Click "More settings"
   - Set "Scale" to "100"
   - Set "Margins" to "None"
   - Enable "Background graphics"
3. Click "Print"

## Features

### Layout Optimizations
- **Text Wrapping**: Long patient names, consultant names, and addresses wrap gracefully
- **No Clipping**: All content fits within paper bounds
- **Deterministic Sizing**: Fixed widths prevent layout surprises
- **Professional Typography**: Clean, readable fonts with proper hierarchy

### Thermal Receipt Features
- **Multi-Copy Support**: Print 1-10 copies in a single print job
- **Cut Lines**: Dashed separator lines with "✂ CUT HERE" markers between copies
- **Compact Layout**: Single-column design optimized for narrow width
- **Essential Fields Only**: Code column hidden to save space

### A4 Receipt Features
- **Dual Copy**: Patient copy and Lab/Office copy on one page
- **Two-Column Header**: Efficient use of space for patient information
- **Full Details**: Includes all fields including test codes
- **Professional Appearance**: Suitable for formal documentation

## Component Structure

### Files
- `PrintReceiptPage.tsx` - Main React component
- `PrintReceiptPage.module.css` - Print-optimized styles
- `printPreferences.ts` - User preference persistence

### Key Components
```
PrintReceiptPage
├── Controls (screen only)
│   ├── Format selector (A4 / Thermal)
│   ├── Copies input (thermal only)
│   └── Print button
└── Print Area
    ├── A4Container (for A4 format)
    │   ├── A4Top (Patient Copy)
    │   ├── Separator (cut line)
    │   └── A4Bottom (Lab/Office Copy)
    └── ThermalContainer (for thermal format)
        └── ThermalCopy × N (based on copies setting)
```

## CSS Architecture

### Print Media Queries
```css
@page {
    size: 80mm auto;  /* Default for thermal */
    margin: 0;
}

@media print {
    /* Print-specific styles */
    body { background: white; }
    .noDisplayPrint { display: none; }
}
```

### Text Overflow Handling
All text fields use:
```css
word-break: break-word;
overflow-wrap: anywhere;
white-space: normal;
```

### Fixed Column Widths
- Price column: 20mm (thermal and A4)
- Code column: 25mm (A4 only)
- Financial grid: 60mm (A4), 100% (thermal)

## User Preferences

### Persistence
User preferences are saved to `localStorage`:
- Last selected format (A4 or Thermal)
- Number of thermal copies (default: 2)

### Keys
- `lims:receipt:format` - "A4" or "Thermal"
- `lims:receipt:thermalCopies` - Number (1-10)

## Testing & Verification

### Test Data Requirements
Test with:
1. **Long patient name** (e.g., "Muhammad Abdullah Al-Rahman Khan")
2. **Long consultant name** (e.g., "Dr. Professor Muhammad Shahid Ahmed")
3. **Multiple test items** (5+ tests)
4. **Long test names** (e.g., "Complete Blood Count with Differential and Platelet Count")
5. **Maximum discount** (to test financial section)

### Manual Verification Checklist
- [ ] All text is visible (no clipping)
- [ ] Long names wrap properly
- [ ] Financial totals align correctly
- [ ] Cut lines are visible
- [ ] Logo/header image displays correctly
- [ ] Footer information is readable
- [ ] Multiple copies print correctly (thermal)
- [ ] Page breaks work correctly (A4)

### Browser Testing
Tested and verified in:
- ✅ Chrome/Chromium (recommended)
- ⚠️ Firefox (may require manual margin adjustment)
- ⚠️ Safari (may require manual margin adjustment)
- ⚠️ Edge (should work like Chrome)

## Troubleshooting

### Issue: Content is clipped/cut off
**Solution**: Ensure browser scale is set to 100%, not "Fit to page"

### Issue: Thermal receipt is too wide
**Solution**: Your printer may be 58mm. Try:
1. Set browser scale to 72% (58/80 = 0.725)
2. Or modify CSS: change `80mm` to `58mm` in `.thermalContainer`

### Issue: Blank page or missing content
**Solution**: Enable "Background graphics" in print settings

### Issue: Headers/footers appear on print
**Solution**: Disable browser headers/footers in print settings

### Issue: Multiple copies not working
**Solution**: Ensure you're using the thermal format and the copies input is set correctly

### Issue: A4 receipts on separate pages
**Solution**: This is expected behavior for some browsers. Each receipt copy may print on a separate page.

## Customization

### Changing Thermal Width (80mm → 58mm)
Edit `PrintReceiptPage.module.css`:
```css
/* Line ~260 */
.thermalContainer {
    width: 58mm;  /* Changed from 80mm */
    /* ... */
}

/* Line ~64 (in @media print) */
.thermalContainer {
    width: 58mm !important;  /* Changed from 80mm */
    /* ... */
}
```

### Adjusting Font Sizes
All font sizes use `pt` units for print consistency:
- Thermal: 7pt-12pt
- A4: 8pt-14pt

Edit the respective sections in the CSS file.

### Adding Custom Fields
1. Add field to `ReceiptContent` component in `PrintReceiptPage.tsx`
2. Ensure proper text wrapping classes are applied
3. Test with long values

## Known Limitations

1. **@page rules**: CSS `@page` rules have limited browser support. The default is set for thermal (80mm). A4 printing relies on browser defaults.

2. **Print preview**: Browser print preview may not exactly match final output. Always test with actual printer.

3. **Cross-browser**: Print behavior varies across browsers. Chrome/Chromium provides the most consistent results.

4. **Dynamic page size**: Cannot dynamically switch `@page` size based on format selection due to CSS limitations. Thermal is the default.

## Future Enhancements

### Potential Improvements
- [ ] Add 58mm thermal option in UI (currently requires CSS edit)
- [ ] PDF generation for email/download
- [ ] Print queue management
- [ ] Custom receipt templates
- [ ] Barcode/QR code support
- [ ] Multi-language support

## Support

For issues or questions:
1. Check this documentation
2. Verify browser print settings
3. Test with different browsers
4. Check browser console for errors
5. Verify receipt data is loading correctly

## Version History

### v1.0.0 (Current)
- Initial implementation
- 80mm thermal support
- A4 dual-copy support
- Multi-copy thermal printing
- User preference persistence
- Comprehensive text wrapping
- Print-optimized CSS
