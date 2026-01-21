import api from './client';
import type {
  Patient,
  PatientCreateRequest,
  PatientLookupResult,
  LabTest,
  TestPanel,
  TestCategory,
  TestSearchResult,
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
  TestParameter,
  WorklistPatient,
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

  lookup: async (mobile: string) => {
    const response = await api.get<ApiResponse<PatientLookupResult[]>>('/patients/lookup/', {
      params: { mobile },
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

  searchTests: async (query: string, limit = 20) => {
    const response = await api.get<ApiResponse<TestSearchResult[]>>('/laboratory/tests/search/', {
      params: { q: query, limit },
    });
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

  getExpected: async (orderItemId: number) => {
    const response = await api.get<{ results: Array<Record<string, unknown>> }>(
      '/results/expected/',
      { params: { order_item_id: orderItemId } },
    );
    return response.data;
  },

  ensure: async (orderItemId: number) => {
    const response = await api.post<{ results: TestResult[] }>(
      '/results/ensure/',
      {},
      { params: { order_item_id: orderItemId } },
    );
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

  uploadReportHeaderImage: async (file: File): Promise<SystemSettings> => {
    const formData = new FormData();
    formData.append('report_header_image', file);
    const response = await api.post<SystemSettings>('/core/settings/report-header-image/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  removeReportHeaderImage: async (): Promise<SystemSettings> => {
    const response = await api.delete<SystemSettings>('/core/settings/report-header-image/');
    return response.data;
  },

  uploadReportFooterImage: async (file: File): Promise<SystemSettings> => {
    const formData = new FormData();
    formData.append('report_footer_image', file);
    const response = await api.post<SystemSettings>('/core/settings/report-footer-image/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  removeReportFooterImage: async (): Promise<SystemSettings> => {
    const response = await api.delete<SystemSettings>('/core/settings/report-footer-image/');
    return response.data;
  },

  uploadLabLogo: async (file: File): Promise<SystemSettings> => {
    // Note: The backend viewset updates 'lab_logo' via standard update (PUT/PATCH) 
    // but requires multipart/form-data. Since we added MultiPartParser to the viewset,
    // we can use PATCH to update just the logo.
    const formData = new FormData();
    formData.append('lab_logo', file);
    const response = await api.patch<SystemSettings>('/core/settings/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    // The response determines the new settings with the logo URL
    if (response.data.success && response.data.data) return response.data.data;
    // Fallback if structure is different (ApiResponse vs direct object)
    // The interceptor or generic might return differently.
    // Based on `patch` implementation above: `await api.patch<ApiResponse<SystemSettings>>`
    // So response.data is ApiResponse.
    return response.data.data;
  },

  removeLabLogo: async (): Promise<SystemSettings> => {
    // To remove, we can send null? Or we might need a specific action.
    // Django FileField deletion usually requires passing empty or specific flag.
    // Alternatively, using the 'delete' method on a field if supported, but typically 
    // we'd used a dedicated action if we want to delete ONLY the file.
    // Or PATCH with null? DRF handles null if field is nullable.
    // Let's try PATCH with lab_logo: null.
    const response = await api.patch<ApiResponse<SystemSettings>>('/core/settings/', { lab_logo: null });
    return response.data.data;
  },
};

/**
 * Worklist API service
 */
export const worklistApi = {
  listPatients: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<WorklistPatient>>('/worklist/patients/', { params });
    return response.data;
  },
};
