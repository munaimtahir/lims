import { useState, useEffect } from 'react'
import { resultService } from '../../services/results'
import type { Result } from '../../types'
import { COLORS } from '../../utils/constants'

interface ResultFormData {
  value: string
  unit: string
  reference_range: string
  notes: string
}

export function ResultEntryPage() {
  const [results, setResults] = useState<Result[]>([])
  const [selectedResult, setSelectedResult] = useState<Result | null>(null)
  const [formData, setFormData] = useState<ResultFormData>({
    value: '',
    unit: '',
    reference_range: '',
    notes: '',
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const loadResults = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const allResults = await resultService.getAll()
      // Filter for DRAFT status - ready for entry
      const draftResults = allResults.filter((r) => r.status === 'DRAFT')
      setResults(draftResults)
    } catch (err) {
      console.error('Failed to load results:', err)
      setError('Failed to load results. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadResults()
  }, [])

  const handleSelectResult = (result: Result) => {
    setSelectedResult(result)
    setFormData({
      value: result.value || '',
      unit: result.unit || '',
      reference_range: result.reference_range || '',
      notes: result.notes || '',
    })
    setError(null)
    setSuccessMessage(null)
  }

  const handleSaveDraft = async () => {
    if (!selectedResult) return

    setIsSaving(true)
    setError(null)
    try {
      // Update the result with form data
      await resultService.update(selectedResult.id, {
        ...formData,
        status: 'DRAFT',
      })
      setSuccessMessage('Draft saved successfully')
      setTimeout(() => setSuccessMessage(null), 3000)
      await loadResults()
      setSelectedResult(null)
      setFormData({ value: '', unit: '', reference_range: '', notes: '' })
    } catch (err) {
      console.error('Failed to save draft:', err)
      setError('Failed to save draft. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleEnterResult = async () => {
    if (!selectedResult) return

    if (!formData.value.trim()) {
      setError('Result value is required')
      return
    }

    setIsSaving(true)
    setError(null)
    try {
      // First update the result with form data
      await resultService.update(selectedResult.id, {
        ...formData,
      })
      // Then mark as entered
      await resultService.enter(selectedResult.id)
      setSuccessMessage('Result entered successfully')
      setTimeout(() => setSuccessMessage(null), 3000)
      await loadResults()
      setSelectedResult(null)
      setFormData({ value: '', unit: '', reference_range: '', notes: '' })
    } catch (err) {
      console.error('Failed to enter result:', err)
      setError('Failed to enter result. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: Results List */}
      <div className="lg:col-span-1">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          Results Pending Entry
        </h2>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading...</p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && results.length === 0 && (
          <div className="bg-gray-50 border border-gray-200 text-gray-600 px-4 py-8 rounded-lg text-center">
            No results pending entry.
          </div>
        )}

        {/* Results List */}
        {!isLoading && results.length > 0 && (
          <div className="space-y-2">
            {results.map((result) => (
              <div
                key={result.id}
                onClick={() => handleSelectResult(result)}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                  selectedResult?.id === result.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <div className="font-medium text-gray-900">
                  Result ID: {result.id}
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  Order Item: {result.order_item}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Status:{' '}
                  <span
                    className={`px-2 py-0.5 rounded-full ${
                      COLORS.status[result.status as keyof typeof COLORS.status] ||
                      'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {result.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right: Entry Form */}
      <div className="lg:col-span-2">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Result Entry</h2>

        {/* Success Message */}
        {successMessage && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4">
            {successMessage}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {!selectedResult ? (
          <div className="bg-gray-50 border border-gray-200 text-gray-600 px-4 py-12 rounded-lg text-center">
            Select a result from the list to enter data.
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded">
              <h3 className="font-semibold text-gray-900 mb-2">
                Result Information
              </h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-600">Result ID:</span>{' '}
                  <span className="font-medium">{selectedResult.id}</span>
                </div>
                <div>
                  <span className="text-gray-600">Order Item:</span>{' '}
                  <span className="font-medium">{selectedResult.order_item}</span>
                </div>
                <div>
                  <span className="text-gray-600">Current Value:</span>{' '}
                  <span className="font-medium">
                    {selectedResult.value || 'Not entered'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Status:</span>{' '}
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs ${
                      COLORS.status[
                        selectedResult.status as keyof typeof COLORS.status
                      ] || 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {selectedResult.status}
                  </span>
                </div>
              </div>
            </div>

            {/* Form */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Result Value <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.value}
                  onChange={(e) =>
                    setFormData({ ...formData, value: e.target.value })
                  }
                  placeholder="Enter result value"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Unit
                </label>
                <input
                  type="text"
                  value={formData.unit}
                  onChange={(e) =>
                    setFormData({ ...formData, unit: e.target.value })
                  }
                  placeholder="e.g., mg/dL, g/dL"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Reference Range
                </label>
                <input
                  type="text"
                  value={formData.reference_range}
                  onChange={(e) =>
                    setFormData({ ...formData, reference_range: e.target.value })
                  }
                  placeholder="e.g., 0-5.5"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notes
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) =>
                    setFormData({ ...formData, notes: e.target.value })
                  }
                  rows={3}
                  placeholder="Enter any notes or comments"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleSaveDraft}
                  disabled={isSaving}
                  className="px-6 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 disabled:opacity-50"
                >
                  {isSaving ? 'Saving...' : 'Save as Draft'}
                </button>
                <button
                  onClick={handleEnterResult}
                  disabled={isSaving}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {isSaving ? 'Entering...' : 'Enter Result'}
                </button>
                <button
                  onClick={() => {
                    setSelectedResult(null)
                    setFormData({
                      value: '',
                      unit: '',
                      reference_range: '',
                      notes: '',
                    })
                    setError(null)
                  }}
                  className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
