import { useState, useEffect } from 'react'
import { settingsService, type WorkflowSettings } from '../services/settings'

/**
 * Custom hook for fetching and managing workflow settings.
 * @returns {object} An object containing the workflow settings, loading state, error state, and a refresh function.
 */
export function useWorkflowSettings() {
  const [settings, setSettings] = useState<WorkflowSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      setLoading(true)
      const data = await settingsService.getWorkflowSettings()
      setSettings(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch settings')
    } finally {
      setLoading(false)
    }
  }

  /**
   * Refreshes the workflow settings.
   */
  const refresh = () => {
    fetchSettings()
  }

  return {
    settings,
    loading,
    error,
    refresh,
    enableSampleCollection: settings?.enable_sample_collection ?? true,
    enableSampleReceive: settings?.enable_sample_receive ?? true,
    enableVerification: settings?.enable_verification ?? true,
  }
}
