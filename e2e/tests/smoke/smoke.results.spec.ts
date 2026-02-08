import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/DashboardPage';
import { ResultsPage } from '../../pages/ResultsPage';
import { waitForTableLoaded } from '../../utils/waiters';
import { selectors } from '../../utils/selectors';

// Smoke 3: Navigate to Results module
// Smoke 4: Open a Result detail when available

test.describe('results module @smoke', () => {
  test('results worklist renders @smoke', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.openResults();

    const results = new ResultsPage(page);
    await results.ensureWorklistVisible();
    await waitForTableLoaded(page, { tableSelector: selectors.results.table, emptySelector: selectors.results.emptyMessage });

    const hasRows = await results.hasRows();
    if (hasRows) {
      const rowCount = await page.locator(selectors.results.rows).count();
      await expect(rowCount).toBeGreaterThan(0);
      const patientCellText = await page.locator(selectors.results.rows).first().locator('td').nth(1).innerText();
      expect(patientCellText.trim()).not.toBe('');
      expect(patientCellText.trim()).not.toBe('—');
    } else {
      await results.expectEmptyState();
    }
  });

  test('open first result detail if present @smoke', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.openResults();

    const results = new ResultsPage(page);
    await results.ensureWorklistVisible();
    const opened = await results.openFirstResultIfPresent();

    if (!opened) {
      await results.expectEmptyState();
      test.info().annotations.push({ type: 'data', description: 'No result rows available to open' });
      return;
    }

    await results.expectDetailView();
  });

  test('save and verify results when available @smoke', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.openResults();

    const results = new ResultsPage(page);
    await results.ensureWorklistVisible();
    const opened = await results.openFirstResultIfPresent();

    if (!opened) {
      await results.expectEmptyState();
      test.info().annotations.push({ type: 'data', description: 'No result rows available to save/verify' });
      return;
    }

    await results.expectDetailView();

    const inputs = page.locator('input[placeholder="Enter value"]');
    const inputCount = await inputs.count();
    if (inputCount === 0) {
      test.info().annotations.push({ type: 'data', description: 'No editable inputs available for save/verify' });
      return;
    }

    for (let i = 0; i < inputCount; i += 1) {
      await inputs.nth(i).fill('1');
    }

    const saveResponsePromise = page.waitForResponse((resp) =>
      resp.url().includes('/api/v1/results/bulk_entry/') && resp.request().method() === 'POST'
    );
    await page.getByRole('button', { name: /Save Draft/i }).first().click();
    const saveResponse = await saveResponsePromise;
    expect(saveResponse.status()).toBeGreaterThanOrEqual(200);

    page.once('dialog', (dialog) => dialog.accept());
    const verifyResponsePromise = page.waitForResponse((resp) =>
      resp.url().includes('/api/v1/results/bulk-verify/') && resp.request().method() === 'POST'
    );
    await page.getByRole('button', { name: /Save & Verify/i }).first().click();
    const verifyResponse = await verifyResponsePromise;
    expect(verifyResponse.status()).toBe(200);

    await expect(page.getByText(/All results have been verified/i).first()).toBeVisible();
  });
});
