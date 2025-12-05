import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { dashboardApi } from '../../api/services';
import styles from './DashboardHome.module.css';

interface DashboardStatistics {
  today?: {
    orders?: number;
    samples?: number;
    results?: number;
    reports?: number;
    revenue?: number;
  };
  totals?: {
    patients?: number;
    orders?: number;
    results?: number;
  };
  pending?: {
    collections?: number;
    results?: number;
    verifications?: number;
  };
  revenue?: {
    total?: number;
    unpaid?: number;
    today?: number;
  };
  orders?: {
    status_breakdown?: Array<{ status: string; count: number }>;
  };
}

export default function DashboardHome() {
  const { user } = useAuth();
  
  const { data: statistics, isLoading } = useQuery({
    queryKey: ['dashboard-statistics'],
    queryFn: () => dashboardApi.getStatistics(),
  });

  const getWelcomeMessage = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const getRoleDashboard = () => {
    if (isLoading) {
      return <div className={styles.loading}>Loading statistics...</div>;
    }
    
    switch (user?.role) {
      case 'Admin':
        return <AdminDashboard statistics={statistics} />;
      case 'Receptionist':
        return <ReceptionDashboard statistics={statistics} />;
      case 'Cashier':
        return <CashierDashboard statistics={statistics} />;
      case 'Phlebotomist':
        return <PhlebotomistDashboard statistics={statistics} />;
      case 'Lab Technician':
        return <TechnicianDashboard statistics={statistics} />;
      case 'Pathologist':
        return <PathologistDashboard statistics={statistics} />;
      case 'Manager':
        return <ManagerDashboard statistics={statistics} />;
      default:
        return <DefaultDashboard />;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>{getWelcomeMessage()}, {user?.full_name?.split(' ')[0]}!</h1>
        <p className={styles.role}>Logged in as {user?.role}</p>
      </div>
      
      {getRoleDashboard()}
    </div>
  );
}

function AdminDashboard({ statistics }: { statistics?: DashboardStatistics }) {
  return (
    <div className={styles.statsGrid}>
      <StatCard title="Total Patients" value={statistics?.totals?.patients || '0'} icon="👥" />
      <StatCard title="Orders Today" value={statistics?.today?.orders || '0'} icon="📋" />
      <StatCard title="Pending Results" value={statistics?.pending?.results || '0'} icon="🔬" />
      <StatCard title="Reports Generated" value={statistics?.today?.reports || '0'} icon="📄" />
    </div>
  );
}

function ReceptionDashboard({ statistics }: { statistics?: DashboardStatistics }) {
  return (
    <div className={styles.statsGrid}>
      <StatCard title="Orders Created Today" value={statistics?.today?.orders || '0'} icon="📋" />
      <StatCard title="Total Patients" value={statistics?.totals?.patients || '0'} icon="👥" />
      <StatCard title="Pending Payments" value={statistics?.revenue?.unpaid ? `$${statistics.revenue.unpaid}` : '0'} icon="💰" />
    </div>
  );
}

function CashierDashboard({ statistics }: { statistics?: DashboardStatistics }) {
  return (
    <div className={styles.statsGrid}>
      <StatCard title="Payments Today" value={statistics?.today?.revenue ? `$${statistics.today.revenue}` : '$0'} icon="💵" />
      <StatCard title="Pending Orders" value={statistics?.orders?.status_breakdown?.find((s) => s.status === 'pending')?.count || '0'} icon="📋" />
      <StatCard title="Total Revenue" value={statistics?.revenue?.total ? `$${statistics.revenue.total}` : '$0'} icon="💰" />
    </div>
  );
}

function PhlebotomistDashboard({ statistics }: { statistics?: DashboardStatistics }) {
  return (
    <div className={styles.statsGrid}>
      <StatCard title="Pending Collection" value={statistics?.pending?.collections || '0'} icon="💉" />
      <StatCard title="Collected Today" value={statistics?.today?.samples || '0'} icon="✅" />
    </div>
  );
}

function TechnicianDashboard({ statistics }: { statistics?: DashboardStatistics }) {
  return (
    <div className={styles.statsGrid}>
      <StatCard title="Results to Enter" value={statistics?.pending?.results || '0'} icon="📝" />
      <StatCard title="Entered Today" value={statistics?.today?.results || '0'} icon="✅" />
    </div>
  );
}

function PathologistDashboard({ statistics }: { statistics?: DashboardStatistics }) {
  return (
    <div className={styles.statsGrid}>
      <StatCard title="Pending Review" value={statistics?.pending?.verifications || '0'} icon="🔍" />
      <StatCard title="Reports Generated" value={statistics?.today?.reports || '0'} icon="📄" />
      <StatCard title="Total Results" value={statistics?.totals?.results || '0'} icon="✅" />
    </div>
  );
}

function ManagerDashboard({ statistics }: { statistics?: DashboardStatistics }) {
  return (
    <div className={styles.statsGrid}>
      <StatCard title="Total Orders" value={statistics?.totals?.orders || '0'} icon="📋" />
      <StatCard title="Revenue Today" value={statistics?.revenue?.today ? `$${statistics.revenue.today}` : '$0'} icon="💰" />
      <StatCard title="Total Revenue" value={statistics?.revenue?.total ? `$${statistics.revenue.total}` : '$0'} icon="💵" />
    </div>
  );
}

function DefaultDashboard() {
  return (
    <div className={styles.welcomeCard}>
      <p>Welcome to the Laboratory Information Management System.</p>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: string;
}

function StatCard({ title, value, icon }: StatCardProps) {
  return (
    <div className={styles.statCard}>
      <div className={styles.statIcon}>{icon}</div>
      <div className={styles.statContent}>
        <div className={styles.statValue}>{value}</div>
        <div className={styles.statTitle}>{title}</div>
      </div>
    </div>
  );
}
