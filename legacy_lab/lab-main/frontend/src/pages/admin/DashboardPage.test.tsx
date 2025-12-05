import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { DashboardPage } from './DashboardPage'
import { dashboardService } from '../../services/dashboard'
import type { DashboardAnalytics } from '../../types'

vi.mock('../../services/dashboard')

const mockAnalytics: DashboardAnalytics = {
  quick_tiles: {
    total_orders_today: 10,
    reports_published_today: 8,
  },
  orders_per_day: [
    { date: '2025-01-01', count: 5 },
    { date: '2025-01-02', count: 10 },
    { date: '2025-01-03', count: 7 },
  ],
  sample_status: {
    pending: 5,
    collected: 10,
    received: 15,
    rejected: 2,
  },
  result_status: {
    draft: 3,
    entered: 8,
    verified: 12,
    published: 20,
  },
  avg_tat_hours: 24.5,
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard with analytics data', async () => {
    vi.mocked(dashboardService.getAnalytics).mockResolvedValue(mockAnalytics)

    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Lab Dashboard & Analytics')).toBeInTheDocument()
    })

    // Check quick tiles
    expect(screen.getByText('Total Orders Today')).toBeInTheDocument()
    expect(screen.getByText('Reports Published Today')).toBeInTheDocument()

    // Check that analytics data is displayed
    const quickTilesSection = screen
      .getByText('Total Orders Today')
      .closest('div')
    expect(quickTilesSection).toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    vi.mocked(dashboardService.getAnalytics).mockImplementation(
      () =>
        new Promise(() => {
          // Never resolves
        })
    )

    render(<DashboardPage />)
    expect(screen.getByText('Loading analytics...')).toBeInTheDocument()
  })

  it('shows error message when data loading fails', async () => {
    const errorMessage = 'Failed to fetch analytics'
    vi.mocked(dashboardService.getAnalytics).mockRejectedValue(
      new Error(errorMessage)
    )

    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('renders empty state when no data available', async () => {
    const emptyAnalytics: DashboardAnalytics = {
      quick_tiles: {
        total_orders_today: 0,
        reports_published_today: 0,
      },
      orders_per_day: [],
      sample_status: {
        pending: 0,
        collected: 0,
        received: 0,
        rejected: 0,
      },
      result_status: {
        draft: 0,
        entered: 0,
        verified: 0,
        published: 0,
      },
      avg_tat_hours: 0,
    }

    vi.mocked(dashboardService.getAnalytics).mockResolvedValue(emptyAnalytics)

    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getAllByText('No data available').length).toBeGreaterThan(0)
    })
  })
})
