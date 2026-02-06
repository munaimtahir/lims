import { test as base, expect } from '@playwright/test';
import { waitForAppReady } from '../utils/waiters';

export const test = base.extend({
  authenticatedPage: async ({ page }, use) => {
    await page.goto('/dashboard');
    await waitForAppReady(page);
    await use(page);
  },
});

export { expect };
