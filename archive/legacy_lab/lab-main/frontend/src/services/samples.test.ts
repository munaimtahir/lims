import { describe, it, expect, beforeEach, vi } from 'vitest'
import { sampleService } from './samples'
import { apiClient } from './api'

vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

describe('sampleService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all samples', async () => {
      const mockSamples = [
        {
          id: 1,
          order_item: 1,
          barcode: 'SAM-20240101-0001',
          status: 'PENDING',
          sample_type: 'Blood',
        },
      ]
      vi.mocked(apiClient.get).mockResolvedValueOnce({ results: mockSamples })

      const result = await sampleService.getAll()

      expect(apiClient.get).toHaveBeenCalledWith('/samples/')
      expect(result).toEqual(mockSamples)
    })

    it('should fetch samples with filters', async () => {
      const mockSamples = [
        {
          id: 1,
          order_item: 1,
          barcode: 'SAM-20240101-0001',
          status: 'COLLECTED',
          sample_type: 'Blood',
        },
      ]
      vi.mocked(apiClient.get).mockResolvedValueOnce({ results: mockSamples })

      const result = await sampleService.getAll({ status: 'COLLECTED' })

      expect(apiClient.get).toHaveBeenCalledWith(
        '/samples/?status=COLLECTED'
      )
      expect(result).toEqual(mockSamples)
    })
  })

  describe('getById', () => {
    it('should fetch a sample by id', async () => {
      const mockSample = {
        id: 1,
        order_item: 1,
        barcode: 'SAM-20240101-0001',
        status: 'PENDING',
        sample_type: 'Blood',
      }
      vi.mocked(apiClient.get).mockResolvedValueOnce(mockSample)

      const result = await sampleService.getById(1)

      expect(apiClient.get).toHaveBeenCalledWith('/samples/1/')
      expect(result).toEqual(mockSample)
    })
  })

  describe('collect', () => {
    it('should mark sample as collected', async () => {
      const mockSample = {
        id: 1,
        order_item: 1,
        barcode: 'SAM-20240101-0001',
        status: 'COLLECTED',
        sample_type: 'Blood',
      }
      vi.mocked(apiClient.post).mockResolvedValueOnce(mockSample)

      const result = await sampleService.collect(1)

      expect(apiClient.post).toHaveBeenCalledWith('/samples/1/collect/')
      expect(result).toEqual(mockSample)
    })
  })

  describe('receive', () => {
    it('should mark sample as received', async () => {
      const mockSample = {
        id: 1,
        order_item: 1,
        barcode: 'SAM-20240101-0001',
        status: 'RECEIVED',
        sample_type: 'Blood',
      }
      vi.mocked(apiClient.post).mockResolvedValueOnce(mockSample)

      const result = await sampleService.receive(1)

      expect(apiClient.post).toHaveBeenCalledWith('/samples/1/receive/')
      expect(result).toEqual(mockSample)
    })
  })

  describe('reject', () => {
    it('should reject sample with reason', async () => {
      const mockSample = {
        id: 1,
        order_item: 1,
        barcode: 'SAM-20240101-0001',
        status: 'REJECTED',
        sample_type: 'Blood',
        rejection_reason: 'Hemolyzed sample',
      }
      vi.mocked(apiClient.post).mockResolvedValueOnce(mockSample)

      const result = await sampleService.reject(1, 'Hemolyzed sample')

      expect(apiClient.post).toHaveBeenCalledWith('/samples/1/reject/', {
        rejection_reason: 'Hemolyzed sample',
      })
      expect(result).toEqual(mockSample)
    })
  })
})
