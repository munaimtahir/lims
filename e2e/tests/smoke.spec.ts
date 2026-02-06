import { test } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { expectVisible, expectHasText } from '../utils/assertions';
import { waitForAppReady } from '../utils/waiters';
import users from '../data/users.json' assert { type: 'json' };

// One intent: verify login happy path shows dashboard shell
// Idempotent: relies on stable test user and does not mutate data

test.describe('Smoke: Login', () => {
  test('logs in and sees dashboard shell', async ({ page }) => {
    const login = new LoginPage(page);

    await login.goto();
    await login.login(users.valid.email, users.valid.password);

    await waitForAppReady(page);
    await expectVisible(page, '[data-testid="dashboard-shell"]', 'Dashboard should be visible after login');
    await expectHasText(page, '[data-testid="topbar-username"]', users.valid.email, 'User email should be shown');
  });
});
