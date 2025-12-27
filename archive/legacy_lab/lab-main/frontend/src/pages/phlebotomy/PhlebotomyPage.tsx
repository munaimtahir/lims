import { useState, useEffect } from 'react'
import { sampleService } from '../../services/samples'
import type { Sample } from '../../types'
import { COLORS } from '../../utils/constants'

export function PhlebotomyPage() {
  const [samples, setSamples] = useState<Sample[]>([])
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [searchBarcode, setSearchBarcode] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const loadSamples = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const allSamples = await sampleService.getAll()
      setSamples(allSamples)
    } catch (err) {
      console.error('Failed to load samples:', err)
      setError('Failed to load samples. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadSamples()
  }, [])

  const handleCollectSample = async (sampleId: number) => {
    try {
      setError(null)
      await sampleService.collect(sampleId)
      setSuccessMessage('Sample collected successfully')
      setTimeout(() => setSuccessMessage(null), 3000)
      await loadSamples()
    } catch (err) {
      console.error('Failed to collect sample:', err)
      setError('Failed to collect sample. Please try again.')
    }
  }

  const handleReceiveSample = async (sampleId: number) => {
    try {
      setError(null)
      await sampleService.receive(sampleId)
      setSuccessMessage('Sample received successfully')
      setTimeout(() => setSuccessMessage(null), 3000)
      await loadSamples()
    } catch (err) {
      console.error('Failed to receive sample:', err)
      setError('Failed to receive sample. Please try again.')
    }
  }

  const handleRejectSample = async (sampleId: number) => {
    const reason = prompt('Enter rejection reason:')
    if (!reason || !reason.trim()) {
      return
    }

    try {
      setError(null)
      await sampleService.reject(sampleId, reason.trim())
      setSuccessMessage('Sample rejected successfully')
      setTimeout(() => setSuccessMessage(null), 3000)
      await loadSamples()
    } catch (err) {
      console.error('Failed to reject sample:', err)
      setError('Failed to reject sample. Please try again.')
    }
  }

  const filteredSamples = samples.filter((sample) => {
    const matchesStatus = filterStatus === 'all' || sample.status === filterStatus
    const matchesBarcode =
      !searchBarcode || sample.barcode.toLowerCase().includes(searchBarcode.toLowerCase())
    return matchesStatus && matchesBarcode
  })

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return '-'
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
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        Sample Collection & Receiving
      </h1>

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

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Status
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="PENDING">Pending Collection</option>
              <option value="COLLECTED">Collected</option>
              <option value="RECEIVED">Received</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search by Barcode
            </label>
            <input
              type="text"
              value={searchBarcode}
              onChange={(e) => setSearchBarcode(e.target.value)}
              placeholder="Enter barcode..."
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading samples...</p>
        </div>
      )}

      {/* Sample List */}
      {!isLoading && filteredSamples.length === 0 && (
        <div className="bg-gray-50 border border-gray-200 text-gray-600 px-4 py-12 rounded-lg text-center">
          No samples found matching your criteria.
        </div>
      )}

      {!isLoading && filteredSamples.length > 0 && (
        <>
          <div className="bg-white rounded-lg shadow overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Barcode
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Sample Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Collected At
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Received At
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Rejection Reason
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredSamples.map((sample) => (
                  <tr key={sample.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {sample.barcode}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {sample.sample_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          COLORS.status[sample.status as keyof typeof COLORS.status] ||
                          'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {sample.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatDateTime(sample.collected_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatDateTime(sample.received_at)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {sample.rejection_reason || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      {sample.status === 'PENDING' && (
                        <button
                          onClick={() => handleCollectSample(sample.id)}
                          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-xs"
                        >
                          Collect
                        </button>
                      )}
                      {sample.status === 'COLLECTED' && (
                        <>
                          <button
                            onClick={() => handleReceiveSample(sample.id)}
                            className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-xs"
                          >
                            Receive
                          </button>
                          <button
                            onClick={() => handleRejectSample(sample.id)}
                            className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-xs"
                          >
                            Reject
                          </button>
                        </>
                      )}
                      {sample.status === 'RECEIVED' && (
                        <button
                          onClick={() => handleRejectSample(sample.id)}
                          className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-xs"
                        >
                          Reject
                        </button>
                      )}
                      {sample.status === 'REJECTED' && (
                        <span className="text-gray-400 text-xs">No actions available</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Summary */}
          <div className="mt-4 text-sm text-gray-600">
            Showing {filteredSamples.length} sample{filteredSamples.length !== 1 ? 's' : ''}
          </div>
        </>
      )}
    </div>
  )
}
