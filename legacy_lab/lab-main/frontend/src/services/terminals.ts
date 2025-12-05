import { apiClient } from './api'
import { TERMINAL_ENDPOINTS } from '../utils/constants'
import type { LabTerminal, LabTerminalFormData } from '../types'

/**
 * Interface for a paginated API response.
 * @template T - The type of the items in the results array.
 */
interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/**
 * Service for handling lab terminal-related API calls.
 */
export const terminalService = {
  /**
   * Retrieves all lab terminals.
   * @returns {Promise<LabTerminal[]>} A promise that resolves with an array of all lab terminals.
   */
  async getAll(): Promise<LabTerminal[]> {
    const response = await apiClient.get<PaginatedResponse<LabTerminal>>(
      TERMINAL_ENDPOINTS.LIST
    )
    return response.results || []
  },

  /**
   * Retrieves a lab terminal by its ID.
   * @param {number} id - The ID of the lab terminal.
   * @returns {Promise<LabTerminal>} A promise that resolves with the lab terminal.
   */
  async getById(id: number): Promise<LabTerminal> {
    return apiClient.get<LabTerminal>(TERMINAL_ENDPOINTS.DETAIL(id))
  },

  /**
   * Creates a new lab terminal.
   * @param {LabTerminalFormData} data - The data for the new lab terminal.
   * @returns {Promise<LabTerminal>} A promise that resolves with the created lab terminal.
   */
  async create(data: LabTerminalFormData): Promise<LabTerminal> {
    return apiClient.post<LabTerminal>(TERMINAL_ENDPOINTS.LIST, data)
  },

  /**
   * Updates a lab terminal.
   * @param {number} id - The ID of the lab terminal to update.
   * @param {Partial<LabTerminalFormData>} data - The data to update the lab terminal with.
   * @returns {Promise<LabTerminal>} A promise that resolves with the updated lab terminal.
   */
  async update(
    id: number,
    data: Partial<LabTerminalFormData>
  ): Promise<LabTerminal> {
    return apiClient.patch<LabTerminal>(TERMINAL_ENDPOINTS.DETAIL(id), data)
  },

  /**
   * Deletes a lab terminal.
   * @param {number} id - The ID of the lab terminal to delete.
   * @returns {Promise<void>} A promise that resolves when the lab terminal is deleted.
   */
  async delete(id: number): Promise<void> {
    await apiClient.delete(TERMINAL_ENDPOINTS.DETAIL(id))
  },
}
