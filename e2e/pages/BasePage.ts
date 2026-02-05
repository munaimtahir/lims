import { Page, Locator, expect } from '@playwright/test';

export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  protected locator(selector: string): Locator {
    return this.page.locator(selector);
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

  async goto(path = '/') {
    await this.page.goto(path);
  }
}
