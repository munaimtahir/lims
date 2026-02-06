import { BasePage } from './BasePage';
import { selectors } from '../utils/selectors';
import { testUser, requireCredentials } from '../utils/testdata';

export class LoginPage extends BasePage {
  async goto() {
    await super.goto('/login');
  }

  async login(email?: string, password?: string) {
    const userEmail = email || testUser.email;
    const userPassword = password || testUser.password;
    requireCredentials();
    await this.fill(selectors.login.email, userEmail);
    await this.fill(selectors.login.password, userPassword);
    await this.click(selectors.login.submit);
  }
}
