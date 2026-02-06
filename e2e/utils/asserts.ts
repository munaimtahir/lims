import { Page, expect } from '@playwright/test';

export async function expectVisible(page: Page, selector: string, message?: string) {
  await expect(page.locator(selector), message).toBeVisible();
}

export async function expectHasText(page: Page, selector: string, text: string, message?: string) {
  await expect(page.locator(selector), message).toHaveText(text);
}
