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
  OrderItem,
  TestResult,
  Payment,
  Report,
  ApiResponse,
  PaginatedResponse,
  User,
  ReferenceRange,
  ReferenceRangeCreateRequest,
  SystemSettings,
  TestParameter,
  WorklistPatient,
  PrintTemplate,
  CatalogImportSummary,
  CatalogAuditSummary,
  BackupArtifact,
  BackupSettings,
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

  globalSearch: async (query: string) => {
    const response = await api.get<{ success: boolean, data: any[] }>('/patients/search/', {
      params: { q: query },
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

  exportCatalog: async () => {
    const response = await api.get('/laboratory/export/', { responseType: 'blob' });
    return response.data as Blob;
  },

  importCatalog: async (
    file: File,
    options: { strict: boolean; allow_defaults: boolean; mode: string; dry_run: boolean }
  ) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<{ summary: CatalogImportSummary }>(
      '/laboratory/import/',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        params: options,
      }
    );
    return response.data;
  },

  auditCatalog: async () => {
    const response = await api.get<CatalogAuditSummary>('/laboratory/catalog/audit/');
    return response.data;
  },

  downloadImportTemplate: async () => {
    const response = await api.get('/laboratory/import/download-template/', { responseType: 'blob' });
    return response.data as Blob;
  },

  // Mutations
  createTest: async (data: Partial<LabTest>) => {
    const response = await api.post<LabTest>('/laboratory/tests/', data);
    return response.data;
  },
  updateTest: async (id: number, data: Partial<LabTest>) => {
    const response = await api.patch<LabTest>(`/laboratory/tests/${id}/`, data);
    return response.data;
  },
  deleteTest: async (id: number) => {
    await api.delete(`/laboratory/tests/${id}/`);
  },

  createPanel: async (data: Partial<TestPanel>) => {
    const response = await api.post<TestPanel>('/laboratory/panels/', data);
    return response.data;
  },
  updatePanel: async (id: number, data: Partial<TestPanel>) => {
    const response = await api.patch<TestPanel>(`/laboratory/panels/${id}/`, data);
    return response.data;
  },
  deletePanel: async (id: number) => {
    await api.delete(`/laboratory/panels/${id}/`);
  },

  createParameter: async (data: Partial<TestParameter>) => {
    const response = await api.post<TestParameter>('/laboratory/parameters/', data);
    return response.data;
  },
  updateParameter: async (id: number, data: Partial<TestParameter>) => {
    const response = await api.patch<TestParameter>(`/laboratory/parameters/${id}/`, data);
    return response.data;
  },
  deleteParameter: async (id: number) => {
    await api.delete(`/laboratory/parameters/${id}/`);
  },

  createCategory: async (data: Partial<TestCategory>) => {
    const response = await api.post<TestCategory>('/laboratory/categories/', data);
    return response.data;
  },
  updateCategory: async (id: number, data: Partial<TestCategory>) => {
    const response = await api.patch<TestCategory>(`/laboratory/categories/${id}/`, data);
    return response.data;
  },
  deleteCategory: async (id: number) => {
    await api.delete(`/laboratory/categories/${id}/`);
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

  getOrderItem: async (id: number) => {
    const response = await api.get<OrderItem>(`/orders/order-items/${id}/`);
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

  updateStatus: async (id: number, status: string, barcode?: string, postponement_reason?: string, additionalData?: Record<string, unknown>) => {
    const response = await api.patch<SampleCollection>(`/samples/${id}/`, {
      status,
      ...(barcode && { barcode }),
      ...(postponement_reason && { postponement_reason }),
      ...additionalData,
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

  bulkVerify: async (resultIds: number[]) => {
    const response = await api.post('/results/bulk-verify/', { result_ids: resultIds });
    return response.data;
  },

  bulkReject: async (resultIds: number[], reason: string) => {
    const response = await api.post('/results/bulk-reject/', { result_ids: resultIds, reason });
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
 * User management API service
 */
export const userApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<User>>('/auth/users/', { params });
    return response.data;
  },

  create: async (data: {
    username: string;
    email: string;
    full_name: string;
    role: User['role'];
    password: string;
    password_confirm: string;
  }) => {
    const response = await api.post<ApiResponse<User>>('/auth/users/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<User>) => {
    const response = await api.patch<ApiResponse<User>>(`/auth/users/${id}/`, data);
    return response.data;
  },

  remove: async (id: number) => {
    await api.delete(`/auth/users/${id}/`);
  },

  resetPassword: async (id: number, newPassword: string, newPasswordConfirm: string) => {
    const response = await api.post<{ success: boolean; message?: string }>(`/auth/users/${id}/reset_password/`, {
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
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
    const response = await api.patch<ApiResponse<SystemSettings>>('/core/settings/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    // The response determines the new settings with the logo URL
    if (response.data.success && response.data.data) return response.data.data;
    // Fallback if structure is different (ApiResponse vs direct object)
    // The interceptor or generic might return differently.
    // Based on `patch` implementation above: `await api.patch<ApiResponse<SystemSettings>>`
    // So response.data is ApiResponse.
    return response.data.data as SystemSettings;
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

export const printTemplateApi = {
  list: async () => {
    const response = await api.get<PrintTemplate[]>('/core/print-templates/');
    return response.data;
  },
  create: async (data: Partial<PrintTemplate>) => {
    const response = await api.post<PrintTemplate>('/core/print-templates/', data);
    return response.data;
  },
  update: async (id: number, data: Partial<PrintTemplate>) => {
    const response = await api.patch<PrintTemplate>(`/core/print-templates/${id}/`, data);
    return response.data;
  },
  delete: async (id: number) => {
    await api.delete(`/core/print-templates/${id}/`);
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

/**
 * Analytics & Reports API service
 */
export const analyticsApi = {
  overview: async (params?: Record<string, unknown>) => {
    const response = await api.get('/reports/overview/', { params });
    return response.data;
  },
  patients: async (params?: Record<string, unknown>) => {
    const response = await api.get('/reports/patients/', { params });
    return response.data;
  },
  tests: async (params?: Record<string, unknown>) => {
    const response = await api.get('/reports/tests/', { params });
    return response.data;
  },
  referrals: async (params?: Record<string, unknown>) => {
    const response = await api.get('/reports/referrals/', { params });
    return response.data;
  },
  finance: async (params?: Record<string, unknown>) => {
    const response = await api.get('/reports/finance/', { params });
    return response.data;
  },
  exportReport: async (reportKey: string, format: 'csv' | 'xlsx', params?: Record<string, unknown>) => {
    const response = await api.post(
      '/reports/export/',
      { report_key: reportKey, format, filters: params },
      { responseType: 'blob' }
    );
    return response.data;
  },
  exportLogs: async (params?: Record<string, unknown>) => {
    const response = await api.get('/reports/export-logs/', { params });
    return response.data;
  },
};

export const backupApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await api.get<PaginatedResponse<BackupArtifact>>('/backups/', { params });
    return response.data;
  },
  get: async (id: string) => {
    const response = await api.get<BackupArtifact>(`/backups/${id}/`);
    return response.data;
  },
  create: async (pushOffsite = false) => {
    const response = await api.post<BackupArtifact>('/backups/', { push_offsite: pushOffsite });
    return response.data;
  },
  download: async (id: string) => {
    const response = await api.get(`/backups/${id}/download/`, { responseType: 'blob' });
    return response.data as Blob;
  },
  restore: async (id: string, confirmation: string) => {
    const response = await api.post(`/backups/${id}/restore/`, { confirmation });
    return response.data;
  },
  importBackup: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<BackupArtifact>('/backups/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  push: async (id: string) => {
    const response = await api.post<BackupArtifact>(`/backups/${id}/push/`);
    return response.data;
  },
  remove: async (id: string) => {
    await api.delete(`/backups/${id}/`);
  },
  settings: async () => {
    const response = await api.get<BackupSettings>('/backups/settings/');
    return response.data;
  },
  testOffsite: async () => {
    const response = await api.post<{ ok: boolean; message: string }>('/backups/offsite-test/');
    return response.data;
  },
};
