import { apiClient } from './api'
import type {
  LIMSTest,
  LIMSTestFormData,
  Parameter,
  ParameterFormData,
  ReferenceRange,
  ReferenceRangeFormData,
  TestParameter,
  TestParameterFormData,
} from '../types'

/**
 * Interface for a paginated API response.
 */
interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

const BASE_URL = '/catalog'

/**
 * Service for handling LIMS Test-related API calls.
 */
export const limsTestService = {
  async getAll(active?: boolean): Promise<LIMSTest[]> {
    const params = active !== undefined ? `?active=${active}` : ''
    const response = await apiClient.get<PaginatedResponse<LIMSTest>>(
      `${BASE_URL}/tests/${params}`
    )
    return response.results || []
  },

  async getById(id: number): Promise<LIMSTest> {
    return apiClient.get<LIMSTest>(`${BASE_URL}/tests/${id}/`)
  },

  async create(data: LIMSTestFormData): Promise<LIMSTest> {
    return apiClient.post<LIMSTest>(`${BASE_URL}/tests/`, data)
  },

  async update(id: number, data: Partial<LIMSTestFormData>): Promise<LIMSTest> {
    return apiClient.patch<LIMSTest>(`${BASE_URL}/tests/${id}/`, data)
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/tests/${id}/`)
  },
}

/**
 * Service for handling Parameter-related API calls.
 */
export const parameterService = {
  async getAll(active?: boolean): Promise<Parameter[]> {
    const params = active !== undefined ? `?active=${active}` : ''
    const response = await apiClient.get<PaginatedResponse<Parameter>>(
      `${BASE_URL}/parameters/${params}`
    )
    return response.results || []
  },

  async getById(id: number): Promise<Parameter> {
    return apiClient.get<Parameter>(`${BASE_URL}/parameters/${id}/`)
  },

  async create(data: ParameterFormData): Promise<Parameter> {
    return apiClient.post<Parameter>(`${BASE_URL}/parameters/`, data)
  },

  async update(
    id: number,
    data: Partial<ParameterFormData>
  ): Promise<Parameter> {
    return apiClient.patch<Parameter>(`${BASE_URL}/parameters/${id}/`, data)
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/parameters/${id}/`)
  },
}

/**
 * Service for handling TestParameter relationship API calls.
 */
export const testParameterService = {
  async getAll(testId?: number): Promise<TestParameter[]> {
    const params = testId ? `?test=${testId}` : ''
    const response = await apiClient.get<PaginatedResponse<TestParameter>>(
      `${BASE_URL}/test-parameters/${params}`
    )
    return response.results || []
  },

  async getById(id: number): Promise<TestParameter> {
    return apiClient.get<TestParameter>(`${BASE_URL}/test-parameters/${id}/`)
  },

  async create(data: TestParameterFormData): Promise<TestParameter> {
    return apiClient.post<TestParameter>(`${BASE_URL}/test-parameters/`, data)
  },

  async update(
    id: number,
    data: Partial<TestParameterFormData>
  ): Promise<TestParameter> {
    return apiClient.patch<TestParameter>(
      `${BASE_URL}/test-parameters/${id}/`,
      data
    )
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/test-parameters/${id}/`)
  },
}

/**
 * Service for handling ReferenceRange API calls.
 */
export const referenceRangeService = {
  async getAll(parameterId?: number): Promise<ReferenceRange[]> {
    const params = parameterId ? `?parameter=${parameterId}` : ''
    const response = await apiClient.get<PaginatedResponse<ReferenceRange>>(
      `${BASE_URL}/reference-ranges/${params}`
    )
    return response.results || []
  },

  async getById(id: number): Promise<ReferenceRange> {
    return apiClient.get<ReferenceRange>(
      `${BASE_URL}/reference-ranges/${id}/`
    )
  },

  async create(data: ReferenceRangeFormData): Promise<ReferenceRange> {
    return apiClient.post<ReferenceRange>(
      `${BASE_URL}/reference-ranges/`,
      data
    )
  },

  async update(
    id: number,
    data: Partial<ReferenceRangeFormData>
  ): Promise<ReferenceRange> {
    return apiClient.patch<ReferenceRange>(
      `${BASE_URL}/reference-ranges/${id}/`,
      data
    )
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/reference-ranges/${id}/`)
  },
}
