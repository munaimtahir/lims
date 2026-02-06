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
});
