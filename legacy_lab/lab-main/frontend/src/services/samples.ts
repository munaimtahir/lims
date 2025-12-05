import { apiClient } from './api'
import { SAMPLE_ENDPOINTS } from '../utils/constants'
import type { Sample } from '../types'

/**
 * Service for handling sample-related API calls.
 */
export const sampleService = {
  /**
   * Retrieves all samples.
   * @param {Record<string, string>} [filters] - The filters to apply to the request.
   * @returns {Promise<Sample[]>} A promise that resolves with an array of samples.
   */
  async getAll(filters?: Record<string, string>): Promise<Sample[]> {
    const queryParams = filters
      ? '?' + new URLSearchParams(filters).toString()
      : ''
    const response = await apiClient.get<{ results: Sample[] }>(
      SAMPLE_ENDPOINTS.LIST + queryParams
    )
    return response.results || []
  },

  /**
   * Retrieves a sample by its ID.
   * @param {number} id - The ID of the sample.
   * @returns {Promise<Sample>} A promise that resolves with the sample.
   */
  async getById(id: number): Promise<Sample> {
    return apiClient.get<Sample>(SAMPLE_ENDPOINTS.DETAIL(id))
  },

  /**
   * Marks a sample as collected.
   * @param {number} id - The ID of the sample to collect.
   * @returns {Promise<Sample>} A promise that resolves with the updated sample.
   */
  async collect(id: number): Promise<Sample> {
    return apiClient.post<Sample>(SAMPLE_ENDPOINTS.COLLECT(id))
  },

  /**
   * Marks a sample as received.
   * @param {number} id - The ID of the sample to receive.
   * @returns {Promise<Sample>} A promise that resolves with the updated sample.
   */
  async receive(id: number): Promise<Sample> {
    return apiClient.post<Sample>(SAMPLE_ENDPOINTS.RECEIVE(id))
  },

  /**
   * Rejects a sample.
   * @param {number} id - The ID of the sample to reject.
   * @param {string} rejectionReason - The reason for rejecting the sample.
   * @returns {Promise<Sample>} A promise that resolves with the updated sample.
   */
  async reject(id: number, rejectionReason: string): Promise<Sample> {
    return apiClient.post<Sample>(SAMPLE_ENDPOINTS.REJECT(id), {
      rejection_reason: rejectionReason,
    })
  },
}
