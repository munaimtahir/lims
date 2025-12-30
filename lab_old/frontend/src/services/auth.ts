import { apiClient } from './api'
import { AUTH_ENDPOINTS, STORAGE_KEYS } from '../utils/constants'
import type { LoginResponse, User } from '../types'

/**
 * Service for handling authentication-related API calls.
 */
export const authService = {
  /**
   * Logs in a user.
   * @param {string} username - The user's username.
   * @param {string} password - The user's password.
   * @returns {Promise<LoginResponse>} A promise that resolves with the login response data.
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>(AUTH_ENDPOINTS.LOGIN, {
      username,
      password,
    })

    apiClient.setTokens(response.access, response.refresh)
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(response.user))

    return response
  },

  /**
   * Logs out the current user.
   * @returns {Promise<void>} A promise that resolves when the user is logged out.
   */
  async logout(): Promise<void> {
    const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)

    try {
      if (refreshToken) {
        await apiClient.post(AUTH_ENDPOINTS.LOGOUT, { refresh: refreshToken })
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      apiClient.clearTokens()
    }
  },

  /**
   * Retrieves the current user from local storage.
   * @returns {User | null} The current user, or null if not found.
   */
  getCurrentUser(): User | null {
    const userStr = localStorage.getItem(STORAGE_KEYS.USER)
    if (!userStr) return null

    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  },

  /**
   * Checks if the user is authenticated.
   * @returns {boolean} True if the user is authenticated, false otherwise.
   */
  isAuthenticated(): boolean {
    return !!apiClient.getAccessToken()
  },
}
