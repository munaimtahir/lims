import { describe, it, expect, beforeEach, vi } from 'vitest'
import { reportService } from './reports'
import { apiClient } from './api'

// Mock API_BASE_URL from environment or use test default
vi.mock('./api', () => ({
  API_BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

// Store the mocked API_BASE_URL for test assertions
const TEST_API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000'

describe('reportService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all reports', async () => {
      const mockReports = [
        {
          id: 1,
          order: { id: 1, order_no: 'ORD-20240101-0001' },
          pdf_file: '/media/reports/report_1.pdf',
          generated_at: '2024-01-01T10:00:00Z',
          generated_by: { id: 1, username: 'pathologist' },
        },
      ]
      vi.mocked(apiClient.get).mockResolvedValueOnce({ results: mockReports })

      const result = await reportService.getAll()

      expect(apiClient.get).toHaveBeenCalledWith('/reports/')
      expect(result).toEqual(mockReports)
    })
  })

  describe('getById', () => {
    it('should fetch a report by id', async () => {
      const mockReport = {
        id: 1,
        order: { id: 1, order_no: 'ORD-20240101-0001' },
        pdf_file: '/media/reports/report_1.pdf',
        generated_at: '2024-01-01T10:00:00Z',
        generated_by: { id: 1, username: 'pathologist' },
      }
      vi.mocked(apiClient.get).mockResolvedValueOnce(mockReport)

      const result = await reportService.getById(1)

      expect(apiClient.get).toHaveBeenCalledWith('/reports/1/')
      expect(result).toEqual(mockReport)
    })
  })

  describe('generate', () => {
    it('should generate a report for an order', async () => {
      const mockReport = {
        id: 1,
        order: { id: 1, order_no: 'ORD-20240101-0001' },
        pdf_file: '/media/reports/report_1.pdf',
        generated_at: '2024-01-01T10:00:00Z',
        generated_by: { id: 1, username: 'pathologist' },
      }
      vi.mocked(apiClient.post).mockResolvedValueOnce(mockReport)

      const result = await reportService.generate(1)

      expect(apiClient.post).toHaveBeenCalledWith('/reports/generate/1/')
      expect(result).toEqual(mockReport)
    })
  })

  describe('getDownloadUrl', () => {
    it('should return the download URL for a report', () => {
      const url = reportService.getDownloadUrl(1)

      expect(url).toBe(`${TEST_API_BASE_URL}/reports/1/download/`)
    })
  })
})
