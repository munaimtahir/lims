// API Configuration
// ==============================================================================
// Environment-driven API base URL configuration
// Priority: VITE_API_URL env var > mode-based default
// ==============================================================================

// Default API URLs for each mode
const DEFAULT_DEV_API_URL = 'http://localhost:8000/api' // Direct backend access for local dev
const DEFAULT_PROD_API_URL = '/api' // Nginx proxies /api to backend in production

/**
 * Determines the API base URL for the application
 * 
 * Resolution order:
 * 1. If VITE_API_URL environment variable is set and non-empty, use it
 * 2. Otherwise, use mode-based default:
 *    - development: http://localhost:8000
 *    - production: /api
 * 
 * Production setup:
 * - Nginx serves frontend on port 80
 * - Nginx proxies /api/* to backend:8000
 * - Frontend uses relative path /api
 * 
 * Development setup:
 * - Frontend dev server on localhost:5173
 * - Backend dev server on localhost:8000
 * - Frontend uses full URL http://localhost:8000/api
 */
const getApiBaseUrl = (): string => {
  const envApiUrl = import.meta.env.VITE_API_URL
  const mode = import.meta.env.MODE
  
  // Check if env var is set and non-empty (handle empty strings)
  if (typeof envApiUrl === 'string' && envApiUrl.trim().length > 0) {
    return envApiUrl.trim()
  }
  
  // Fall back to mode-based default
  return mode === 'production' ? DEFAULT_PROD_API_URL : DEFAULT_DEV_API_URL
}

export const API_BASE_URL = getApiBaseUrl()

// Auth endpoints
// NOTE: These paths are relative to API_BASE_URL
// In production: API_BASE_URL="/api" + "/auth/login/" = "/api/auth/login/"
// In development: API_BASE_URL="http://localhost:8000/api" + "/auth/login/" = "http://localhost:8000/api/auth/login/"
export const AUTH_ENDPOINTS = {
  LOGIN: '/auth/login/',
  REFRESH: '/auth/refresh/',
  LOGOUT: '/auth/logout/',
} as const

// User management endpoints
export const USER_ENDPOINTS = {
  LIST: '/auth/users/',
  DETAIL: (id: number) => `/auth/users/${id}/`,
} as const

// Patient endpoints
export const PATIENT_ENDPOINTS = {
  LIST: '/patients/',
  DETAIL: (id: number) => `/patients/${id}/`,
} as const

// Catalog endpoints
export const CATALOG_ENDPOINTS = {
  LIST: '/catalog/',
  DETAIL: (id: number) => `/catalog/${id}/`,
} as const

// Terminal endpoints
export const TERMINAL_ENDPOINTS = {
  LIST: '/terminals/',
  DETAIL: (id: number) => `/terminals/${id}/`,
} as const

// Order endpoints
export const ORDER_ENDPOINTS = {
  LIST: '/orders/',
  DETAIL: (id: number) => `/orders/${id}/`,
  CANCEL: (id: number) => `/orders/${id}/cancel/`,
  EDIT_TESTS: (id: number) => `/orders/${id}/edit-tests/`,
} as const

// Sample endpoints
export const SAMPLE_ENDPOINTS = {
  LIST: '/samples/',
  DETAIL: (id: number) => `/samples/${id}/`,
  COLLECT: (id: number) => `/samples/${id}/collect/`,
  RECEIVE: (id: number) => `/samples/${id}/receive/`,
  REJECT: (id: number) => `/samples/${id}/reject/`,
} as const

// Result endpoints
export const RESULT_ENDPOINTS = {
  LIST: '/results/',
  DETAIL: (id: number) => `/results/${id}/`,
  ENTER: (id: number) => `/results/${id}/enter/`,
  VERIFY: (id: number) => `/results/${id}/verify/`,
  PUBLISH: (id: number) => `/results/${id}/publish/`,
} as const

// Report endpoints
export const REPORT_ENDPOINTS = {
  LIST: '/reports/',
  DETAIL: (id: number) => `/reports/${id}/`,
  GENERATE: (orderId: number) => `/reports/generate/${orderId}/`,
  DOWNLOAD: (id: number) => `/reports/${id}/download/`,
} as const

// Dashboard endpoints
export const DASHBOARD_ENDPOINTS = {
  ANALYTICS: '/dashboard/analytics/',
} as const

// Health endpoint
export const HEALTH_ENDPOINT = '/health/'

// Route paths
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  LAB: '/lab',
  LAB_NEW: '/lab/new',
  LAB_WORKLIST: '/lab/worklist',
  LAB_ORDER: '/lab/orders/:id',
  LAB_ORDER_DETAIL: (id: number | string) => `/lab/orders/${id}`,
  PATIENTS: '/patients',
  PATIENT_DETAIL: (id: number | string) => `/patients/${id}`,
  PHLEBOTOMY: '/phlebotomy',
  RESULT_ENTRY: '/results/entry',
  RESULT_VERIFICATION: '/results/verification',
  RESULT_PUBLISHING: '/results/publishing',
  REPORTS: '/reports',
  REPORT_VIEW: (id: number | string) => `/reports/${id}`,
  CSV_IMPORT: '/settings/import',
  CSV_IMPORT_TESTS: '/settings/import/tests',
  CSV_IMPORT_PARAMETERS: '/settings/import/parameters',
  CSV_IMPORT_RANGES: '/settings/import/ranges',
  SETTINGS: '/settings',
  ADMIN_USERS: '/settings/users',
  ADMIN_CATALOG: '/settings/catalog',
  ADMIN_TERMINALS: '/settings/terminals',
  ADMIN_DASHBOARD: '/dashboard',
} as const

// Role-based permissions
export const ROLE_PERMISSIONS = {
  ADMIN: ['all'],
  RECEPTION: ['patients', 'orders', 'reports.view'],
  PHLEBOTOMY: ['samples.collect', 'worklist.view'],
  TECHNOLOGIST: ['samples.receive', 'results.enter', 'worklist.view'],
  PATHOLOGIST: [
    'results.verify',
    'results.publish',
    'reports.generate',
    'worklist.view',
  ],
} as const

// Color scheme matching existing xMed EMR
export const COLORS = {
  header: {
    bg: 'bg-red-900',
    text: 'text-white',
  },
  section: {
    bg: 'bg-blue-700',
    text: 'text-white',
  },
  card: {
    bg: 'bg-teal-50',
    border: 'border-teal-200',
    hover: 'hover:bg-teal-100',
  },
  status: {
    NEW: 'bg-blue-100 text-blue-800',
    COLLECTED: 'bg-yellow-100 text-yellow-800',
    IN_PROCESS: 'bg-purple-100 text-purple-800',
    VERIFIED: 'bg-green-100 text-green-800',
    PUBLISHED: 'bg-green-200 text-green-900',
    CANCELLED: 'bg-gray-300 text-gray-700',
    PENDING: 'bg-gray-100 text-gray-800',
    RECEIVED: 'bg-teal-100 text-teal-800',
    REJECTED: 'bg-red-100 text-red-800',
    DRAFT: 'bg-gray-100 text-gray-800',
    ENTERED: 'bg-blue-100 text-blue-800',
  },
} as const

// Local storage keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
} as const
