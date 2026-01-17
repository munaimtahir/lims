/**
 * User and authentication types
 */
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
}

export type UserRole =
  | 'Admin'
  | 'Receptionist'
  | 'Cashier'
  | 'Phlebotomist'
  | 'Lab Technician'
  | 'Pathologist'
  | 'Manager';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  data: {
    user: User;
    access_token: string;
    refresh_token: string;
  };
  message: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

/**
 * Patient types
 */
export interface Patient {
  id: number;
  patient_id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  date_of_birth: string;
  age: number;
  gender: 'Male' | 'Female' | 'Other';
  phone: string;
  email?: string;
  national_id?: string;
  address?: string;
  created_at: string;
  updated_at: string;
  total_orders: number;
  last_visit?: string;
}

export interface PatientCreateRequest {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: 'Male' | 'Female' | 'Other';
  phone: string;
  email?: string;
  national_id?: string;
  address?: string;
}

/**
 * Test catalog types
 */
export interface TestCategory {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
}

export interface TestParameter {
  id: number;
  test: number;
  parameter_name: string;
  loinc_code?: string;
  unit: string;
  reference_min_male?: number;
  reference_max_male?: number;
  reference_min_female?: number;
  reference_max_female?: number;
  critical_low?: number;
  critical_high?: number;
  decimal_places: number;
  display_order: number;
}

export interface LabTest {
  id: number;
  category: number;
  category_name: string;
  test_code: string;
  test_name: string;
  loinc_code?: string;
  sample_type: string;
  sample_volume?: string;
  price: string;
  turnaround_time: number;
  instructions?: string;
  is_active: boolean;
  parameters: TestParameter[];
}

export interface TestPanel {
  id: number;
  panel_code: string;
  panel_name: string;
  category: number;
  category_name: string;
  sample_type: string;
  sample_volume?: string;
  price: string;
  turnaround_time: number;
  tests: LabTest[];
  description?: string;
  is_active: boolean;
}

/**
 * Order types
 */
export type OrderStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';

export interface OrderItem {
  id: number;
  test?: number;
  panel?: number;
  test_name?: string;
  panel_name?: string;
  test_code?: string;
  panel_code?: string;
  price: string;
  status: string;
}

export interface Order {
  id: number;
  order_id: string;
  patient: number;
  patient_name: string;
  ordered_by?: number;
  ordered_by_name?: string;
  created_at: string;
  updated_at: string;
  status: OrderStatus;
  notes: string;
  total_amount: string;
  discount: string;
  net_amount: string;
  is_paid: boolean;
  items: OrderItem[];
}

export interface OrderCreateRequest {
  patient: number;
  test_ids?: number[];
  panel_ids?: number[];
  discount?: string;
  notes?: string;
}

/**
 * Sample collection types
 */
export type SampleStatus = 'pending' | 'collected' | 'received' | 'rejected';

export interface SampleCollection {
  id: number;
  order: number;
  order_id: string;
  patient_name: string;
  order_items: number[];
  sample_type: string;
  barcode?: string;
  status: SampleStatus;
  collected_at?: string;
  collected_by?: number;
  collected_by_name?: string;
  notes: string;
}

/**
 * Result types
 */
export type ResultFlag =
  | ''
  | 'L'
  | 'H'
  | 'C'
  | 'normal'
  | 'low'
  | 'high'
  | 'critical_low'
  | 'critical_high'
  | 'abnormal';
export type ResultStatus = 'pending' | 'verified' | 'rejected';

export interface TestResult {
  id: number;
  order_item: number;
  test_parameter: number;
  parameter_name: string;
  unit: string;
  result_value: string;
  flag: ResultFlag;
  remarks: string;
  entered_by?: number;
  entered_by_name?: string;
  entered_at: string;
  verified_by?: number;
  verified_by_name?: string;
  verified_at?: string;
  status: ResultStatus;
}

/**
 * Billing types
 */
export type PaymentMethod = 'cash' | 'card' | 'bank_transfer' | 'mobile_money' | 'insurance';

export interface Payment {
  id: number;
  order: number;
  amount: string;
  payment_method: PaymentMethod;
  transaction_id?: string;
  payment_date: string;
  recorded_by?: number;
  recorded_by_name?: string;
  notes: string;
}

/**
 * Report types
 */
export interface Report {
  id: number;
  order: number;
  order_id_display?: string;
  report_file: string;
  generated_at: string;
  generated_by?: number;
  generated_by_name?: string;
  is_final: boolean;
  pathologist_signature?: string;
  technician_signature?: string;
  verified_by?: number;
  verified_by_name?: string;
  verified_at?: string;
}

/**
 * API response types
 */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  message?: string;
  [key: string]: unknown;
}

/**
 * Reference Range types
 */
export interface ReferenceRange {
  id: number;
  parameter: number;
  parameter_name: string;
  test_name: string;
  test_code: string;
  age_min?: number;
  age_max?: number;
  gender: 'Male' | 'Female' | 'Both';
  reference_min?: number;
  reference_max?: number;
  critical_low?: number;
  critical_high?: number;
  version: number;
  is_active: boolean;
  effective_date: string;
  notes?: string;
  created_at: string;
  created_by?: number;
  created_by_name?: string;
}

export interface ReferenceRangeCreateRequest {
  parameter: number;
  age_min?: number;
  age_max?: number;
  gender: 'Male' | 'Female' | 'Both';
  reference_min?: number;
  reference_max?: number;
  critical_low?: number;
  critical_high?: number;
  notes?: string;
}

/**
 * System Settings types
 */
export interface SystemSettings {
  id: number;
  lab_name: string;
  lab_address?: string;
  lab_phone?: string;
  lab_email?: string;
  lab_logo?: string;
  report_header?: string;
  report_footer?: string;
  currency: string;
  tax_rate: string;
  email_host?: string;
  email_port: number;
  email_use_tls: boolean;
  email_use_ssl: boolean;
  email_host_user?: string;
  email_host_password?: string;
  email_from?: string;
  backup_enabled: boolean;
  backup_frequency: 'daily' | 'weekly' | 'monthly';
  updated_at: string;
  updated_by?: number;
  updated_by_name?: string;
}
