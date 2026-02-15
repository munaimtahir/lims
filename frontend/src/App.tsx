import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { BrandingProvider } from './contexts/BrandingContext';
import { ProtectedRoute, SampleWorkflowGuard } from './components/auth';
import { DashboardLayout } from './components/dashboard';
import { LoginPage } from './pages/auth';
import { PrintReceiptPage } from './pages/print';
import { DashboardHome } from './pages/dashboard';
import { PatientsPage } from './pages/patients';
import { PatientsWorklistPage } from './pages/patient-worklist';
import { TestCatalogPage } from './pages/tests';
import { SamplesPage } from './pages/samples';
import { CollectionWorklistPage } from './pages/collection';
import { ResultsPage } from './pages/results';
import { ResultEntryWorklistPage } from './pages/worklist';
import { VerificationQueuePage } from './pages/review';
import { ReportsPage } from './pages/reports';
import { PaymentsPage } from './pages/payments';
import { AuditLogsPage } from './pages/audit';
import { BackupsPage } from './pages/backups';

import ReferenceRangesPage from './pages/reference-ranges';
import SystemSettingsPage from './pages/settings';
import RegistrationPage from './pages/registration';
import { BranchesAndCentersPage } from './pages/branches-and-centers';
import { OrdersPage, CreateOrderPage } from './pages/orders';
import {
  AnalyticsOverviewPage,
  AnalyticsPatientsPage,
  AnalyticsTestsPage,
  AnalyticsReferralsPage,
  AnalyticsFinancePage,
  AnalyticsExportLogsPage
} from './pages/analytics';
import './App.css';


// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrandingProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />
              {/* Print Routes */}
              <Route
                path="/print/receipt/:orderId"
                element={
                  <ProtectedRoute>
                    <PrintReceiptPage />
                  </ProtectedRoute>
                }
              />

              {/* Protected routes */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<DashboardHome />} />

                {/* Implemented pages */}
                <Route path="registration" element={<RegistrationPage />} />
                <Route path="patients" element={<PatientsPage />} />
                <Route path="patients-worklist" element={<PatientsWorklistPage />} />
                <Route path="orders" element={<OrdersPage />} />
                <Route path="orders/create" element={<CreateOrderPage />} />
                <Route path="tests" element={<TestCatalogPage />} />
                <Route path="samples" element={<SampleWorkflowGuard><SamplesPage /></SampleWorkflowGuard>} />
                <Route path="collection" element={<SampleWorkflowGuard><CollectionWorklistPage /></SampleWorkflowGuard>} />
                <Route path="results" element={<ResultsPage />} />
                <Route path="worklist" element={<ResultEntryWorklistPage />} />
                <Route path="verification" element={<VerificationQueuePage />} />
                <Route path="review" element={<Navigate to="/dashboard/verification" replace />} />
                <Route path="reports" element={<ReportsPage />} />
                <Route path="payments" element={<PaymentsPage />} />
                <Route path="audit" element={<AuditLogsPage />} />
                <Route
                  path="backups"
                  element={
                    <ProtectedRoute allowedRoles={['Admin', 'Manager', 'Pathologist']}>
                      <BackupsPage />
                    </ProtectedRoute>
                  }
                />


                {/* Analytics */}
                <Route path="analytics" element={<AnalyticsOverviewPage />} />
                <Route path="analytics/patients" element={<AnalyticsPatientsPage />} />
                <Route path="analytics/tests" element={<AnalyticsTestsPage />} />
                <Route path="analytics/referrals" element={<AnalyticsReferralsPage />} />
                <Route path="analytics/finance" element={<AnalyticsFinancePage />} />
                <Route path="analytics/export-logs" element={<AnalyticsExportLogsPage />} />

                {/* Settings pages */}
                <Route path="reference-ranges" element={<ReferenceRangesPage />} />
                <Route path="settings" element={<SystemSettingsPage />} />
                <Route
                  path="branches-and-centers"
                  element={
                    <ProtectedRoute allowedRoles={['Admin', 'Manager']}>
                      <BranchesAndCentersPage />
                    </ProtectedRoute>
                  }
                />
              </Route>


              {/* Default redirect */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </BrandingProvider>
    </QueryClientProvider>
  );
}

export default App;
