# How to Run the LIMS Frontend

## Prerequisites

- Node.js 18+ (recommended: v20)
- pnpm 8.15.9+
- Backend API running (see backend/README.md)

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
pnpm install --frozen-lockfile
```

### 2. Start Development Server

```bash
pnpm dev
```

The frontend will be available at **http://localhost:5173**

### 3. Login

Use one of these demo accounts:

| Username | Password | Role | Access |
|----------|----------|------|--------|
| admin | admin123 | Admin | Full access to all features |
| reception | reception123 | Reception | Patient registration, orders |
| phlebotomy | phlebotomy123 | Phlebotomy | Sample collection |
| tech | tech123 | Technologist | Sample receiving, result entry |
| pathologist | path123 | Pathologist | Result verification, publishing, reports |

**⚠️ For production, create secure users with `python manage.py createsuperuser`**

## Environment Configuration

### Development Mode

The frontend uses `VITE_API_URL` to configure the API endpoint:

**Default behavior (no configuration needed):**
- Development: `http://localhost:8000/api` (direct backend access)
- Production: `/api` (assumes nginx proxy)

**To override, create `.env.development`:**
```bash
VITE_API_URL=http://localhost:8000/api
```

### Production Mode

**For production with nginx proxy (recommended):**
```bash
# .env.production
VITE_API_URL=/api
```

**For production without proxy (direct backend):**
```bash
# .env.production
VITE_API_URL=http://your-backend-ip:8000/api
```

## Available Scripts

```bash
# Development server
pnpm dev

# Build for production
pnpm build

# Build for development (with source maps)
pnpm build:dev

# Preview production build
pnpm preview

# Run tests
pnpm test

# Run tests with UI
pnpm test:ui

# Run tests with coverage
pnpm test:coverage

# Lint code
pnpm lint

# Format code
pnpm format

# Check formatting
pnpm format:check

# Run E2E tests with Playwright
pnpm playwright

# Install Playwright browsers
pnpm playwright:install
```

## Features & Navigation

After logging in, you'll have access to:

### For All Users
- **Home** - Dashboard overview
- **Lab** - Lab home with quick actions

### For Reception
- **Patients** - Search, view, and manage patients
- **Lab → New Lab Slip** - Register patients and create orders

### For Phlebotomy Staff
- **Phlebotomy** - Collect and receive samples
- **Worklist** - View pending samples

### For Technologists
- **Phlebotomy** - Receive samples
- **Result Entry** - Enter test results
- **Worklist** - View samples and results

### For Pathologists
- **Verification** - Verify entered results
- **Publishing** - Publish verified results
- **Reports** - Generate and download PDF reports

### For Admins
- **Dashboard** - Analytics and statistics
- **Data Import** - CSV import documentation
- **Settings** - User management, test catalog, terminals
- Full access to all features

## Complete Workflow

1. **Register Patient** (Reception)
   - Go to Lab → New Lab Slip
   - Enter patient details (CNIC, phone, name, etc.)
   - Select tests from catalog
   - Create order

2. **Collect Sample** (Phlebotomy)
   - Go to Phlebotomy
   - Find pending samples
   - Click "Collect" to mark as collected

3. **Receive Sample** (Technologist)
   - Go to Phlebotomy
   - Find collected samples
   - Click "Receive" to accept in lab

4. **Enter Results** (Technologist)
   - Go to Result Entry
   - Select a result from the list
   - Enter value, unit, reference range
   - Click "Enter Result"

5. **Verify Results** (Pathologist)
   - Go to Verification
   - Review entered results
   - Check reference ranges
   - Click "Verify Result" or "Reject & Send Back"

6. **Publish Results** (Pathologist)
   - Go to Publishing
   - Select verified results
   - Click "Publish Selected"

7. **Generate Report** (Pathologist)
   - Go to Reports
   - Select an order with published results
   - Click "Generate Report"
   - Download PDF

## Development Tips

### Hot Reload
Changes to TypeScript/React files automatically reload in development mode.

### Debugging
- Use React DevTools browser extension
- Check browser console for errors
- Use network tab to inspect API calls

### Testing
```bash
# Run tests in watch mode
pnpm test

# Run specific test file
pnpm test PatientListPage

# Generate coverage report
pnpm test:coverage
```

### Code Quality
```bash
# Check for TypeScript errors
pnpm tsc --noEmit

# Lint code
pnpm lint

# Format code
pnpm format
```

## Troubleshooting

### Backend Connection Issues

**Problem:** "Failed to load" or API errors

**Solution:**
1. Ensure backend is running on port 8000
2. Check `VITE_API_URL` configuration
3. Verify backend health: `curl http://localhost:8000/api/health/`

### Build Errors

**Problem:** TypeScript compilation errors

**Solution:**
```bash
# Clean and reinstall
rm -rf node_modules pnpm-lock.yaml dist
pnpm install --frozen-lockfile
pnpm build
```

### Test Failures

**Problem:** Tests fail after changes

**Solution:**
```bash
# Run tests with verbose output
pnpm test --reporter=verbose

# Clear test cache
rm -rf node_modules/.vitest
pnpm test
```

## Production Deployment

### Building

```bash
# Install dependencies
pnpm install --frozen-lockfile

# Build for production
pnpm build
```

The production build will be in the `dist/` directory.

### Serving with Docker

The entire stack (backend + frontend + nginx) can be deployed with:

```bash
cd ..  # Go to root directory
docker compose up -d
```

Frontend will be available at **http://localhost** (port 80)

### Serving with Custom Web Server

Copy the `dist/` directory to your web server:

```bash
# Example with nginx
cp -r dist/* /var/www/html/
```

Ensure your web server proxies `/api/*` requests to the backend.

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions

## Known Limitations

- CSV imports are handled via Django management commands (documented in Data Import page)
- PDF generation requires backend access
- No offline mode (requires active backend connection)

## Support

For issues or questions:
1. Check backend logs: `docker compose logs backend`
2. Check frontend console in browser DevTools
3. Review API documentation: `docs/API.md`
4. Check test coverage: `docs/TESTS_COVERAGE.md`
