import { Outlet, NavLink, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useBranding } from '../../contexts/BrandingContext';
import { TopHeader } from './TopHeader';
import styles from './DashboardLayout.module.css';


export default function DashboardLayout() {
  const { user, logout, currentBranch } = useAuth();
  const { branding } = useBranding();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  type NavChild = { to: string; label: string };
  type NavItem = { label: string; to?: string; children?: NavChild[] };

  // Get navigation items based on user role
  const getNavItems = () => {
    const items: NavItem[] = [];

    if (!user) return items;

    const addSection = (label: string, children: NavChild[]) => {
      if (children.length) {
        items.push({ label, children });
      }
    };

    switch (user.role) {
      case 'Admin':
        addSection('Operations', [
          { to: '/dashboard/registration', label: 'Registration' },
          { to: '/dashboard/patients', label: 'Patients' },
          { to: '/dashboard/patients-worklist', label: 'Worklist' },
          { to: '/dashboard/samples', label: 'Samples' },
        ]);

        addSection('Results', [
          { to: '/dashboard/results', label: 'Result Entry' },
          { to: '/dashboard/verification', label: 'Verification' },
          { to: '/dashboard/reports', label: 'My Reports' },
        ]);
        addSection('Analytics & Reports', [
          { to: '/dashboard/analytics', label: 'Overview' },
          { to: '/dashboard/analytics/patients', label: 'Patients' },
          { to: '/dashboard/analytics/tests', label: 'Tests' },
          { to: '/dashboard/analytics/referrals', label: 'Referrals' },
          { to: '/dashboard/analytics/finance', label: 'Finance' },
          { to: '/dashboard/analytics/export-logs', label: 'Export Logs' },
        ]);

        addSection('Administration', [
          { to: '/dashboard/settings?tab=ui', label: 'UI Update' },
          { to: '/dashboard/settings?tab=users', label: 'User Management' },
          { to: '/dashboard/settings?tab=reports', label: 'Report Customization' },
          { to: '/dashboard/settings?tab=print', label: 'Print Templates' },
          { to: '/dashboard/tests', label: 'Test Catalog' },
          { to: '/dashboard/tests?tab=parameters', label: 'Parameters' },
          { to: '/dashboard/tests?tab=ranges', label: 'Normal Ranges' },
          { to: '/dashboard/audit', label: 'Audit Logs' },
          { to: '/dashboard/backups', label: 'Backups' },
        ]);
        break;
      case 'Receptionist':
        addSection('Operations', [
          { to: '/dashboard/registration', label: 'Registration' },
          { to: '/dashboard/patients', label: 'Patients' },
          { to: '/dashboard/patients-worklist', label: 'Worklist' },
        ]);
        break;
      case 'Phlebotomist':
        addSection('Operations', [
          { to: '/dashboard/collection', label: 'Collection Worklist' },
          { to: '/dashboard/samples', label: 'Samples' },
        ]);
        break;
      case 'Lab Technician':
        addSection('Results', [
          { to: '/dashboard/results', label: 'Result Entry' },
        ]);
        addSection('Operations', [
          { to: '/dashboard/samples', label: 'Samples' },
        ]);
        break;
      case 'Pathologist':
        addSection('Results', [
          { to: '/dashboard/verification', label: 'Verification' },
          { to: '/dashboard/reports', label: 'Reports' },
        ]);
        addSection('Administration', [
          { to: '/dashboard/backups', label: 'Backups' },
        ]);
        break;

      case 'Manager':
        addSection('Analytics & Reports', [
          { to: '/dashboard/analytics', label: 'Overview' },
          { to: '/dashboard/analytics/patients', label: 'Patients' },
          { to: '/dashboard/analytics/tests', label: 'Tests' },
          { to: '/dashboard/analytics/referrals', label: 'Referrals' },
          { to: '/dashboard/analytics/finance', label: 'Finance' },
          { to: '/dashboard/analytics/export-logs', label: 'Export Logs' },
        ]);
        addSection('Results', [
          { to: '/dashboard/reports', label: 'My Reports' },
        ]);
        addSection('Administration', [
          { to: '/dashboard/settings?tab=users', label: 'User Management' },
          { to: '/dashboard/settings?tab=reports', label: 'Report Customization' },
          { to: '/dashboard/settings?tab=print', label: 'Print Templates' },
          { to: '/dashboard/tests', label: 'Test Catalog' },
          { to: '/dashboard/tests?tab=parameters', label: 'Parameters' },
          { to: '/dashboard/tests?tab=ranges', label: 'Normal Ranges' },
          { to: '/dashboard/audit', label: 'Audit Logs' },
          { to: '/dashboard/backups', label: 'Backups' },
        ]);
        break;
    }


    // Filter out restricted sections based on branch capability
    if (currentBranch?.capability_mode === 'COLLECT_ONLY') {
      return items.filter(item => item.label !== 'Results');
    }

    return items;
  };

  const displayName = branding?.lab_display_name || branding?.lab_name || 'LIMS';
  const logoUrl = branding?.lab_logo;

  return (
    <div className={styles.layout} data-testid="dashboard-shell">
      <nav className={styles.sidebar}>
        <Link to="/dashboard" className={styles.logo}>
          {logoUrl && (
            <img src={logoUrl} alt={displayName} className={styles.logoImage} />
          )}
          <h1>{displayName}</h1>
        </Link>

        <ul className={styles.navList}>
          {getNavItems().map((item) => (
            <li key={item.to ?? item.label}>
              {item.to ? (
                <NavLink
                  to={item.to}
                  end={item.to === '/dashboard'}
                  className={({ isActive }) =>
                    isActive ? `${styles.navLink} ${styles.active}` : styles.navLink
                  }
                >
                  {item.label}
                </NavLink>
              ) : (
                <div className={styles.navSection}>{item.label}</div>
              )}
              {item.children && (
                <ul className={styles.subNavList}>
                  {item.children.map((child) => (
                    <li key={child.to}>
                      <NavLink
                        to={child.to}
                        className={({ isActive }) =>
                          isActive ? `${styles.subNavLink} ${styles.active}` : styles.subNavLink
                        }
                      >
                        {child.label}
                      </NavLink>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>

        <div className={styles.userInfo}>
          <div className={styles.userName}>{user?.full_name}</div>
          <div className={styles.userRole} data-testid="topbar-username">{user?.email}</div>
          <button onClick={handleLogout} className={styles.logoutButton}>
            Sign Out
          </button>
        </div>
      </nav>

      <main className={styles.main} data-testid="app-ready">
        <TopHeader />
        <Outlet />
      </main>
    </div>
  );
}
