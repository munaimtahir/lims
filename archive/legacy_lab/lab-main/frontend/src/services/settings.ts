import { apiClient } from './api'

/**
 * Interface for workflow settings.
 */
export interface WorkflowSettings {
  enable_sample_collection: boolean
  enable_sample_receive: boolean
  enable_verification: boolean
  updated_at?: string
}

/**
 * Interface for role permissions.
 */
export interface RolePermission {
  id?: number
  role: string
  can_register: boolean
  can_collect: boolean
  can_enter_result: boolean
  can_verify: boolean
  can_publish: boolean
  can_edit_catalog: boolean
  can_edit_settings: boolean
  updated_at?: string
}

/**
 * Interface for user permissions.
 */
export interface UserPermissions {
  role: string
  permissions: {
    can_register: boolean
    can_collect: boolean
    can_enter_result: boolean
    can_verify: boolean
    can_publish: boolean
    can_edit_catalog: boolean
    can_edit_settings: boolean
  }
}

/**
 * Service for handling settings-related API calls.
 */
export const settingsService = {
  /**
   * Retrieves the workflow settings.
   * @returns {Promise<WorkflowSettings>} A promise that resolves with the workflow settings.
   */
  async getWorkflowSettings(): Promise<WorkflowSettings> {
    return apiClient.get<WorkflowSettings>('/settings/workflow/')
  },

  /**
   * Updates the workflow settings.
   * @param {Partial<WorkflowSettings>} settings - The settings to update.
   * @returns {Promise<WorkflowSettings>} A promise that resolves with the updated workflow settings.
   */
  async updateWorkflowSettings(
    settings: Partial<WorkflowSettings>
  ): Promise<WorkflowSettings> {
    return apiClient.put<WorkflowSettings>('/settings/workflow/', settings)
  },

  /**
   * Retrieves the role permissions.
   * @returns {Promise<RolePermission[]>} A promise that resolves with an array of role permissions.
   */
  async getRolePermissions(): Promise<RolePermission[]> {
    return apiClient.get<RolePermission[]>('/settings/permissions/')
  },

  /**
   * Updates the role permissions.
   * @param {RolePermission[]} permissions - The permissions to update.
   * @returns {Promise<RolePermission[]>} A promise that resolves with the updated role permissions.
   */
  async updateRolePermissions(
    permissions: RolePermission[]
  ): Promise<RolePermission[]> {
    return apiClient.put<RolePermission[]>(
      '/settings/permissions/update/',
      permissions
    )
  },

  /**
   * Retrieves the permissions for the current user.
   * @returns {Promise<UserPermissions>} A promise that resolves with the user's permissions.
   */
  async getUserPermissions(): Promise<UserPermissions> {
    return apiClient.get<UserPermissions>('/settings/permissions/me/')
  },
}
