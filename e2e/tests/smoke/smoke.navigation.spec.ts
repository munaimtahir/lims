import { test } from '@playwright/test';
import { DashboardPage } from '../../pages/DashboardPage';
import { testUser } from '../../utils/testdata';

// Smoke 1: App shell loads
test('dashboard shell renders with user info @smoke', async ({ page }) => {
  const dashboard = new DashboardPage(page);
  await dashboard.goto();
  await dashboard.expectShellVisible();
  await dashboard.expectUsername(testUser.email);
});
