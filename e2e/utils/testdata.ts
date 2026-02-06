import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: process.env.ENV_PATH || path.join(__dirname, '..', '.env') });

export const testUser = {
  email: process.env.E2E_USER_EMAIL || '',
  password: process.env.E2E_USER_PASSWORD || '',
};

export const flags = {
  allowWrites: (process.env.E2E_ALLOW_WRITES || 'false').toLowerCase() === 'true',
};

export function requireCredentials() {
  if (!testUser.email || !testUser.password) {
    throw new Error('E2E_USER_EMAIL and E2E_USER_PASSWORD must be set in e2e/.env');
  }
}
