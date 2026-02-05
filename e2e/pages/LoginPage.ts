import { BasePage } from './BasePage';
import { selectors } from '../utils/selectors';

export class LoginPage extends BasePage {
  async goto() {
    await super.goto('/login');
  }

  async login(email: string, password: string) {
    await this.fill(selectors.login.email, email);
    await this.fill(selectors.login.password, password);
    await this.click(selectors.login.submit);
  }
}
