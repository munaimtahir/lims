import api from './client';
import type {
  Patient,
  PatientCreateRequest,
  LabTest,
  TestPanel,
  TestCategory,
  Order,
  OrderCreateRequest,
  SampleCollection,
  TestResult,
  Payment,
  Report,
  ApiResponse,
  PaginatedResponse,
  ReferenceRange,
  ReferenceRangeCreateRequest,
  SystemSettings,
  LabTerminal,
  LabTerminalCreateRequest,
  Notification,
  TestParameter,
} from '../types';

/**
 * Patient API service
 */
export const patientApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<Patient>>('/patients/', { params });
    return response.data;
  },

  get: async (id: number): Promise<ApiResponse<Patient>> => {
    const response = await api.get<ApiResponse<Patient>>(`/patients/${id}/`);
    return response.data;
  },

  create: async (data: PatientCreateRequest): Promise<ApiResponse<Patient>> => {
    const response = await api.post<ApiResponse<Patient>>('/patients/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<PatientCreateRequest>): Promise<ApiResponse<Patient>> => {
    const response = await api.patch<ApiResponse<Patient>>(`/patients/${id}/`, data);
    return response.data;
  },

  history: async (id: number) => {
    const response = await api.get(`/patients/${id}/history/`);
    return response.data;
  },

  search: async (query: string) => {
    const response = await api.get<PaginatedResponse<Patient>>('/patients/', {
      params: { search: query },
    });
    return response.data;
  },
};

/**
 * Laboratory (Test Catalog) API service
 */
export const laboratoryApi = {
  // Categories
  getCategories: async () => {
    const response = await api.get<PaginatedResponse<TestCategory>>('/laboratory/categories/');
    return response.data;
  },

  // Tests
  getTests: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<LabTest>>('/laboratory/tests/', { params });
    return response.data;
  },

  getTest: async (id: number) => {
    const response = await api.get<LabTest>(`/laboratory/tests/${id}/`);
    return response.data;
  },

  // Panels
  getPanels: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<TestPanel>>('/laboratory/panels/', { params });
    return response.data;
  },

  getPanel: async (id: number) => {
    const response = await api.get<TestPanel>(`/laboratory/panels/${id}/`);
    return response.data;
  },

  // Parameters
  getParameters: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<TestParameter>>('/laboratory/parameters/', { params });
    return response.data;
  },
};

/**
 * Order API service
 */
export const orderApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<Order>>('/orders/orders/', { params });
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get<Order>(`/orders/orders/${id}/`);
    return response.data;
  },

  create: async (data: OrderCreateRequest) => {
    const response = await api.post<Order>('/orders/orders/', data);
    return response.data;
  },

  cancel: async (id: number) => {
    const response = await api.post(`/orders/orders/${id}/cancel/`);
    return response.data;
  },

  getByStatus: async (status: string) => {
    const response = await api.get<PaginatedResponse<Order>>('/orders/orders/', {
      params: { status },
    });
    return response.data;
  },
};

/**
 * Sample Collection API service
 */
export const sampleApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<SampleCollection>>('/samples/', { params });
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get<SampleCollection>(`/samples/${id}/`);
    return response.data;
  },

  create: async (data: Partial<SampleCollection>) => {
    const response = await api.post<SampleCollection>('/samples/', data);
    return response.data;
  },

  updateStatus: async (id: number, status: string, barcode?: string) => {
    const response = await api.patch<SampleCollection>(`/samples/${id}/`, {
      status,
      ...(barcode && { barcode }),
    });
    return response.data;
  },

  getCollectionWorklist: async () => {
    const response = await api.get<PaginatedResponse<SampleCollection>>('/samples/pending_collections/');
    return response.data;
  },
};

/**
 * Results API service
 */
export const resultApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<TestResult>>('/results/', { params });
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get<TestResult>(`/results/${id}/`);
    return response.data;
  },

  create: async (data: Partial<TestResult>) => {
    const response = await api.post<TestResult>('/results/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<TestResult>) => {
    const response = await api.patch<TestResult>(`/results/${id}/`, data);
    return response.data;
  },

  verify: async (id: number) => {
    const response = await api.post(`/results/${id}/verify/`);
    return response.data;
  },

  reject: async (id: number, reason?: string) => {
    const response = await api.post(`/results/${id}/reject/`, reason ? { reason } : {});
    return response.data;
  },

  getByOrderItem: async (orderItemId: number) => {
    const response = await api.get<PaginatedResponse<TestResult>>('/results/', {
      params: { order_item: orderItemId },
    });
    return response.data;
  },

  getWorklist: async () => {
    const response = await api.get('/results/worklist/');
    return response.data;
  },

  getVerificationQueue: async () => {
    const response = await api.get<PaginatedResponse<TestResult>>('/results/verification_queue/');
    return response.data;
  },

  bulkEntry: async (results: Array<{ order_item: number; test_parameter: number; result_value: string; remarks?: string }>) => {
    const response = await api.post('/results/bulk_entry/', { results });
    return response.data;
  },
};

