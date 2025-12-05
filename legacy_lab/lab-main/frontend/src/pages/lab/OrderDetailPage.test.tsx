import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { OrderDetailPage } from './OrderDetailPage'
import { orderService } from '../../services/orders'
import { sampleService } from '../../services/samples'
import { resultService } from '../../services/results'
import { reportService } from '../../services/reports'
import { AuthProvider } from '../../hooks/useAuth'

vi.mock('../../services/orders')
vi.mock('../../services/samples')
vi.mock('../../services/results')
vi.mock('../../services/reports')
vi.mock('../../services/auth', () => ({
  authService: {
    getCurrentUser: () => ({ id: 1, username: 'admin', role: 'ADMIN' }),
    isAuthenticated: () => true,
  },
}))

const mockOrder = {
  id: 1,
  order_no: 'ORD-001',
  patient: {
    id: 1,
    mrn: 'PAT-001',
    full_name: 'John Doe',
    sex: 'M' as const,
    age_years: 30,
    age_months: null,
    age_days: null,
    cnic: '12345-1234567-1',
    phone: '03001234567',
    dob: '1994-01-01',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  items: [
    {
      id: 1,
      test: {
        id: 1,
        code: 'CBC',
        name: 'Complete Blood Count',
        description: '',
        category: 'Hematology',
        sample_type: 'Blood',
        price: 500,
        turnaround_time_hours: 24,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      status: 'NEW' as const,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ],
  priority: 'ROUTINE' as const,
  status: 'NEW' as const,
  notes: '',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('OrderDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(orderService.getById).mockResolvedValue(mockOrder)
    vi.mocked(sampleService.getAll).mockResolvedValue([])
    vi.mocked(resultService.getAll).mockResolvedValue([])
    vi.mocked(reportService.getAll).mockResolvedValue([])
  })

  it('shows loading state', () => {
    vi.mocked(orderService.getById).mockImplementation(
      () => new Promise(() => {})
    )

    render(
      <MemoryRouter initialEntries={['/lab/orders/1']}>
        <AuthProvider>
          <Routes>
            <Route path="/lab/orders/:id" element={<OrderDetailPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByText('Loading order...')).toBeInTheDocument()
  })

  it('renders page with tabs', async () => {
    render(
      <MemoryRouter initialEntries={['/lab/orders/1']}>
        <AuthProvider>
          <Routes>
            <Route path="/lab/orders/:id" element={<OrderDetailPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(
      () => {
        expect(
          screen.getByRole('button', { name: 'Summary' })
        ).toBeInTheDocument()
      },
      { timeout: 5000 }
    )
  })
})
