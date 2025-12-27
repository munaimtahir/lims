import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { LabWorklistPage } from './LabWorklistPage'
import { orderService } from '../../services/orders'

vi.mock('../../services/orders')

describe('LabWorklistPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the worklist page', () => {
    vi.mocked(orderService.getAll).mockResolvedValue([])

    render(
      <BrowserRouter>
        <LabWorklistPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Lab Worklist')).toBeInTheDocument()
  })

  it('displays filter controls', () => {
    vi.mocked(orderService.getAll).mockResolvedValue([])

    render(
      <BrowserRouter>
        <LabWorklistPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/From Date/i)).toBeInTheDocument()
    expect(screen.getByText(/To Date/i)).toBeInTheDocument()
    expect(screen.getAllByText(/Status/i)[0]).toBeInTheDocument()
    expect(screen.getByText(/Patient Search/i)).toBeInTheDocument()
  })

  it('shows loading state', () => {
    vi.mocked(orderService.getAll).mockImplementation(
      () => new Promise(() => {})
    )

    render(
      <BrowserRouter>
        <LabWorklistPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Loading orders...')).toBeInTheDocument()
  })

  it('displays orders in cards', async () => {
    const mockOrders = [
      {
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
      },
    ]

    vi.mocked(orderService.getAll).mockResolvedValue(mockOrders)

    render(
      <BrowserRouter>
        <LabWorklistPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('ORD-001')).toBeInTheDocument()
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Complete Blood Count')).toBeInTheDocument()
    })
  })

  it('shows empty state when no orders', async () => {
    vi.mocked(orderService.getAll).mockResolvedValue([])

    render(
      <BrowserRouter>
        <LabWorklistPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/No orders found/i)).toBeInTheDocument()
    })
  })
})
