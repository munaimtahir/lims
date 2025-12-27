import { describe, it, expect, beforeEach, vi } from 'vitest'
import { resultService } from './results'
import { apiClient } from './api'

vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}))

describe('resultService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all results', async () => {
      const mockResults = [
        {
          id: 1,
          order_item: 1,
          status: 'DRAFT',
          value: '120',
          unit: 'mg/dL',
        },
      ]
      vi.mocked(apiClient.get).mockResolvedValueOnce({ results: mockResults })

      const result = await resultService.getAll()

      expect(apiClient.get).toHaveBeenCalledWith('/results/')
      expect(result).toEqual(mockResults)
    })
  })

  describe('getById', () => {
    it('should fetch a result by id', async () => {
      const mockResult = {
        id: 1,
        order_item: 1,
        status: 'ENTERED',
        value: '120',
        unit: 'mg/dL',
      }
      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResult)

      const result = await resultService.getById(1)

      expect(apiClient.get).toHaveBeenCalledWith('/results/1/')
      expect(result).toEqual(mockResult)
    })
  })

  describe('enter', () => {
    it('should enter a result with data', async () => {
      const mockResult = {
        id: 1,
        order_item: 1,
        status: 'ENTERED',
        value: '120',
        unit: 'mg/dL',
      }
      const enterData = {
        value: '120',
        unit: 'mg/dL',
        flag: 'normal' as const,
      }
      vi.mocked(apiClient.patch).mockResolvedValueOnce(mockResult)
      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResult)

      const result = await resultService.enter(1, enterData)

      expect(apiClient.patch).toHaveBeenCalledWith('/results/1/', {
        value: '120',
        unit: 'mg/dL',
        reference_range: undefined,
        flags: 'normal',
        notes: undefined,
      })
      expect(apiClient.post).toHaveBeenCalledWith('/results/1/enter/')
      expect(result).toEqual(mockResult)
    })
  })

  describe('verify', () => {
    it('should verify a result', async () => {
      const mockResult = {
        id: 1,
        order_item: 1,
        status: 'VERIFIED',
        value: '120',
        unit: 'mg/dL',
      }
      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResult)

      const result = await resultService.verify(1)

      expect(apiClient.post).toHaveBeenCalledWith('/results/1/verify/')
      expect(result).toEqual(mockResult)
    })
  })

  describe('publish', () => {
    it('should publish a result', async () => {
      const mockResult = {
        id: 1,
        order_item: 1,
        status: 'PUBLISHED',
        value: '120',
        unit: 'mg/dL',
      }
      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResult)

      const result = await resultService.publish(1)

      expect(apiClient.post).toHaveBeenCalledWith('/results/1/publish/')
      expect(result).toEqual(mockResult)
    })
  })
})
