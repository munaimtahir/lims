import apiClient from '../client';
import type { PaginatedResponse, TestResult, WorklistOrderItem } from '../../types';

export const resultApi = {
  getById: (id: number) => apiClient.get<TestResult>(`/results/${id}`),
  getByOrderItem: (orderItemId: number) => apiClient.post<{ results: TestResult[] }>('/results/ensure/', { order_item_id: orderItemId }),
  getWorklist: () => apiClient.get<PaginatedResponse<WorklistOrderItem>>('/results/worklist'),
  ensure: (orderItemId: number) => apiClient.post(`/results/ensure?order_item_id=${orderItemId}`),
  bulkEntry: (data: Partial<TestResult>[]) => apiClient.post('/results/bulk_entry', { results: data }),
  bulkVerify: (resultIds: number[]) => apiClient.post('/results/bulk-verify/', { result_ids: resultIds }),
};
