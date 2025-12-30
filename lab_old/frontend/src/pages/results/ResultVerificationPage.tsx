import { useState, useEffect } from 'react'
import { resultService } from '../../services/results'
import type { Result } from '../../types'
import { COLORS } from '../../utils/constants'

export function ResultVerificationPage() {
  const [results, setResults] = useState<Result[]>([])
  const [selectedResult, setSelectedResult] = useState<Result | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const loadResults = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const allResults = await resultService.getAll()
      // Filter for ENTERED status - ready for verification
      const enteredResults = allResults.filter((r) => r.status === 'ENTERED')
      setResults(enteredResults)
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
    setError(null)
    setSuccessMessage(null)
  }

  const handleVerifyResult = async () => {
    if (!selectedResult) return

    setIsProcessing(true)
    setError(null)
    try {
      await resultService.verify(selectedResult.id)
      setSuccessMessage('Result verified successfully')
      setTimeout(() => setSuccessMessage(null), 3000)
      await loadResults()
      setSelectedResult(null)
    } catch (err) {
      console.error('Failed to verify result:', err)
      setError('Failed to verify result. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleRejectResult = async () => {
    if (!selectedResult) return

    const reason = prompt(
      'Enter reason for rejection (result will be sent back to technologist):'
    )
    if (!reason || !reason.trim()) {
      return
    }

    setIsProcessing(true)
    setError(null)
    try {
      // Update result with rejection notes and change status back to DRAFT
      await resultService.update(selectedResult.id, {
        status: 'DRAFT',
        notes: `Rejected: ${reason.trim()}`,
      })
      setSuccessMessage('Result rejected and sent back for correction')
      setTimeout(() => setSuccessMessage(null), 3000)
      await loadResults()
      setSelectedResult(null)
    } catch (err) {
      console.error('Failed to reject result:', err)
      setError('Failed to reject result. Please try again.')
    } finally {
      setIsProcessing(false)
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

  const isOutOfRange = (value: string, range: string): boolean => {
    if (!value || !range) return false

    const numValue = parseFloat(value)
    if (isNaN(numValue)) return false

    // Parse range like "0-5.5" or "< 10" or "> 5"
    const rangeMatch = range.match(/(\d+\.?\d*)\s*-\s*(\d+\.?\d*)/)
    if (rangeMatch) {
      const [, min, max] = rangeMatch
      return numValue < parseFloat(min) || numValue > parseFloat(max)
    }

    return false
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: Results List */}
      <div className="lg:col-span-1">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          Results Pending Verification
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
            No results pending verification.
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
                <div className="text-sm text-gray-900 mt-1 font-semibold">
                  Value: {result.value} {result.unit}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Entered: {formatDateTime(result.entered_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right: Verification Details */}
      <div className="lg:col-span-2">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          Result Verification
        </h2>

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
            Select a result from the list to verify.
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-6">
            {/* Result Details */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Result Details
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">
                    Result ID
                  </label>
                  <p className="text-gray-900 font-semibold">
                    {selectedResult.id}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">
                    Order Item
                  </label>
                  <p className="text-gray-900">{selectedResult.order_item}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">
                    Status
                  </label>
                  <p>
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        COLORS.status[
                          selectedResult.status as keyof typeof COLORS.status
                        ] || 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {selectedResult.status}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">
                    Entered At
                  </label>
                  <p className="text-gray-900">
                    {formatDateTime(selectedResult.entered_at)}
                  </p>
                </div>
              </div>
            </div>

            {/* Result Value with Range Check */}
            <div
              className={`p-4 rounded-lg mb-6 ${
                isOutOfRange(
                  selectedResult.value,
                  selectedResult.reference_range || ''
                )
                  ? 'bg-red-50 border-2 border-red-300'
                  : 'bg-green-50 border-2 border-green-200'
              }`}
            >
              <h3 className="text-lg font-semibold mb-3">Result Value</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">
                    Value
                  </label>
                  <p className="text-2xl font-bold text-gray-900">
                    {selectedResult.value}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">
                    Unit
                  </label>
                  <p className="text-xl text-gray-900">
                    {selectedResult.unit || '-'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">
                    Reference Range
                  </label>
                  <p className="text-xl text-gray-900">
                    {selectedResult.reference_range || 'Not specified'}
                  </p>
                </div>
              </div>
              {isOutOfRange(
                selectedResult.value,
                selectedResult.reference_range || ''
              ) && (
                <div className="mt-3 p-2 bg-red-100 text-red-800 rounded text-sm font-medium">
                  ⚠️ Out of Range - Review carefully before verification
                </div>
              )}
            </div>

            {/* Flags and Notes */}
            {(selectedResult.flags || selectedResult.notes) && (
              <div className="mb-6 space-y-3">
                {selectedResult.flags && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">
                      Flags
                    </label>
                    <p className="text-gray-900">{selectedResult.flags}</p>
                  </div>
                )}
                {selectedResult.notes && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">
                      Notes
                    </label>
                    <p className="text-gray-900">{selectedResult.notes}</p>
                  </div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t">
              <button
                onClick={handleVerifyResult}
                disabled={isProcessing}
                className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 font-medium"
              >
                {isProcessing ? 'Verifying...' : 'Verify Result'}
              </button>
              <button
                onClick={handleRejectResult}
                disabled={isProcessing}
                className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {isProcessing ? 'Rejecting...' : 'Reject & Send Back'}
              </button>
              <button
                onClick={() => {
                  setSelectedResult(null)
                  setError(null)
                }}
                className="px-6 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
