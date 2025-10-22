# 🧩 Coding Standards — LIMS

## Python
- Use FastAPI conventions.
- Format with Black + isort.
- Use Pydantic for validation.
- Each router exports an APIRouter instance.

## TypeScript
- Functional React components only.
- API calls via `NEXT_PUBLIC_API_BASE`.
- Use Tailwind CSS for styling.
- Reusable components in `/frontend/components/`.

## Commits
Follow **Conventional Commits**:
```
feat: add voice registration
fix: resolve build issue
chore: update dependencies
```

## Tests
- Backend: pytest
- Frontend: Jest/Vitest (future integration)
