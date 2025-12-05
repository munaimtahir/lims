import { apiClient } from './api'
import { RESULT_ENDPOINTS } from '../utils/constants'
import type { Result } from '../types'

/**
 * Interface for the data required to enter a result.
 */
interface EnterResultData {
  value: string
  unit?: string
  reference_range?: string
  flag?: 'normal' | 'high' | 'low' | 'abnormal'
  notes?: string
}

/**
 * Service for handling result-related API calls.
 */
export const resultService = {
  /**
   * Retrieves all results.
   * @param {Record<string, string>} [filters] - The filters to apply to the request.
   * @returns {Promise<Result[]>} A promise that resolves with an array of results.
   */
  async getAll(filters?: Record<string, string>): Promise<Result[]> {
    const queryParams = filters
      ? '?' + new URLSearchParams(filters).toString()
      : ''
    const response = await apiClient.get<{ results: Result[] }>(
      RESULT_ENDPOINTS.LIST + queryParams
    )
    return response.results || []
  },

  /**
   * Retrieves a result by its ID.
   * @param {number} id - The ID of the result.
   * @returns {Promise<Result>} A promise that resolves with the result.
   */
  async getById(id: number): Promise<Result> {
    return apiClient.get<Result>(RESULT_ENDPOINTS.DETAIL(id))
  },

  /**
   * Updates a result.
   * @param {number} id - The ID of the result to update.
   * @param {Partial<Result>} data - The data to update.
   * @returns {Promise<Result>} A promise that resolves with the updated result.
   */
  async update(id: number, data: Partial<Result>): Promise<Result> {
    return apiClient.patch<Result>(RESULT_ENDPOINTS.DETAIL(id), data)
  },

  /**
   * Enters a result.
   * @param {number} id - The ID of the result to enter.
   * @param {EnterResultData} data - The data for the result (optional).
   * @returns {Promise<Result>} A promise that resolves with the entered result.
   */
  async enter(id: number, data?: EnterResultData): Promise<Result> {
    if (data) {
      await apiClient.patch<Result>(RESULT_ENDPOINTS.DETAIL(id), {
        value: data.value,
        unit: data.unit,
        reference_range: data.reference_range,
        flags: data.flag,
        notes: data.notes,
      })
    }
    return apiClient.post<Result>(RESULT_ENDPOINTS.ENTER(id))
  },

  /**
   * Verifies a result.
   * @param {number} id - The ID of the result to verify.
   * @returns {Promise<Result>} A promise that resolves with the verified result.
   */
  async verify(id: number): Promise<Result> {
    return apiClient.post<Result>(RESULT_ENDPOINTS.VERIFY(id))
  },

  /**
   * Publishes a result.
   * @param {number} id - The ID of the result to publish.
   * @returns {Promise<Result>} A promise that resolves with the published result.
   */
  async publish(id: number): Promise<Result> {
    return apiClient.post<Result>(RESULT_ENDPOINTS.PUBLISH(id))
  },
}
