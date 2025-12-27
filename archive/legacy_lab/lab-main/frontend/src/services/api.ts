import { API_BASE_URL, STORAGE_KEYS } from '../utils/constants'

export { API_BASE_URL }

/**
 * Custom error class for API-related errors.
 * @param {string} message - The error message.
 * @param {number} [status] - The HTTP status code of the response.
 * @param {unknown} [data] - The response data.
 */
export class ApiError extends Error {
  status?: number
  data?: unknown

  constructor(message: string, status?: number, data?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

/**
 * A client for interacting with the API.
 * Handles token storage, token refreshing, and request signing.
 */
class ApiClient {
  private baseURL: string
  private accessToken: string | null = null
  private refreshToken: string | null = null

  /**
   * @param {string} baseURL - The base URL of the API.
   */
  constructor(baseURL: string) {
    this.baseURL = baseURL
    this.loadTokens()
  }

  /**
   * Loads access and refresh tokens from local storage.
   */
  private loadTokens() {
    this.accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
    this.refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)
  }

  /**
   * Sets and stores the access and refresh tokens.
   * @param {string} access - The access token.
   * @param {string} refresh - The refresh token.
   */
  public setTokens(access: string, refresh: string) {
    this.accessToken = access
    this.refreshToken = refresh
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, access)
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refresh)
  }

  /**
   * Clears the stored tokens and user data.
   */
  public clearTokens() {
    this.accessToken = null
    this.refreshToken = null
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER)
  }

  /**
   * Returns the current access token.
   * @returns {string | null} The access token, or null if not set.
   */
  public getAccessToken() {
    return this.accessToken
  }

  /**
   * Refreshes the access token using the refresh token.
   * @returns {Promise<string>} A promise that resolves with the new access token.
   */
  private async refreshAccessToken(): Promise<string> {
    if (!this.refreshToken) {
      throw new ApiError('No refresh token available', 401)
    }

    const response = await fetch(`${this.baseURL}/auth/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: this.refreshToken }),
    })

    if (!response.ok) {
      this.clearTokens()
      throw new ApiError('Failed to refresh token', response.status)
    }

    const data = await response.json()
    this.accessToken = data.access
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access)
    return data.access
  }

  /**
   * Makes a request to the API.
   * Handles token refreshing and retries on 401 errors.
   * @param {string} path - The path of the API endpoint.
   * @param {RequestInit} [options] - The request options.
   * @returns {Promise<T>} A promise that resolves with the response data.
   */
  public async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${path}`
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    }

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`
    }

    let response = await fetch(url, {
      ...options,
      headers,
    })

    if (
      response.status === 401 &&
      this.refreshToken &&
      !path.includes('/auth/')
    ) {
      try {
        await this.refreshAccessToken()
        headers['Authorization'] = `Bearer ${this.accessToken}`
        response = await fetch(url, {
          ...options,
          headers,
        })
      } catch {
        this.clearTokens()
        throw new ApiError('Authentication failed', 401)
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(
        errorData.message || `Request failed with status ${response.status}`,
        response.status,
        errorData
      )
    }

    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      return response.json()
    }

    return {} as T
  }

  /**
   * Makes a GET request to the API.
   * @param {string} path - The path of the API endpoint.
   * @param {RequestInit} [options] - The request options.
   * @returns {Promise<T>} A promise that resolves with the response data.
   */
  public async get<T>(path: string, options?: RequestInit): Promise<T> {
    return this.request<T>(path, { ...options, method: 'GET' })
  }

  /**
   * Makes a POST request to the API.
   * @param {string} path - The path of the API endpoint.
   * @param {unknown} [data] - The request data.
   * @param {RequestInit} [options] - The request options.
   * @returns {Promise<T>} A promise that resolves with the response data.
   */
  public async post<T>(
    path: string,
    data?: unknown,
    options?: RequestInit
  ): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * Makes a PUT request to the API.
   * @param {string} path - The path of the API endpoint.
   * @param {unknown} [data] - The request data.
   * @param {RequestInit} [options] - The request options.
   * @returns {Promise<T>} A promise that resolves with the response data.
   */
  public async put<T>(
    path: string,
    data?: unknown,
    options?: RequestInit
  ): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * Makes a PATCH request to the API.
   * @param {string} path - The path of the API endpoint.
   * @param {unknown} [data] - The request data.
   * @param {RequestInit} [options] - The request options.
   * @returns {Promise<T>} A promise that resolves with the response data.
   */
  public async patch<T>(
    path: string,
    data?: unknown,
    options?: RequestInit
  ): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * Makes a DELETE request to the API.
   * @param {string} path - The path of the API endpoint.
   * @param {RequestInit} [options] - The request options.
   * @returns {Promise<T>} A promise that resolves with the response data.
   */
  public async delete<T>(path: string, options?: RequestInit): Promise<T> {
    return this.request<T>(path, { ...options, method: 'DELETE' })
  }
}

export const apiClient = new ApiClient(API_BASE_URL)