/**
 * Payment API service
 */
export const paymentApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<Payment>>('/payments/', { params });
    return response.data;
  },

  create: async (data: Partial<Payment>) => {
    const response = await api.post<Payment>('/payments/', data);
    return response.data;
  },

  getByOrder: async (orderId: number) => {
    const response = await api.get<PaginatedResponse<Payment>>('/payments/', {
      params: { order: orderId },
    });
    return response.data;
  },

  getReceipt: async (paymentId: number) => {
    const response = await api.get(`/payments/${paymentId}/receipt/`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

/**
 * Report API service
 */
export const reportApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<Report>>('/reports/', { params });
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get<Report>(`/reports/${id}/`);
    return response.data;
  },

  generate: async (orderId: number) => {
    const response = await api.post<Report>('/reports/generate/', { order_id: orderId });
    return response.data;
  },

  download: async (reportId: number) => {
    const response = await api.get(`/reports/${reportId}/download/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  markDelivered: async (reportId: number) => {
    const response = await api.post(`/reports/${reportId}/mark_delivered/`);
    return response.data;
  },

  uploadSignature: async (reportId: number, signature: File, signatureType: 'pathologist' | 'technician') => {
    const formData = new FormData();
    formData.append('signature', signature);
    formData.append('signature_type', signatureType);
    const response = await api.post<Report>(`/reports/${reportId}/upload_signature/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

/**
 * Dashboard API service
 */
export const dashboardApi = {
  getStatistics: async () => {
    const response = await api.get('/dashboard/statistics/');
    return response.data;
  },
};

/**
 * Reference Range API service
 */
export const referenceRangeApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<ReferenceRange>>('/laboratory/reference-ranges/', { params });
    return response.data;
  },

  get: async (id: number): Promise<ApiResponse<ReferenceRange>> => {
    const response = await api.get<ApiResponse<ReferenceRange>>(`/laboratory/reference-ranges/${id}/`);
    return response.data;
  },

  create: async (data: ReferenceRangeCreateRequest): Promise<ApiResponse<ReferenceRange>> => {
    const response = await api.post<ApiResponse<ReferenceRange>>('/laboratory/reference-ranges/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<ReferenceRangeCreateRequest>): Promise<ApiResponse<ReferenceRange>> => {
    const response = await api.patch<ApiResponse<ReferenceRange>>(`/laboratory/reference-ranges/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/laboratory/reference-ranges/${id}/`);
  },

  forParameter: async (parameterId: number, age?: number, gender?: string) => {
    const params: Record<string, unknown> = { parameter_id: parameterId };
    if (age !== undefined) params.age = age;
    if (gender) params.gender = gender;
    const response = await api.get<PaginatedResponse<ReferenceRange>>('/laboratory/reference-ranges/for_parameter/', { params });
    return response.data;
  },
};

/**
 * System Settings API service
 */
export const systemSettingsApi = {
  get: async (): Promise<ApiResponse<SystemSettings>> => {
    const response = await api.get<ApiResponse<SystemSettings>>('/core/settings/');
    return response.data;
  },

  update: async (data: Partial<SystemSettings>): Promise<ApiResponse<SystemSettings>> => {
    const response = await api.put<ApiResponse<SystemSettings>>('/core/settings/', data);
    return response.data;
  },

  patch: async (data: Partial<SystemSettings>): Promise<ApiResponse<SystemSettings>> => {
    const response = await api.patch<ApiResponse<SystemSettings>>('/core/settings/', data);
    return response.data;
  },
};

/**
 * Lab Terminal API service
 */
export const labTerminalApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<LabTerminal>>('/core/terminals/', { params });
    return response.data;
  },

  get: async (id: number): Promise<ApiResponse<LabTerminal>> => {
    const response = await api.get<ApiResponse<LabTerminal>>(`/core/terminals/${id}/`);
    return response.data;
  },

  create: async (data: LabTerminalCreateRequest): Promise<ApiResponse<LabTerminal>> => {
    const response = await api.post<ApiResponse<LabTerminal>>('/core/terminals/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<LabTerminalCreateRequest>): Promise<ApiResponse<LabTerminal>> => {
    const response = await api.patch<ApiResponse<LabTerminal>>(`/core/terminals/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/core/terminals/${id}/`);
  },

  getNextMrn: async (id: number) => {
    const response = await api.post(`/core/terminals/${id}/get_next_mrn/`);
    return response.data;
  },

  resetRange: async (id: number) => {
    const response = await api.post(`/core/terminals/${id}/reset_range/`);
    return response.data;
  },

  getActive: async () => {
    const response = await api.get<PaginatedResponse<LabTerminal>>('/core/terminals/active/');
    return response.data;
  },
};

/**
 * Notification API service
 */
export const notificationApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<Notification>>('/notifications/', { params });
    return response.data;
  },

  get: async (id: number): Promise<ApiResponse<Notification>> => {
    const response = await api.get<ApiResponse<Notification>>(`/notifications/${id}/`);
    return response.data;
  },
};
