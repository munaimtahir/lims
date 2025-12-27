import { apiClient } from './api'
import { USER_ENDPOINTS } from '../utils/constants'
import type { User, UserFormData } from '../types'

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
 * Service for handling user-related API calls.
 */
export const userService = {
  /**
   * Retrieves all users.
   * @returns {Promise<User[]>} A promise that resolves with an array of all users.
   */
  async getAll(): Promise<User[]> {
    const response = await apiClient.get<PaginatedResponse<User>>(
      USER_ENDPOINTS.LIST
    )
    return response.results || []
  },

  /**
   * Retrieves a user by their ID.
   * @param {number} id - The ID of the user.
   * @returns {Promise<User>} A promise that resolves with the user.
   */
  async getById(id: number): Promise<User> {
    return apiClient.get<User>(USER_ENDPOINTS.DETAIL(id))
  },

  /**
   * Creates a new user.
   * @param {UserFormData} data - The data for the new user.
   * @returns {Promise<User>} A promise that resolves with the created user.
   */
  async create(data: UserFormData): Promise<User> {
    return apiClient.post<User>(USER_ENDPOINTS.LIST, data)
  },

  /**
   * Updates a user.
   * @param {number} id - The ID of the user to update.
   * @param {Partial<UserFormData>} data - The data to update the user with.
   * @returns {Promise<User>} A promise that resolves with the updated user.
   */
  async update(id: number, data: Partial<UserFormData>): Promise<User> {
    return apiClient.patch<User>(USER_ENDPOINTS.DETAIL(id), data)
  },

  /**
   * Deletes a user.
   * @param {number} id - The ID of the user to delete.
   * @returns {Promise<void>} A promise that resolves when the user is deleted.
   */
  async delete(id: number): Promise<void> {
    await apiClient.delete(USER_ENDPOINTS.DETAIL(id))
  },
}
