import { Page, Locator, expect } from '@playwright/test';
import { waitForNetworkIdleSafe } from '../utils/waiters';

export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  protected locator(selector: string): Locator {
    return this.page.locator(selector);
  }

  async goto(path = '/') {
    await this.page.goto(path);
    await waitForNetworkIdleSafe(this.page);
  }

  async click(selector: string) {
    const el = this.locator(selector);
    await expect(el, `Element not clickable: ${selector}`).toBeVisible();
    await el.click();
  }

  async fill(selector: string, value: string) {
    const el = this.locator(selector);
    await expect(el, `Input not visible: ${selector}`).toBeVisible();
    await el.fill(value);
  }

  async expectVisible(selector: string, message?: string) {
    await expect(this.locator(selector), message).toBeVisible();
  }

  async expectText(selector: string, text: string | RegExp, message?: string) {
    await expect(this.locator(selector), message).toContainText(text);
  }
}
