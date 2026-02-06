import { expect } from '@playwright/test';
import { BasePage } from './BasePage';
import { selectors } from '../utils/selectors';
import { waitForTableLoaded } from '../utils/waiters';

export class ResultsPage extends BasePage {
  async goto() {
    await super.goto('/dashboard/results');
    await waitForTableLoaded(this.page, { tableSelector: selectors.results.table, emptySelector: selectors.results.emptyMessage });
  }

  async ensureWorklistVisible() {
    await expect(this.page.getByRole('heading', { name: /Pending Results Worklist/i })).toBeVisible();
  }

  async hasRows() {
    return await this.page.locator(selectors.results.rows).count() > 0;
  }

  async openFirstResultIfPresent() {
    const rows = this.page.locator(selectors.results.rows);
    if (await rows.count() === 0) return false;
    const enterButton = this.page.locator(selectors.results.enterButton).first();
    await expect(enterButton).toBeVisible();
    await enterButton.click();
    await waitForTableLoaded(this.page, { tableSelector: selectors.results.detailHeader, emptySelector: selectors.results.detailHeader });
    return true;
  }

  async expectEmptyState() {
    await expect(this.page.locator(selectors.results.emptyMessage)).toBeVisible();
  }

  async expectDetailView() {
    await expect(this.page.locator(selectors.results.detailHeader)).toBeVisible();
  }
}
