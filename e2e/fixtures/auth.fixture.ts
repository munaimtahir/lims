import { test as base } from '@playwright/test';
import users from '../data/users.json' assert { type: 'json' };
import { LoginPage } from '../pages/LoginPage';
import { waitForAppReady } from '../utils/waiters';

export const test = base.extend({
  authenticatedPage: async ({ page }, use) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.login(users.valid.email, users.valid.password);
    await waitForAppReady(page);
    await use(page);
  },
});

export { expect } from '@playwright/test';
