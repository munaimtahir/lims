import { apiClient } from './api'
import { DASHBOARD_ENDPOINTS } from '../utils/constants'
import type { DashboardAnalytics } from '../types'

/**
 * Service for handling dashboard-related API calls.
 */
export const dashboardService = {
  /**
   * Retrieves dashboard analytics.
   * @param {object} [params] - The parameters for filtering the analytics.
   * @param {string} [params.start_date] - The start date for the analytics.
   * @param {string} [params.end_date] - The end date for the analytics.
   * @returns {Promise<DashboardAnalytics>} A promise that resolves with the dashboard analytics.
   */
  async getAnalytics(params?: {
    start_date?: string
    end_date?: string
  }): Promise<DashboardAnalytics> {
    const queryParams = new URLSearchParams()
    if (params?.start_date) {
      queryParams.append('start_date', params.start_date)
    }
    if (params?.end_date) {
      queryParams.append('end_date', params.end_date)
    }

    const url =
      queryParams.toString() !== ''
        ? `${DASHBOARD_ENDPOINTS.ANALYTICS}?${queryParams.toString()}`
        : DASHBOARD_ENDPOINTS.ANALYTICS

    return apiClient.get<DashboardAnalytics>(url)
  },
}
