# Testing Strategy
- **Backend:** pytest, pytest-django, factory_boy, freezegun; coverage target 100%, fail under=100.
- **Frontend:** Vitest + React Testing Library unit tests; Playwright e2e flows.
- **Contracts:** Schemas validated with pydantic/zod; strict typing enforced in CI.
- **Seed tests:** a golden-path e2e registering a patient and placing an order.
