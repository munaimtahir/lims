import { apiClient } from './api'
import { ORDER_ENDPOINTS } from '../utils/constants'
import type { Order } from '../types'

/**
 * Interface for the data required to create an order.
 */
interface CreateOrderData {
  patient: number
  test_ids: number[]
  priority?: 'ROUTINE' | 'URGENT' | 'STAT'
  notes?: string
}

/**
 * Interface for the data required to edit the tests in an order.
 */
interface EditOrderTestsData {
  tests_to_add?: number[]
  tests_to_remove?: number[]
}

/**
 * Service for handling order-related API calls.
 */
export const orderService = {
  /**
   * Retrieves all orders.
   * @param {Record<string, string>} [filters] - The filters to apply to the request.
   * @returns {Promise<Order[]>} A promise that resolves with an array of orders.
   */
  async getAll(filters?: Record<string, string>): Promise<Order[]> {
    const queryParams = filters
      ? '?' + new URLSearchParams(filters).toString()
      : ''
    const response = await apiClient.get<{ results: Order[] }>(
      ORDER_ENDPOINTS.LIST + queryParams
    )
    return response.results || []
  },

  /**
   * Retrieves an order by its ID.
   * @param {number} id - The ID of the order.
   * @returns {Promise<Order>} A promise that resolves with the order.
   */
  async getById(id: number): Promise<Order> {
    return apiClient.get<Order>(ORDER_ENDPOINTS.DETAIL(id))
  },

  /**
   * Creates a new order.
   * @param {CreateOrderData} data - The data for the new order.
   * @returns {Promise<Order>} A promise that resolves with the created order.
   */
  async create(data: CreateOrderData): Promise<Order> {
    return apiClient.post<Order>(ORDER_ENDPOINTS.LIST, data)
  },

  /**
   * Cancels an order.
   * @param {number} id - The ID of the order to cancel.
   * @returns {Promise<Order>} A promise that resolves with the cancelled order.
   */
  async cancel(id: number): Promise<Order> {
    return apiClient.post<Order>(ORDER_ENDPOINTS.CANCEL(id))
  },

  /**
   * Edits the tests in an order.
   * @param {number} id - The ID of the order to edit.
   * @param {EditOrderTestsData} data - The data for editing the tests.
   * @returns {Promise<Order>} A promise that resolves with the updated order.
   */
  async editTests(id: number, data: EditOrderTestsData): Promise<Order> {
    return apiClient.patch<Order>(ORDER_ENDPOINTS.EDIT_TESTS(id), data)
  },
}
