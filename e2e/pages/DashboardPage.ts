import { BasePage } from './BasePage';
import { selectors } from '../utils/selectors';
import { waitForAppReady } from '../utils/waiters';

export class DashboardPage extends BasePage {
  async goto() {
    await super.goto('/dashboard');
    await waitForAppReady(this.page);
  }

  async expectShellVisible() {
    await this.expectVisible(selectors.dashboard.shell, 'Dashboard shell should be visible');
  }

  async expectUsername(email: string) {
    await this.expectText(selectors.dashboard.username, email, 'Logged in user email should be shown');
  }

  async openResults() {
    await this.click(selectors.dashboard.navResults);
    await waitForAppReady(this.page);
  }
}
