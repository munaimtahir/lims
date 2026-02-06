import { test, expect } from '@playwright/test';

// Minimal harness check to ensure Playwright test runner executes independently of app state
test('sanity harness executes', async ({ page }) => {
  await page.goto('about:blank');
  await page.setContent('<main data-testid="sanity">sanity-ok</main>');
  await expect(page.getByTestId('sanity')).toHaveText('sanity-ok');
});
