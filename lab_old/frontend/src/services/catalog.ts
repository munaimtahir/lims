import { apiClient } from './api'
import { CATALOG_ENDPOINTS } from '../utils/constants'
import type { TestCatalog, TestCatalogFormData } from '../types'

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
 * Service for handling test catalog-related API calls.
 */
export const catalogService = {
  /**
   * Searches the test catalog.
   * @param {string} query - The search query.
   * @returns {Promise<TestCatalog[]>} A promise that resolves with an array of test catalog items.
   */
  async search(query: string): Promise<TestCatalog[]> {
    const response = await apiClient.get<{ results: TestCatalog[] }>(
      `${CATALOG_ENDPOINTS.LIST}?search=${encodeURIComponent(query)}`
    )
    return response.results || []
  },

  /**
   * Retrieves all test catalog items.
   * @returns {Promise<TestCatalog[]>} A promise that resolves with an array of all test catalog items.
   */
  async getAll(): Promise<TestCatalog[]> {
    const response = await apiClient.get<PaginatedResponse<TestCatalog>>(
      CATALOG_ENDPOINTS.LIST
    )
    return response.results || []
  },

  /**
   * Retrieves a test catalog item by its ID.
   * @param {number} id - The ID of the test catalog item.
   * @returns {Promise<TestCatalog>} A promise that resolves with the test catalog item.
   */
  async getById(id: number): Promise<TestCatalog> {
    return apiClient.get<TestCatalog>(CATALOG_ENDPOINTS.DETAIL(id))
  },

  /**
   * Creates a new test catalog item.
   * @param {TestCatalogFormData} data - The data for the new test catalog item.
   * @returns {Promise<TestCatalog>} A promise that resolves with the created test catalog item.
   */
  async create(data: TestCatalogFormData): Promise<TestCatalog> {
    return apiClient.post<TestCatalog>(CATALOG_ENDPOINTS.LIST, data)
  },

  /**
   * Updates a test catalog item.
   * @param {number} id - The ID of the test catalog item to update.
   * @param {Partial<TestCatalogFormData>} data - The data to update the test catalog item with.
   * @returns {Promise<TestCatalog>} A promise that resolves with the updated test catalog item.
   */
  async update(
    id: number,
    data: Partial<TestCatalogFormData>
  ): Promise<TestCatalog> {
    return apiClient.patch<TestCatalog>(CATALOG_ENDPOINTS.DETAIL(id), data)
  },

  /**
   * Deletes a test catalog item.
   * @param {number} id - The ID of the test catalog item to delete.
   * @returns {Promise<void>} A promise that resolves when the test catalog item is deleted.
   */
  async delete(id: number): Promise<void> {
    await apiClient.delete(CATALOG_ENDPOINTS.DETAIL(id))
  },
}
