import { Page, expect } from '@playwright/test';
import { selectors } from './selectors';

export async function waitForAppReady(page: Page) {
  await page.waitForLoadState('domcontentloaded');
  await expect(page.locator(selectors.dashboard.shell)).toBeVisible({ timeout: 20_000 });
}

export async function waitForTableLoaded(page: Page, options?: { tableSelector?: string; emptySelector?: string }) {
  const tableSelector = options?.tableSelector || selectors.results.table;
  const emptySelector = options?.emptySelector || selectors.results.emptyMessage;
  // Use locator.any to avoid Playwright css parsing issues with text selectors
  const table = page.locator(tableSelector);
  const empty = page.locator(emptySelector);
  await Promise.race([table.first().waitFor({ state: 'visible', timeout: 15_000 }), empty.first().waitFor({ state: 'visible', timeout: 15_000 })]);
}

export async function waitForToastSuccess(page: Page, text: string | RegExp = /success/i) {
  const toast = page.locator(selectors.common.toast).filter({ hasText: text });
  await expect(toast.first()).toBeVisible({ timeout: 10_000 });
}

export async function waitForNetworkIdleSafe(page: Page) {
  try {
    await page.waitForLoadState('networkidle', { timeout: 10_000 });
  } catch (err) {
    // Ignore timeouts; networkidle can be flaky on long polling apps
  }
}
