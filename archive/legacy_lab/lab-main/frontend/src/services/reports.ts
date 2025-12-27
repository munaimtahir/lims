import { apiClient, API_BASE_URL } from './api'
import { REPORT_ENDPOINTS } from '../utils/constants'
import type { Report } from '../types'

/**
 * Service for handling report-related API calls.
 */
export const reportService = {
  /**
   * Retrieves all reports.
   * @returns {Promise<Report[]>} A promise that resolves with an array of all reports.
   */
  async getAll(): Promise<Report[]> {
    const response = await apiClient.get<{ results: Report[] }>(
      REPORT_ENDPOINTS.LIST
    )
    return response.results || []
  },

  /**
   * Retrieves a report by its ID.
   * @param {number} id - The ID of the report.
   * @returns {Promise<Report>} A promise that resolves with the report.
   */
  async getById(id: number): Promise<Report> {
    return apiClient.get<Report>(REPORT_ENDPOINTS.DETAIL(id))
  },

  /**
   * Generates a report for an order.
   * @param {number} orderId - The ID of the order to generate a report for.
   * @returns {Promise<Report>} A promise that resolves with the generated report.
   */
  async generate(orderId: number): Promise<Report> {
    return apiClient.post<Report>(REPORT_ENDPOINTS.GENERATE(orderId))
  },

  /**
   * Returns the download URL for a report.
   * @param {number} id - The ID of the report.
   * @returns {string} The download URL for the report.
   */
  getDownloadUrl(id: number): string {
    return `${API_BASE_URL}${REPORT_ENDPOINTS.DOWNLOAD(id)}`
  },
}
