import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { HomePage } from './HomePage'

// Mock the dashboard service
vi.mock('../../services/dashboard', () => ({
  dashboardService: {
    getAnalytics: vi.fn().mockResolvedValue({
      quick_tiles: {
        total_orders_today: 10,
        reports_published_today: 5,
      },
      orders_per_day: [],
      sample_status: {
        pending: 3,
        collected: 2,
        received: 4,
        rejected: 1,
      },
      result_status: {
        draft: 2,
        entered: 3,
        verified: 1,
        published: 5,
      },
      avg_tat_hours: 4.5,
    }),
  },
}))

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard title', async () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    expect(screen.getByText('Lab Dashboard')).toBeInTheDocument()
  })

  it('displays quick stats cards', async () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    // Wait for analytics to load
    await waitFor(() => {
      expect(screen.getByText("Today's Orders")).toBeInTheDocument()
    })

    expect(screen.getByText('Pending Phlebotomy')).toBeInTheDocument()
    expect(screen.getByText('Pending Result Entry')).toBeInTheDocument()
    expect(screen.getByText('Pending Verification')).toBeInTheDocument()
  })

  it('displays quick actions section', async () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    expect(screen.getByText('Quick Actions')).toBeInTheDocument()
  })

  it('displays analytics data after loading', async () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument() // total_orders_today
    })
  })
})
