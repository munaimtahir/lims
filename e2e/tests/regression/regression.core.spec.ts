import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/DashboardPage';
import { waitForAppReady } from '../../utils/waiters';
import { requireCredentials } from '../../utils/testdata';

// Regression check: unauthenticated users are redirected to login
test('protected routes require auth @regression', async ({ browser }) => {
  requireCredentials();
  const baseURL = process.env.BASE_URL || 'http://localhost:8012';
  const context = await browser.newContext({ baseURL, storageState: { cookies: [], origins: [] } });
  const page = await context.newPage();
  await page.goto('/dashboard');
  await expect(page.getByTestId('login-email')).toBeVisible();
  await context.close();
});

// Regression check: direct deep link to results works when authenticated
test('deep link to results renders worklist @regression', async ({ page }) => {
  const dashboard = new DashboardPage(page);
  await dashboard.goto();
  await page.goto('/dashboard/results');
  await waitForAppReady(page);
  await expect(page.getByRole('heading', { name: /Pending Results Worklist/i })).toBeVisible();
  await expect(page.locator('table')).toBeVisible();
});
