import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { BrandingProvider } from './contexts/BrandingContext';
import { ProtectedRoute } from './components/auth';
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
import ReferenceRangesPage from './pages/reference-ranges';
import SystemSettingsPage from './pages/settings';
import RegistrationPage from './pages/registration';
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
                <Route path="orders" element={<Navigate to="/dashboard/patients" replace />} />
                <Route path="tests" element={<TestCatalogPage />} />
                <Route path="samples" element={<SamplesPage />} />
                <Route path="collection" element={<CollectionWorklistPage />} />
                <Route path="results" element={<ResultsPage />} />
                <Route path="worklist" element={<ResultEntryWorklistPage />} />
                <Route path="verification" element={<VerificationQueuePage />} />
                <Route path="review" element={<Navigate to="/dashboard/verification" replace />} />
                <Route path="reports" element={<ReportsPage />} />
                <Route path="payments" element={<PaymentsPage />} />
                <Route path="audit" element={<AuditLogsPage />} />

                {/* Settings pages */}
                <Route path="reference-ranges" element={<ReferenceRangesPage />} />
                <Route path="settings" element={<SystemSettingsPage />} />
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
