import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { orderService } from '../../services/orders'
import { sampleService } from '../../services/samples'
import { resultService } from '../../services/results'
import { reportService } from '../../services/reports'
import { catalogService } from '../../services/catalog'
import type { Order, Sample, Result, Report } from '../../types'
import { ROUTES, COLORS } from '../../utils/constants'
import { formatDateTime, formatCurrency } from '../../utils/validators'
import { useAuth } from '../../hooks/useAuth'
import { Modal } from '../../components/Modal'
import { Toast } from '../../components/Toast'

type TabType = 'summary' | 'samples' | 'results' | 'report'

type ToastType = {
  message: string
  type: 'success' | 'error' | 'info'
} | null

export function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()

  const [order, setOrder] = useState<Order | null>(null)
  const [samples, setSamples] = useState<Sample[]>([])
  const [results, setResults] = useState<Result[]>([])
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('summary')
  const [toast, setToast] = useState<ToastType>(null)

  // Rejection modal state
  const [rejectModal, setRejectModal] = useState<{
    isOpen: boolean
    sampleId: number | null
  }>({ isOpen: false, sampleId: null })
  const [rejectionReason, setRejectionReason] = useState('')

  // Edit tests modal state
  const [editTestsModal, setEditTestsModal] = useState(false)
  const [availableTests, setAvailableTests] = useState<
    Array<{ id: number; name: string; code: string; price: number }>
  >([])
  const [selectedTestsToAdd, setSelectedTestsToAdd] = useState<number[]>([])
  const [testsToRemove, setTestsToRemove] = useState<number[]>([])

  // Results entry form state
  const [resultFormData, setResultFormData] = useState<
    Record<
      number,
      {
        value: string
        unit: string
        flags: string
        notes: string
      }
    >
  >({})

  useEffect(() => {
    if (id) {
      fetchOrder(Number(id))
    }
  }, [id])

  useEffect(() => {
    if (order) {
      fetchSamples()
      fetchResults()
      fetchReports()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [order])

  const fetchOrder = async (orderId: number) => {
    setLoading(true)
    try {
      const data = await orderService.getById(orderId)
      setOrder(data)
    } catch (error) {
      console.error('Failed to fetch order:', error)
      setToast({ message: 'Failed to load order', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const fetchSamples = async () => {
    try {
      const allSamples = await sampleService.getAll()
      const orderItemIds = order?.items.map(item => item.id) || []
      const filteredSamples = allSamples.filter(s =>
        orderItemIds.includes(s.order_item)
      )
      setSamples(filteredSamples)
    } catch (error) {
      console.error('Failed to fetch samples:', error)
    }
  }

  const fetchResults = async () => {
    try {
      const allResults = await resultService.getAll()
      const orderItemIds = order?.items.map(item => item.id) || []
      const filteredResults = allResults.filter(r =>
        orderItemIds.includes(r.order_item)
      )
      setResults(filteredResults)

      // Initialize form data with existing results
      const formData: Record<
        number,
        {
          value: string
          unit: string
          flags: string
          notes: string
        }
      > = {}
      filteredResults.forEach(result => {
        formData[result.order_item] = {
          value: result.value || '',
          unit: result.unit || '',
          flags: result.flags || '',
          notes: result.notes || '',
        }
      })
      setResultFormData(formData)
    } catch (error) {
      console.error('Failed to fetch results:', error)
    }
  }

  const fetchReports = async () => {
    try {
      const allReports = await reportService.getAll()
      const orderReports = allReports.filter(r => r.order.id === order?.id)
      setReports(orderReports)
    } catch (error) {
      console.error('Failed to fetch reports:', error)
    }
  }

  const handleCollectSample = async (sampleId: number) => {
    setActionLoading(`collect-${sampleId}`)
    try {
      await sampleService.collect(sampleId)
      setToast({ message: 'Sample collected successfully', type: 'success' })
      await fetchSamples()
    } catch (err) {
      setToast({
        message:
          err instanceof Error ? err.message : 'Failed to collect sample',
        type: 'error',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleReceiveSample = async (sampleId: number) => {
    setActionLoading(`receive-${sampleId}`)
    try {
      await sampleService.receive(sampleId)
      setToast({ message: 'Sample received successfully', type: 'success' })
      await fetchSamples()
    } catch (err) {
      setToast({
        message:
          err instanceof Error ? err.message : 'Failed to receive sample',
        type: 'error',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleRejectSample = async () => {
    if (!rejectModal.sampleId) {
      // This should not happen in normal operation
      console.error('No sample ID provided for rejection')
      setRejectModal({ isOpen: false, sampleId: null })
      return
    }

    if (!rejectionReason.trim()) {
      setToast({ message: 'Please enter a rejection reason', type: 'error' })
      return
    }

    setActionLoading(`reject-${rejectModal.sampleId}`)
    try {
      await sampleService.reject(rejectModal.sampleId, rejectionReason)
      setToast({ message: 'Sample rejected successfully', type: 'success' })
      setRejectModal({ isOpen: false, sampleId: null })
      setRejectionReason('')
      await fetchSamples()
    } catch (err) {
      setToast({
        message: err instanceof Error ? err.message : 'Failed to reject sample',
        type: 'error',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleEnterResult = async (resultId: number, orderItemId: number) => {
    setActionLoading(`enter-${resultId}`)
    try {
      const formData = resultFormData[orderItemId]
      if (!formData?.value) {
        setToast({ message: 'Please enter a result value', type: 'error' })
        setActionLoading(null)
        return
      }

      await resultService.enter(resultId, {
        value: formData.value,
        unit: formData.unit,
        flag: formData.flags as
          | 'normal'
          | 'high'
          | 'low'
          | 'abnormal'
          | undefined,
        notes: formData.notes,
      })
      setToast({ message: 'Result entered successfully', type: 'success' })
      await fetchResults()
    } catch (err) {
      setToast({
        message: err instanceof Error ? err.message : 'Failed to enter result',
        type: 'error',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleVerifyResult = async (resultId: number) => {
    setActionLoading(`verify-${resultId}`)
    try {
      await resultService.verify(resultId)
      setToast({ message: 'Result verified successfully', type: 'success' })
      await fetchResults()
    } catch (err) {
      setToast({
        message: err instanceof Error ? err.message : 'Failed to verify result',
        type: 'error',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handlePublishResult = async (resultId: number) => {
    setActionLoading(`publish-${resultId}`)
    try {
      await resultService.publish(resultId)
      setToast({ message: 'Result published successfully', type: 'success' })
      await fetchResults()
    } catch (err) {
      setToast({
        message:
          err instanceof Error ? err.message : 'Failed to publish result',
        type: 'error',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleGenerateReport = async () => {
    if (!order) return
    setActionLoading('generate-report')
    try {
      await reportService.generate(order.id)
      setToast({ message: 'Report generated successfully', type: 'success' })
      await fetchReports()
    } catch (err) {
      setToast({
        message:
          err instanceof Error ? err.message : 'Failed to generate report',
        type: 'error',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleCancelOrder = async () => {
    if (!order) return

    // Confirm cancellation
    if (
      !window.confirm(
        'Are you sure you want to cancel this order? This action cannot be undone.'
      )
    ) {
      return
    }

    setActionLoading('cancel-order')
    try {
      await orderService.cancel(order.id)
      setToast({ message: 'Order cancelled successfully', type: 'success' })
      await fetchOrder(order.id)
    } catch (err) {
      setToast({
        message: err instanceof Error ? err.message : 'Failed to cancel order',
        type: 'error',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleOpenEditTestsModal = async () => {
    try {
      const tests = await catalogService.getAll()
      setAvailableTests(tests)
      setEditTestsModal(true)
      setSelectedTestsToAdd([])
      setTestsToRemove([])
    } catch {
      setToast({
        message: 'Failed to load test catalog',
        type: 'error',
      })
    }
  }

  const handleEditTests = async () => {
    if (!order) return

    // Validate at least one change
    if (selectedTestsToAdd.length === 0 && testsToRemove.length === 0) {
      setToast({
        message: 'Please select tests to add or remove',
        type: 'error',
      })
      return
    }

    setActionLoading('edit-tests')
    try {
      await orderService.editTests(order.id, {
        tests_to_add:
          selectedTestsToAdd.length > 0 ? selectedTestsToAdd : undefined,
        tests_to_remove: testsToRemove.length > 0 ? testsToRemove : undefined,
      })
      setToast({ message: 'Order tests updated successfully', type: 'success' })
      setEditTestsModal(false)
      await fetchOrder(order.id)
    } catch (err) {
      setToast({
        message:
          err instanceof Error ? err.message : 'Failed to edit order tests',
        type: 'error',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleToggleTestToRemove = (testId: number) => {
    setTestsToRemove(prev =>
      prev.includes(testId)
        ? prev.filter(id => id !== testId)
        : [...prev, testId]
    )
  }

  const handleToggleTestToAdd = (testId: number) => {
    setSelectedTestsToAdd(prev =>
      prev.includes(testId)
        ? prev.filter(id => id !== testId)
        : [...prev, testId]
    )
  }

  const getStatusColor = (status: string) => {
    return (
      COLORS.status[status as keyof typeof COLORS.status] ||
      'bg-gray-100 text-gray-800'
    )
  }

  const getSampleForItem = (orderItemId: number) => {
    return samples.find(s => s.order_item === orderItemId)
  }

  const getResultForItem = (orderItemId: number) => {
    return results.find(r => r.order_item === orderItemId)
  }

  const canCollectSamples = user && ['ADMIN', 'PHLEBOTOMY'].includes(user.role)
  const canReceiveSamples =
    user && ['ADMIN', 'TECHNOLOGIST', 'PATHOLOGIST'].includes(user.role)
  const canEnterResults = user && ['ADMIN', 'TECHNOLOGIST'].includes(user.role)
  const canVerifyResults = user && ['ADMIN', 'PATHOLOGIST'].includes(user.role)
  const canGenerateReports =
    user && ['ADMIN', 'PATHOLOGIST'].includes(user.role)
  const canCancelOrder = user && ['ADMIN', 'RECEPTION'].includes(user.role)

  // Can only cancel if order is NEW and no samples collected
  const canActuallyCancelOrder =
    canCancelOrder &&
    order?.status === 'NEW' &&
    samples.every(s => s.status === 'PENDING')

  // Can only edit tests if order is not cancelled, no samples exist, and no results exist
  const canEditTests =
    canCancelOrder &&
    order?.status !== 'CANCELLED' &&
    samples.length === 0 &&
    results.length === 0

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
        <p className="mt-2 text-gray-600">Loading order...</p>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Order not found</p>
        <button
          onClick={() => navigate(ROUTES.LAB_WORKLIST)}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Back to Worklist
        </button>
      </div>
    )
  }

  return (
    <div>
      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Rejection Modal */}
      <Modal
        isOpen={rejectModal.isOpen}
        onClose={() => {
          setRejectModal({ isOpen: false, sampleId: null })
          setRejectionReason('')
        }}
        title="Reject Sample"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Please provide a reason for rejecting this sample:
          </p>
          <textarea
            value={rejectionReason}
            onChange={e => setRejectionReason(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="E.g., Hemolyzed sample, Insufficient volume, etc."
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={() => {
                setRejectModal({ isOpen: false, sampleId: null })
                setRejectionReason('')
              }}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleRejectSample}
              disabled={
                !rejectionReason.trim() ||
                actionLoading === `reject-${rejectModal.sampleId}`
              }
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              {actionLoading === `reject-${rejectModal.sampleId}`
                ? 'Rejecting...'
                : 'Reject Sample'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Edit Tests Modal */}
      <Modal
        isOpen={editTestsModal}
        onClose={() => setEditTestsModal(false)}
        title="Edit Order Tests"
      >
        <div className="space-y-4">
          {/* Current Tests */}
          <div>
            <h3 className="font-semibold mb-2">Current Tests</h3>
            <div className="space-y-2">
              {order?.items.map(item => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-2 border rounded"
                >
                  <div>
                    <p className="font-medium">{item.test.name}</p>
                    <p className="text-sm text-gray-600">
                      {item.test.code} -{' '}
                      {formatCurrency(item.test.price || 0)}
                    </p>
                  </div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={testsToRemove.includes(item.test.id)}
                      onChange={() => handleToggleTestToRemove(item.test.id)}
                      className="rounded"
                    />
                    <span className="text-sm text-red-600">Remove</span>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Available Tests to Add */}
          <div>
            <h3 className="font-semibold mb-2">Available Tests to Add</h3>
            <div className="max-h-60 overflow-y-auto space-y-2">
              {availableTests
                .filter(
                  test => !order?.items.some(item => item.test.id === test.id)
                )
                .map(test => (
                  <div
                    key={test.id}
                    className="flex items-center justify-between p-2 border rounded hover:bg-gray-50"
                  >
                    <div>
                      <p className="font-medium">{test.name}</p>
                      <p className="text-sm text-gray-600">
                        {test.code} - {formatCurrency(test.price)}
                      </p>
                    </div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedTestsToAdd.includes(test.id)}
                        onChange={() => handleToggleTestToAdd(test.id)}
                        className="rounded"
                      />
                      <span className="text-sm text-green-600">Add</span>
                    </label>
                  </div>
                ))}
            </div>
          </div>

          {/* Summary */}
          {(selectedTestsToAdd.length > 0 || testsToRemove.length > 0) && (
            <div className="p-3 bg-blue-50 rounded border border-blue-200">
              <p className="text-sm font-medium text-blue-800">Summary:</p>
              {selectedTestsToAdd.length > 0 && (
                <p className="text-sm text-blue-700">
                  ➕ Adding {selectedTestsToAdd.length} test(s)
                </p>
              )}
              {testsToRemove.length > 0 && (
                <p className="text-sm text-blue-700">
                  ➖ Removing {testsToRemove.length} test(s)
                </p>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col-reverse sm:flex-row gap-2 pt-4">
            <button
              onClick={() => setEditTestsModal(false)}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 w-full sm:w-auto"
            >
              Cancel
            </button>
            <button
              onClick={handleEditTests}
              disabled={actionLoading === 'edit-tests'}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 w-full sm:w-auto"
            >
              {actionLoading === 'edit-tests' ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-800">
            Order Detail
          </h1>
          <p className="text-gray-600">{order.order_no}</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          {canEditTests && (
            <button
              onClick={handleOpenEditTestsModal}
              disabled={actionLoading === 'edit-tests'}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm sm:text-base"
            >
              {actionLoading === 'edit-tests' ? 'Editing...' : 'Edit Tests'}
            </button>
          )}
          {canActuallyCancelOrder && (
            <button
              onClick={handleCancelOrder}
              disabled={actionLoading === 'cancel-order'}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 text-sm sm:text-base"
            >
              {actionLoading === 'cancel-order'
                ? 'Cancelling...'
                : 'Cancel Order'}
            </button>
          )}
          <button
            onClick={() => navigate(ROUTES.LAB_WORKLIST)}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 w-full sm:w-auto"
          >
            Back to Worklist
          </button>
        </div>
      </div>

      {/* Status Badge and Policy Info */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center">
        <span
          className={`inline-block px-4 py-2 rounded-lg text-sm font-medium ${getStatusColor(order.status)}`}
        >
          Status: {order.status}
        </span>
        {order.status !== 'NEW' && (
          <div className="text-sm text-gray-600 bg-blue-50 px-3 py-2 rounded border border-blue-200">
            ℹ️ Orders cannot be edited once sample collection has started
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px overflow-x-auto">
            <button
              onClick={() => setActiveTab('summary')}
              className={`px-4 sm:px-6 py-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === 'summary'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
              }`}
            >
              Summary
            </button>
            <button
              onClick={() => setActiveTab('samples')}
              className={`px-4 sm:px-6 py-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === 'samples'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
              }`}
            >
              Samples
            </button>
            <button
              onClick={() => setActiveTab('results')}
              className={`px-4 sm:px-6 py-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === 'results'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
              }`}
            >
              Results
            </button>
            <button
              onClick={() => setActiveTab('report')}
              className={`px-4 sm:px-6 py-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === 'report'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
              }`}
            >
              Report
            </button>
          </nav>
        </div>

        <div className="p-4 sm:p-6">
          {/* Summary Tab */}
          {activeTab === 'summary' && (
            <div className="space-y-6">
              {/* Patient Info */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  Patient Information
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Name:</span>
                    <p className="font-medium">{order.patient.full_name}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">MRN:</span>
                    <p className="font-medium">{order.patient.mrn}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Gender:</span>
                    <p className="font-medium">
                      {order.patient.sex === 'M'
                        ? 'Male'
                        : order.patient.sex === 'F'
                          ? 'Female'
                          : 'Other'}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-600">Age:</span>
                    <p className="font-medium">
                      {order.patient.age_years !== undefined && order.patient.age_years !== null
                        ? `${order.patient.age_years} years`
                        : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-600">Phone:</span>
                    <p className="font-medium">{order.patient.phone}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">CNIC:</span>
                    <p className="font-medium">{order.patient.cnic}</p>
                  </div>
                </div>
              </div>

              {/* Order Info */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  Order Information
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Order Number:</span>
                    <p className="font-medium">{order.order_no}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Created:</span>
                    <p className="font-medium">
                      {formatDateTime(order.created_at)}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-600">Created By:</span>
                    <p className="font-medium">{order.created_by?.username || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Status:</span>
                    <p className="font-medium">{order.status}</p>
                  </div>
                </div>
              </div>

              {/* Test Items */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  Ordered Tests
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">
                          Test Name
                        </th>
                        <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">
                          Code
                        </th>
                        <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">
                          Specimen
                        </th>
                        <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">
                          Price
                        </th>
                        <th className="text-center py-2 px-3 text-sm font-medium text-gray-700">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {order.items.map(item => (
                        <tr key={item.id} className="border-b border-gray-100">
                          <td className="py-2 px-3">{item.test.name}</td>
                          <td className="py-2 px-3 text-sm text-gray-600">
                            {item.test.code}
                          </td>
                          <td className="py-2 px-3 text-sm text-gray-600">
                            {item.test.sample_type}
                          </td>
                          <td className="py-2 px-3 text-right font-medium">
                            {formatCurrency(item.test.price)}
                          </td>
                          <td className="py-2 px-3 text-center">
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(item.status)}`}
                            >
                              {item.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Billing */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  Billing
                </h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex justify-between mb-2">
                    <span>Total Amount:</span>
                    <span className="font-medium">
                      {formatCurrency(order.items.reduce((sum, item) => sum + Number(item.test.price || 0), 0))}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    Detailed billing information coming soon
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Samples Tab */}
          {activeTab === 'samples' && (
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Sample Management
              </h3>

              <div className="space-y-4">
                {order.items.map(item => {
                  const sample = getSampleForItem(item.id)
                  return (
                    <div
                      key={item.id}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h4 className="font-medium text-gray-900">
                            {item.test.name}
                          </h4>
                          <p className="text-sm text-gray-600">
                            Sample Type: {item.test.sample_type}
                          </p>
                        </div>
                        {sample && (
                          <span
                            className={`px-3 py-1 rounded-lg text-sm font-medium ${getStatusColor(sample.status)}`}
                          >
                            {sample.status}
                          </span>
                        )}
                      </div>

                      {sample ? (
                        <div className="space-y-2">
                          <div className="text-sm">
                            <span className="text-gray-600">Barcode: </span>
                            <span className="font-mono font-medium">
                              {sample.barcode}
                            </span>
                          </div>

                          {sample.collected_at && (
                            <div className="text-sm text-gray-600">
                              Collected: {formatDateTime(sample.collected_at)}
                            </div>
                          )}

                          {sample.received_at && (
                            <div className="text-sm text-gray-600">
                              Received: {formatDateTime(sample.received_at)}
                            </div>
                          )}

                          {sample.status === 'REJECTED' &&
                            sample.rejection_reason && (
                              <div className="text-sm bg-red-50 p-2 rounded border border-red-200">
                                <span className="text-red-800 font-medium">
                                  Rejection Reason:{' '}
                                </span>
                                <span className="text-red-700">
                                  {sample.rejection_reason}
                                </span>
                              </div>
                            )}

                          <div className="flex flex-wrap gap-2 mt-3">
                            {sample.status === 'PENDING' &&
                              canCollectSamples && (
                                <button
                                  onClick={() => handleCollectSample(sample.id)}
                                  disabled={
                                    actionLoading === `collect-${sample.id}`
                                  }
                                  className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 text-sm"
                                >
                                  {actionLoading === `collect-${sample.id}`
                                    ? 'Collecting...'
                                    : 'Collect Sample'}
                                </button>
                              )}

                            {sample.status === 'COLLECTED' &&
                              canReceiveSamples && (
                                <>
                                  <button
                                    onClick={() =>
                                      handleReceiveSample(sample.id)
                                    }
                                    disabled={
                                      actionLoading === `receive-${sample.id}`
                                    }
                                    className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 text-sm"
                                  >
                                    {actionLoading === `receive-${sample.id}`
                                      ? 'Receiving...'
                                      : 'Receive Sample'}
                                  </button>
                                  <button
                                    onClick={() =>
                                      setRejectModal({
                                        isOpen: true,
                                        sampleId: sample.id,
                                      })
                                    }
                                    disabled={actionLoading !== null}
                                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 text-sm"
                                  >
                                    Reject Sample
                                  </button>
                                </>
                              )}
                          </div>
                        </div>
                      ) : (
                        <div className="text-sm text-gray-500 italic">
                          No sample created yet for this test
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Results Tab */}
          {activeTab === 'results' && (
            <div>
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-4">
                <h3 className="text-lg font-semibold text-gray-800">
                  Results Entry & Verification
                </h3>
                {user && (
                  <div className="text-sm">
                    <span className="text-gray-600">Your Role: </span>
                    <span className="font-medium text-blue-600">
                      {user.role === 'TECHNOLOGIST'
                        ? 'Result Entry'
                        : user.role === 'PATHOLOGIST'
                          ? 'Verification & Publishing'
                          : user.role}
                    </span>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                {order.items.map(item => {
                  const result = getResultForItem(item.id)
                  const formData = resultFormData[item.id] || {
                    value: '',
                    unit: '',
                    flags: '',
                    notes: '',
                  }
                  const isEntered = result && result.status !== 'DRAFT'

                  return (
                    <div
                      key={item.id}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h4 className="font-medium text-gray-900">
                            {item.test.name}
                          </h4>
                          <p className="text-sm text-gray-600">
                            {result?.reference_range &&
                              `Reference: ${result.reference_range}`}
                          </p>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          {result && (
                            <>
                              <span
                                className={`px-3 py-1 rounded-lg text-sm font-medium ${getStatusColor(result.status)}`}
                              >
                                {result.status}
                              </span>
                              {result.status === 'DRAFT' && canEnterResults && (
                                <span className="text-xs text-blue-600 font-medium">
                                  → Action: Enter Result
                                </span>
                              )}
                              {result.status === 'ENTERED' &&
                                canVerifyResults && (
                                  <span className="text-xs text-green-600 font-medium">
                                    → Action: Verify
                                  </span>
                                )}
                              {result.status === 'VERIFIED' &&
                                canVerifyResults && (
                                  <span className="text-xs text-purple-600 font-medium">
                                    → Action: Publish
                                  </span>
                                )}
                              {result.status === 'PUBLISHED' && (
                                <span className="text-xs text-gray-600">
                                  ✓ Complete
                                </span>
                              )}
                            </>
                          )}
                        </div>
                      </div>

                      {result ? (
                        <div className="space-y-3">
                          {/* Workflow Position Indicator */}
                          <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-gray-600 font-medium">
                                Workflow Status:
                              </span>
                              <div className="flex items-center gap-2">
                                <span
                                  className={`px-2 py-1 rounded ${
                                    result.status === 'DRAFT'
                                      ? 'bg-gray-200 text-gray-800'
                                      : 'bg-gray-100 text-gray-500'
                                  }`}
                                >
                                  Draft
                                </span>
                                <span className="text-gray-400">→</span>
                                <span
                                  className={`px-2 py-1 rounded ${
                                    result.status === 'ENTERED'
                                      ? 'bg-blue-200 text-blue-800'
                                      : result.status === 'VERIFIED' ||
                                          result.status === 'PUBLISHED'
                                        ? 'bg-blue-100 text-blue-600'
                                        : 'bg-gray-100 text-gray-500'
                                  }`}
                                >
                                  Entered
                                </span>
                                <span className="text-gray-400">→</span>
                                <span
                                  className={`px-2 py-1 rounded ${
                                    result.status === 'VERIFIED'
                                      ? 'bg-green-200 text-green-800'
                                      : result.status === 'PUBLISHED'
                                        ? 'bg-green-100 text-green-600'
                                        : 'bg-gray-100 text-gray-500'
                                  }`}
                                >
                                  Verified
                                </span>
                                <span className="text-gray-400">→</span>
                                <span
                                  className={`px-2 py-1 rounded ${
                                    result.status === 'PUBLISHED'
                                      ? 'bg-purple-200 text-purple-800'
                                      : 'bg-gray-100 text-gray-500'
                                  }`}
                                >
                                  Published
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Result Entry Form */}
                          {!isEntered && canEnterResults && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Value *
                                </label>
                                <input
                                  type="text"
                                  value={formData.value}
                                  onChange={e =>
                                    setResultFormData({
                                      ...resultFormData,
                                      [item.id]: {
                                        ...formData,
                                        value: e.target.value,
                                      },
                                    })
                                  }
                                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="Enter result value"
                                />
                              </div>

                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Unit
                                </label>
                                <input
                                  type="text"
                                  value={formData.unit}
                                  onChange={e =>
                                    setResultFormData({
                                      ...resultFormData,
                                      [item.id]: {
                                        ...formData,
                                        unit: e.target.value,
                                      },
                                    })
                                  }
                                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="Unit"
                                />
                              </div>

                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Flag
                                </label>
                                <select
                                  value={formData.flags}
                                  onChange={e =>
                                    setResultFormData({
                                      ...resultFormData,
                                      [item.id]: {
                                        ...formData,
                                        flags: e.target.value,
                                      },
                                    })
                                  }
                                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                  <option value="">Normal</option>
                                  <option value="high">High</option>
                                  <option value="low">Low</option>
                                  <option value="abnormal">Abnormal</option>
                                </select>
                              </div>

                              <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Notes
                                </label>
                                <textarea
                                  value={formData.notes}
                                  onChange={e =>
                                    setResultFormData({
                                      ...resultFormData,
                                      [item.id]: {
                                        ...formData,
                                        notes: e.target.value,
                                      },
                                    })
                                  }
                                  rows={2}
                                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="Optional notes"
                                />
                              </div>
                            </div>
                          )}

                          {/* Message for Pathologist when result is in DRAFT */}
                          {result.status === 'DRAFT' &&
                            !canEnterResults &&
                            canVerifyResults && (
                              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                                <p className="text-sm text-yellow-800">
                                  ⏳ Waiting for technologist to enter result
                                  values
                                </p>
                              </div>
                            )}

                          {/* Display entered result */}
                          {isEntered && (
                            <div className="bg-gray-50 p-3 rounded-lg space-y-2">
                              <div className="grid grid-cols-2 gap-2 text-sm">
                                <div>
                                  <span className="text-gray-600">Value: </span>
                                  <span className="font-medium">
                                    {result.value} {result.unit}
                                  </span>
                                </div>
                                {result.flags && (
                                  <div>
                                    <span className="text-gray-600">
                                      Flag:{' '}
                                    </span>
                                    <span
                                      className={`font-medium ${
                                        result.flags === 'high' ||
                                        result.flags === 'low'
                                          ? 'text-red-600'
                                          : 'text-green-600'
                                      }`}
                                    >
                                      {result.flags}
                                    </span>
                                  </div>
                                )}
                              </div>

                              {result.notes && (
                                <div className="text-sm">
                                  <span className="text-gray-600">Notes: </span>
                                  <span>{result.notes}</span>
                                </div>
                              )}

                              {result.entered_at && (
                                <div className="text-xs text-gray-500">
                                  Entered: {formatDateTime(result.entered_at)}
                                </div>
                              )}

                              {result.verified_at && (
                                <div className="text-xs text-gray-500">
                                  Verified: {formatDateTime(result.verified_at)}
                                </div>
                              )}
                            </div>
                          )}

                          {/* Action Buttons */}
                          <div className="flex flex-wrap gap-2 mt-3 bg-gray-50 p-3 rounded-lg border border-gray-200">
                            {result.status === 'DRAFT' && canEnterResults && (
                              <button
                                onClick={() =>
                                  handleEnterResult(result.id, item.id)
                                }
                                disabled={
                                  actionLoading === `enter-${result.id}`
                                }
                                className="flex-1 sm:flex-none px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium shadow-sm"
                                aria-label="Enter result"
                              >
                                {actionLoading === `enter-${result.id}`
                                  ? 'Saving...'
                                  : 'Enter Result'}
                              </button>
                            )}

                            {result.status === 'ENTERED' &&
                              canEnterResults &&
                              !canVerifyResults && (
                                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 w-full">
                                  <p className="text-sm text-blue-800">
                                    ✓ Result entered. Waiting for pathologist to
                                    verify.
                                  </p>
                                </div>
                              )}

                            {result.status === 'ENTERED' &&
                              canVerifyResults && (
                                <button
                                  onClick={() => handleVerifyResult(result.id)}
                                  disabled={
                                    actionLoading === `verify-${result.id}`
                                  }
                                  className="flex-1 sm:flex-none px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm font-medium shadow-sm"
                                  aria-label="Verify result"
                                >
                                  {actionLoading === `verify-${result.id}`
                                    ? 'Verifying...'
                                    : 'Verify Result'}
                                </button>
                              )}

                            {result.status === 'VERIFIED' &&
                              canVerifyResults && (
                                <button
                                  onClick={() => handlePublishResult(result.id)}
                                  disabled={
                                    actionLoading === `publish-${result.id}`
                                  }
                                  className="flex-1 sm:flex-none px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 text-sm font-medium shadow-sm"
                                  aria-label="Publish result"
                                >
                                  {actionLoading === `publish-${result.id}`
                                    ? 'Publishing...'
                                    : 'Publish Result'}
                                </button>
                              )}

                            {result.status === 'PUBLISHED' && (
                              <div className="flex-1 px-4 py-2 bg-green-50 text-green-700 rounded-lg text-sm border border-green-200">
                                Result has been published
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="text-sm text-gray-500 italic">
                          No result created yet for this test
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Report Tab */}
          {activeTab === 'report' && (
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Report Generation
              </h3>

              <div className="space-y-4">
                {reports.length > 0 ? (
                  <div className="space-y-3">
                    {reports.map(report => (
                      <div
                        key={report.id}
                        className="border border-gray-200 rounded-lg p-4"
                      >
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-medium text-gray-900">
                              Report #{report.id}
                            </p>
                            <p className="text-sm text-gray-600">
                              Generated: {formatDateTime(report.generated_at)}
                            </p>
                          </div>
                          <a
                            href={reportService.getDownloadUrl(report.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                          >
                            Download PDF
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-600 mb-4">
                      No report generated yet
                    </p>
                  </div>
                )}

                {canGenerateReports && (
                  <div className="text-center pt-4 border-t">
                    <button
                      onClick={handleGenerateReport}
                      disabled={actionLoading === 'generate-report'}
                      className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {actionLoading === 'generate-report'
                        ? 'Generating...'
                        : 'Generate PDF Report'}
                    </button>
                    <p className="text-xs text-gray-500 mt-2">
                      All results must be published before generating a report
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
