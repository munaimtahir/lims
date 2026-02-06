import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

// Allow overriding the env file path via ENV_PATH; default to .env in /e2e
dotenv.config({ path: process.env.ENV_PATH || '.env' });

const isCI = !!process.env.CI;
const baseURL = process.env.BASE_URL || 'http://localhost:8012';

export default defineConfig({
  testDir: '../tests',
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  timeout: 60_000,
  reporter: [
    ['list'],
    ['html', { outputFolder: '../artifacts/html-report' }],
  ],
  use: {
    baseURL,
    browserName: 'chromium',
    headless: true,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15_000,
    navigationTimeout: 20_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  outputDir: '../artifacts/test-output',
});
