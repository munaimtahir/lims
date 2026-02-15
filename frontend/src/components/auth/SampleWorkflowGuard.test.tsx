import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import SampleWorkflowGuard from './SampleWorkflowGuard';
import { tenantSettingsApi } from '../../api/services';

vi.mock('../../api/services', () => ({
  tenantSettingsApi: {
    get: vi.fn(),
  },
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

function wrap(children: React.ReactNode) {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('SampleWorkflowGuard', () => {
  beforeEach(() => {
    vi.mocked(tenantSettingsApi.get).mockResolvedValue({ sample_workflow_enabled: true } as any);
  });

  it('renders children when sample_workflow_enabled is true', async () => {
    render(
      wrap(
        <SampleWorkflowGuard>
          <div>Sample content</div>
        </SampleWorkflowGuard>
      )
    );
    const content = await screen.findByText('Sample content', {}, { timeout: 3000 });
    expect(content).toBeInTheDocument();
  });

  it('redirects when sample_workflow_enabled is false', async () => {
    vi.mocked(tenantSettingsApi.get).mockResolvedValue({ sample_workflow_enabled: false } as any);
    render(
      wrap(
        <SampleWorkflowGuard>
          <div>Sample content</div>
        </SampleWorkflowGuard>
      )
    );
    await screen.findByText(/loading/i, {}, { timeout: 1000 }).catch(() => null);
    await new Promise((r) => setTimeout(r, 100));
    expect(screen.queryByText('Sample content')).toBeNull();
  });
});
