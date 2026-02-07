import { chromium, FullConfig } from '@playwright/test';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { selectors } from '../utils/selectors';
import { waitForAppReady } from '../utils/waiters';
import { testUser, requireCredentials } from '../utils/testdata';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const storageStatePath = path.join(__dirname, '..', '.auth', 'storageState.json');

async function globalSetup(config: FullConfig) {
  dotenv.config({ path: process.env.ENV_PATH || path.join(__dirname, '..', '.env') });
  requireCredentials();

  const baseURL =
    process.env.E2E_BASE_URL ||
    process.env.PLAYWRIGHT_BASE_URL ||
    process.env.BASE_URL ||
    (config.projects[0].use?.baseURL as string) ||
    'http://localhost:8012';

  fs.mkdirSync(path.dirname(storageStatePath), { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ baseURL });

  await page.goto('/login');
  await page.fill(selectors.login.email, testUser.email);
  await page.fill(selectors.login.password, testUser.password);
  await page.click(selectors.login.submit);
  await waitForAppReady(page);

  await page.context().storageState({ path: storageStatePath });
  await browser.close();
}

export default globalSetup;
