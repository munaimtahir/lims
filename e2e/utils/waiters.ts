import { Page, expect } from '@playwright/test';

export async function waitForAppReady(page: Page) {
  await expect(page.locator('[data-testid="app-ready"]')).toBeVisible({ timeout: 15_000 });
}
