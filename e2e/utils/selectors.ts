export const selectors = {
  login: {
    email: '[data-testid="login-email"]',
    password: '[data-testid="login-password"]',
    submit: '[data-testid="login-submit"]',
  },
  dashboard: {
    shell: '[data-testid="dashboard-shell"]',
    username: '[data-testid="topbar-username"]',
    mainArea: '[data-testid="app-ready"]',
    navResults: 'nav a:has-text("Results")',
    navDashboard: 'nav a:has-text("Dashboard")',
  },
  results: {
    heading: 'h1:has-text("Pending Results Worklist")',
    table: 'table',
    rows: 'table tbody tr',
    emptyMessage: 'text=No pending results found.',
    enterButton: 'table tbody tr button:has-text("Enter Results")',
    detailHeader: 'h1:has-text("Result Entry")',
    backButton: 'button:has-text("Back to Worklist")',
  },
  common: {
    toast: '[role="alert"], [role="status"], .Toastify__toast, .toast-success',
  },
};
