# Architecture
**Backend:** Python 3.12, Django 5, Django REST Framework, PostgreSQL 16, Redis (tasks/cache).  
**Frontend:** React 18 + TypeScript, Vite, React Query, Zod, React Hook Form, Playwright for e2e.  
**Infra:** Docker Compose for dev, GitHub Actions for CI, containerized services.

## Domain (initial slices)
1. Patient Registration (MVP)
2. Orders & Test Catalog
3. Sample Collection & Tracking
4. Result Entry → Verification → Publish
5. Reporting: PDF with college-approved templates
6. Users/Roles: Admin, Reception, Phlebotomy, Technologist, Pathologist
