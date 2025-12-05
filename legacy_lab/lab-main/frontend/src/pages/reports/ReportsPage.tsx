import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { reportService } from '../../services/reports'
import { orderService } from '../../services/orders'
import type { Report, Order } from '../../types'
import { ROUTES } from '../../utils/constants'

export function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const loadData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [allReports, allOrders] = await Promise.all([
        reportService.getAll(),
        orderService.getAll(),
      ])
      setReports(allReports)
      // Filter orders that have published results
      setOrders(allOrders.filter((order) => order.status === 'PUBLISHED'))
    } catch (err) {
      console.error('Failed to load data:', err)
      setError('Failed to load reports and orders. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleGenerateReport = async () => {
    if (!selectedOrderId) {
      setError('Please select an order to generate a report')
      return
    }

    setIsGenerating(true)
    setError(null)
    try {
      await reportService.generate(selectedOrderId)
      setSuccessMessage('Report generated successfully')
      setTimeout(() => setSuccessMessage(null), 3000)
      setSelectedOrderId(null)
      await loadData()
    } catch (err) {
      console.error('Failed to generate report:', err)
      setError(
        'Failed to generate report. Ensure all results are published for this order.'
      )
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownloadReport = (reportId: number) => {
    const downloadUrl = reportService.getDownloadUrl(reportId)
    window.open(downloadUrl, '_blank')
  }

  const formatDateTime = (dateString: string) => {
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
        Reports Management
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

      {/* Generate Report Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">
          Generate New Report
        </h2>
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Order (Published Orders Only)
            </label>
            <select
              value={selectedOrderId || ''}
              onChange={(e) =>
                setSelectedOrderId(
                  e.target.value ? parseInt(e.target.value) : null
                )
              }
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Select an Order --</option>
              {orders.map((order) => (
                <option key={order.id} value={order.id}>
                  Order #{order.order_no} - {order.patient.full_name} (
                  {order.items.length} tests)
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleGenerateReport}
            disabled={!selectedOrderId || isGenerating}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isGenerating ? 'Generating...' : 'Generate Report'}
          </button>
        </div>
        {orders.length === 0 && !isLoading && (
          <p className="mt-3 text-sm text-gray-500">
            No orders with published results available for report generation.
          </p>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading reports...</p>
        </div>
      )}

      {/* Reports List */}
      {!isLoading && reports.length === 0 && (
        <div className="bg-gray-50 border border-gray-200 text-gray-600 px-4 py-12 rounded-lg text-center">
          No reports generated yet. Generate your first report above.
        </div>
      )}

      {!isLoading && reports.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800">
              Generated Reports
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Report ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Order No
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Patient
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Generated At
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Generated By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reports.map((report) => (
                  <tr key={report.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{report.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {report.order.order_no}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {report.order.patient.full_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatDateTime(report.generated_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {report.generated_by?.username || 'System'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      <button
                        onClick={() => handleDownloadReport(report.id)}
                        className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-xs font-medium"
                      >
                        Download PDF
                      </button>
                      <Link
                        to={ROUTES.LAB_ORDER_DETAIL(report.order.id)}
                        className="inline-block px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 text-xs font-medium"
                      >
                        View Order
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Summary */}
      {!isLoading && reports.length > 0 && (
        <div className="mt-4 text-sm text-gray-600">
          Total: {reports.length} report{reports.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}
