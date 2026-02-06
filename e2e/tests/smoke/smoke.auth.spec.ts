import { test } from '@playwright/test';
import { DashboardPage } from '../../pages/DashboardPage';
import { waitForAppReady } from '../../utils/waiters';
import { testUser, requireCredentials } from '../../utils/testdata';

// Smoke 2: Authenticated session via storageState should land on dashboard
test('authenticated session shows dashboard shell @smoke', async ({ page }) => {
  requireCredentials();
  await page.goto('/dashboard');
  await waitForAppReady(page);

  const dashboard = new DashboardPage(page);
  await dashboard.expectShellVisible();
  await dashboard.expectUsername(testUser.email);
});
