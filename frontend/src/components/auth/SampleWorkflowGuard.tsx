import { Navigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { tenantSettingsApi } from '../../api/services';

/**
 * When tenant setting sample_workflow_enabled is false, redirects to dashboard
 * with a message. Use this to wrap routes for Sample Collection / Sample Receiving.
 */
export default function SampleWorkflowGuard({ children }: { children: React.ReactNode }) {
  const { data: tenantSettings, isLoading } = useQuery({
    queryKey: ['tenant-settings'],
    queryFn: () => tenantSettingsApi.get(),
    staleTime: 1000 * 60 * 5,
  });

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '200px',
        fontSize: '1rem',
        color: '#64748b',
      }}>
        Loading...
      </div>
    );
  }

  const sampleWorkflowEnabled = tenantSettings?.sample_workflow_enabled ?? true;
  if (!sampleWorkflowEnabled) {
    return (
      <Navigate
        to="/dashboard"
        replace
        state={{ message: 'Module disabled by lab settings.' }}
      />
    );
  }

  return <>{children}</>;
}
