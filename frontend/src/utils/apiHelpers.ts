/**
 * API Response Normalization Utilities
 * 
 * These utilities handle inconsistencies in API response shapes to prevent runtime errors.
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normalizeListResponse<T>(response: any): T[] {
  if (Array.isArray(response)) return response;
  if (response?.results) {
    if (Array.isArray(response.results)) return response.results;
    if (response.results?.data && Array.isArray(response.results.data)) {
      return response.results.data;
    }
  }
  if (response?.data && Array.isArray(response.data)) return response.data;
  console.warn('Could not extract array from response', response);
  return [];
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normalizeObjectResponse<T>(response: any): T | null {
  if (response && typeof response === 'object' && !Array.isArray(response)) {
    if ('data' in response && typeof response.data === 'object') {
      return response.data as T;
    }
    return response as T;
  }
  return null;
}
