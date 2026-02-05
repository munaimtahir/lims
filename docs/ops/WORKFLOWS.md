# CI/CD Workflows

This document summarizes the GitHub Actions workflows configured for the repository and how to run them.

## Workflow Inventory

| Workflow | File | Trigger | Output |
| --- | --- | --- | --- |
| Backend CI | `.github/workflows/backend-ci.yml` | Manual (`workflow_dispatch`) | Coverage artifact (`backend-coverage-report`) |
| Frontend CI | `.github/workflows/frontend-ci.yml` | Manual (`workflow_dispatch`) | Build artifact (`frontend-build`) |
| Docker CI | `.github/workflows/docker-ci.yml` | Manual (`workflow_dispatch`) | Validated Docker builds (no artifact) |

## How to Run

1. Navigate to **Actions** in GitHub.
2. Select the workflow you want to run.
3. Click **Run workflow** (manual trigger).

## Notes

- These workflows are currently **manual-only** to protect production stability and control execution costs.
- Each workflow includes explicit build/lint/test steps, plus artifact upload where relevant.
