import { useState, useEffect } from 'react'
import { settingsService, type WorkflowSettings } from '../../services/settings'

export function WorkflowSettingsPage() {
  const [settings, setSettings] = useState<WorkflowSettings>({
    enable_sample_collection: true,
    enable_sample_receive: true,
    enable_verification: true,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await settingsService.getWorkflowSettings()
      setSettings(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch settings')
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = (field: keyof WorkflowSettings) => {
    setSettings(prev => ({
      ...prev,
      [field]: !prev[field],
    }))
  }

  const handleSave = async () => {
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const updated = await settingsService.updateWorkflowSettings(settings)
      setSettings(updated)
      setSuccess('Workflow settings saved successfully!')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
        <p className="mt-2 text-gray-600">Loading settings...</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800">
          Workflow Customization
        </h1>
        <p className="text-gray-600 mt-2">
          Configure which workflow steps are enabled in your lab.
        </p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded">
          {success}
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 space-y-6">
          <div className="border-b pb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Sample Workflow Steps
            </h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <label
                    htmlFor="enable_sample_collection"
                    className="text-sm font-medium text-gray-900"
                  >
                    Enable Sample Collection Step
                  </label>
                  <p className="text-sm text-gray-500 mt-1">
                    Require manual sample collection by phlebotomy staff. If
                    disabled, samples are marked as collected automatically.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('enable_sample_collection')}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    settings.enable_sample_collection
                      ? 'bg-blue-600'
                      : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      settings.enable_sample_collection
                        ? 'translate-x-5'
                        : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <label
                    htmlFor="enable_sample_receive"
                    className="text-sm font-medium text-gray-900"
                  >
                    Enable Sample Receive Step
                  </label>
                  <p className="text-sm text-gray-500 mt-1">
                    Require manual sample receiving in the lab. If disabled,
                    samples are marked as received automatically.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('enable_sample_receive')}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    settings.enable_sample_receive
                      ? 'bg-blue-600'
                      : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      settings.enable_sample_receive
                        ? 'translate-x-5'
                        : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          <div className="border-b pb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Result Workflow Steps
            </h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <label
                    htmlFor="enable_verification"
                    className="text-sm font-medium text-gray-900"
                  >
                    Require Verification Before Publish
                  </label>
                  <p className="text-sm text-gray-500 mt-1">
                    Require results to be verified by authorized staff before
                    publishing. If disabled, results can be published directly
                    after entry.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('enable_verification')}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    settings.enable_verification
                      ? 'bg-blue-600'
                      : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      settings.enable_verification
                        ? 'translate-x-5'
                        : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-blue-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm text-blue-700">
              <strong>Note:</strong> Changes to workflow settings will affect
              how new orders and samples are processed. Existing orders will
              continue with their current workflow state.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
