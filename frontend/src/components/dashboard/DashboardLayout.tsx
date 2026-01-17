import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import styles from './DashboardLayout.module.css';

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Get navigation items based on user role
  const getNavItems = () => {
    const items: { to: string; label: string; children?: { to: string; label: string }[] }[] = [];
    
    if (!user) return items;

    // Common items for all roles
    items.push({ to: '/dashboard', label: 'Dashboard' });

    switch (user.role) {
      case 'Admin':
        items.push(
          { to: '/dashboard/patients', label: 'Patients' },
          { to: '/dashboard/patients-worklist', label: 'Worklist' },
          { to: '/dashboard/samples', label: 'Samples' },
          { to: '/dashboard/results', label: 'Results' },
          { to: '/dashboard/reports', label: 'Reports' },
          { to: '/dashboard/payments', label: 'Payments' },
          { to: '/dashboard/audit', label: 'Audit Logs' },
          {
            to: '/dashboard/settings',
            label: 'Settings',
            children: [
              { to: '/dashboard/settings?tab=reports', label: 'Report Customization' },
              { to: '/dashboard/tests', label: 'Test Catalog' },
              { to: '/dashboard/reference-ranges', label: 'Normal Ranges' },
            ],
          }
        );
        break;
      case 'Receptionist':
        items.push(
          { to: '/dashboard/patients', label: 'Patients' },
          { to: '/dashboard/patients-worklist', label: 'Worklist' },
          { to: '/dashboard/payments', label: 'Payments' }
        );
        break;
      case 'Cashier':
        items.push(
          { to: '/dashboard/payments', label: 'Payments' }
        );
        break;
      case 'Phlebotomist':
        items.push(
          { to: '/dashboard/collection', label: 'Collection Worklist' },
          { to: '/dashboard/samples', label: 'Samples' }
        );
        break;
      case 'Lab Technician':
        items.push(
          { to: '/dashboard/worklist', label: 'Result Entry' },
          { to: '/dashboard/samples', label: 'Samples' }
        );
        break;
      case 'Pathologist':
        items.push(
          { to: '/dashboard/review', label: 'Review Queue' },
          { to: '/dashboard/reports', label: 'Reports' }
        );
        break;
      case 'Manager':
        items.push(
          { to: '/dashboard/reports', label: 'Reports' },
          { to: '/dashboard/audit', label: 'Audit Logs' },
          {
            to: '/dashboard/settings',
            label: 'Settings',
            children: [
              { to: '/dashboard/settings?tab=reports', label: 'Report Customization' },
              { to: '/dashboard/tests', label: 'Test Catalog' },
              { to: '/dashboard/reference-ranges', label: 'Normal Ranges' },
            ],
          }
        );
        break;
    }

    return items;
  };

  return (
    <div className={styles.layout}>
      <nav className={styles.sidebar}>
        <div className={styles.logo}>
          <h1>LIMS</h1>
        </div>
        
        <ul className={styles.navList}>
          {getNavItems().map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === '/dashboard'}
                className={({ isActive }) =>
                  isActive ? `${styles.navLink} ${styles.active}` : styles.navLink
                }
              >
                {item.label}
              </NavLink>
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
          <div className={styles.userRole}>{user?.role}</div>
          <button onClick={handleLogout} className={styles.logoutButton}>
            Sign Out
          </button>
        </div>
      </nav>
      
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
