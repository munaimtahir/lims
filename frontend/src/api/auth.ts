import api from './client';
import type { LoginRequest, LoginResponse, User, ApiResponse } from '../types';

/**
 * Authentication API service
 */
export const authApi = {
  /**
   * Login with username/email and password
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('auth/login/', credentials);
    return response.data;
  },

  /**
   * Logout and invalidate token
   */
  logout: async (refreshToken?: string): Promise<void> => {
    try {
      await api.post('auth/logout/', { refresh_token: refreshToken });
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API error:', error);
    }
  },

  /**
   * Get current user profile
   */
  me: async (): Promise<ApiResponse<User>> => {
    const response = await api.get<ApiResponse<User>>('auth/me/');
    return response.data;
  },

  /**
   * Change password
   */
  changePassword: async (
    userId: number,
    oldPassword: string,
    newPassword: string,
    newPasswordConfirm: string
  ): Promise<void> => {
    await api.post(`auth/users/${userId}/change_password/`, {
      old_password: oldPassword,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    });
  },
};
