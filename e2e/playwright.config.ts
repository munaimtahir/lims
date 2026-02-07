import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from e2e/.env (can be overridden via ENV_PATH)
dotenv.config({ path: process.env.ENV_PATH || path.join(__dirname, '.env') });

const isCI = process.env.CI === 'true' || process.env.CI === '1';
const baseURL =
  process.env.E2E_BASE_URL ||
  process.env.PLAYWRIGHT_BASE_URL ||
  process.env.BASE_URL ||
  'http://localhost:8012';
const storageStatePath = path.join(__dirname, '.auth', 'storageState.json');

export default defineConfig({
  testDir: path.join(__dirname, 'tests'),
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  reporter: [
    ['list'],
    ['html', { outputFolder: path.join(__dirname, 'artifacts', 'playwright-report') }],
  ],
  outputDir: path.join(__dirname, 'artifacts', 'test-results'),
  globalSetup: './fixtures/auth.setup.ts',
  use: {
    baseURL,
    browserName: 'chromium',
    headless: true,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    storageState: storageStatePath,
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
