import { useState, useEffect } from 'react'
import { resultService } from '../../services/results'
import type { Result } from '../../types'
import { COLORS } from '../../utils/constants'

export function ResultPublishingPage() {
  const [results, setResults] = useState<Result[]>([])
  const [selectedResults, setSelectedResults] = useState<number[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const loadResults = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const allResults = await resultService.getAll()
      // Filter for VERIFIED status - ready for publishing
      const verifiedResults = allResults.filter((r) => r.status === 'VERIFIED')
      setResults(verifiedResults)
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

  const handleSelectResult = (resultId: number) => {
    setSelectedResults((prev) =>
      prev.includes(resultId)
        ? prev.filter((id) => id !== resultId)
        : [...prev, resultId]
    )
  }

  const handleSelectAll = () => {
    if (selectedResults.length === results.length) {
      setSelectedResults([])
    } else {
      setSelectedResults(results.map((r) => r.id))
    }
  }

  const handlePublishResults = async () => {
    if (selectedResults.length === 0) {
      setError('Please select at least one result to publish')
      return
    }

    const confirmed = window.confirm(
      `Are you sure you want to publish ${selectedResults.length} result(s)? This action cannot be undone.`
    )
    if (!confirmed) return

    setIsPublishing(true)
    setError(null)
    try {
      // Publish each selected result
      for (const resultId of selectedResults) {
        await resultService.publish(resultId)
      }
      setSuccessMessage(
        `Successfully published ${selectedResults.length} result(s)`
      )
      setTimeout(() => setSuccessMessage(null), 3000)
      setSelectedResults([])
      await loadResults()
    } catch (err) {
      console.error('Failed to publish results:', err)
      setError('Failed to publish some results. Please try again.')
    } finally {
      setIsPublishing(false)
    }
  }

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Result Publishing</h1>
        <div className="text-sm text-gray-600">
          {selectedResults.length > 0 && (
            <span className="font-medium">
              {selectedResults.length} result(s) selected
            </span>
          )}
        </div>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
          {successMessage}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Action Buttons */}
      {results.length > 0 && (
        <div className="mb-4 flex gap-3">
          <button
            onClick={handleSelectAll}
            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
          >
            {selectedResults.length === results.length
              ? 'Deselect All'
              : 'Select All'}
          </button>
          <button
            onClick={handlePublishResults}
            disabled={selectedResults.length === 0 || isPublishing}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {isPublishing
              ? 'Publishing...'
              : `Publish Selected (${selectedResults.length})`}
          </button>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading results...</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && results.length === 0 && (
        <div className="bg-gray-50 border border-gray-200 text-gray-600 px-4 py-12 rounded-lg text-center">
          No verified results pending publication.
        </div>
      )}

      {/* Results Table */}
      {!isLoading && results.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedResults.length === results.length}
                    onChange={handleSelectAll}
                    className="w-4 h-4"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Result ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Order Item
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Unit
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Reference Range
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Verified At
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.map((result) => (
                <tr
                  key={result.id}
                  className={`hover:bg-gray-50 ${
                    selectedResults.includes(result.id) ? 'bg-blue-50' : ''
                  }`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedResults.includes(result.id)}
                      onChange={() => handleSelectResult(result.id)}
                      className="w-4 h-4"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {result.id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {result.order_item}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                    {result.value}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {result.unit || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {result.reference_range || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        COLORS.status[
                          result.status as keyof typeof COLORS.status
                        ] || 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {result.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDateTime(result.verified_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Summary */}
      {!isLoading && results.length > 0 && (
        <div className="mt-4 text-sm text-gray-600">
          Showing {results.length} verified result{results.length !== 1 ? 's' : ''}{' '}
          ready for publication
        </div>
      )}
    </div>
  )
}
