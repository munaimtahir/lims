import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/DashboardPage';
import { selectors } from '../../utils/selectors';

test.describe('patients worklist @smoke', () => {
  test('print buttons open targets when available @smoke', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    await page.goto('/dashboard/patients-worklist');
    await page.waitForSelector('table');

    const receiptButton = page.locator(`${selectors.worklist.printReceipt}[data-available="true"]`).first();
    if (await receiptButton.count() === 0) {
      test.info().annotations.push({ type: 'data', description: 'No printable receipt available in worklist' });
    } else {
      const popupPromise = page.waitForEvent('popup');
      await receiptButton.click();
      const popup = await popupPromise;
      expect(popup.url()).toMatch(/print\/receipt|receipt/i);
      await popup.close();
    }

    const reportButton = page.locator(`${selectors.worklist.printReport}[data-available="true"]`).first();
    if (await reportButton.count() === 0) {
      test.info().annotations.push({ type: 'data', description: 'No printable report available in worklist' });
    } else {
      const popupPromise = page.waitForEvent('popup');
      await reportButton.click();
      const popup = await popupPromise;
      expect(popup.url()).toMatch(/print\/report|report.*\\.pdf/i);
      await popup.close();
    }
  });
});
