import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { orderService } from '../../services/orders'
import type { Order } from '../../types'
import { ROUTES, COLORS } from '../../utils/constants'
import { formatDateTime, formatCurrency } from '../../utils/validators'

export function LabWorklistPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)

  // Filter state
  const [filters, setFilters] = useState({
    fromDate: '',
    toDate: '',
    status: '',
    patientSearch: '',
  })

  useEffect(() => {
    fetchOrders()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const filterParams: Record<string, string> = {}
      if (filters.fromDate) filterParams.from_date = filters.fromDate
      if (filters.toDate) filterParams.to_date = filters.toDate
      if (filters.status) filterParams.status = filters.status
      if (filters.patientSearch) filterParams.search = filters.patientSearch

      const data = await orderService.getAll(filterParams)
      setOrders(data)
    } catch (error) {
      console.error('Failed to fetch orders:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }))
  }

  const applyFilters = () => {
    fetchOrders()
  }

  const getStatusColor = (status: string) => {
    return (
      COLORS.status[status as keyof typeof COLORS.status] ||
      'bg-gray-100 text-gray-800'
    )
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Lab Worklist</h1>

      {/* Filter Bar */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From Date
            </label>
            <input
              type="date"
              value={filters.fromDate}
              onChange={e => handleFilterChange('fromDate', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              To Date
            </label>
            <input
              type="date"
              value={filters.toDate}
              onChange={e => handleFilterChange('toDate', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filters.status}
              onChange={e => handleFilterChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="NEW">New</option>
              <option value="COLLECTED">Collected</option>
              <option value="IN_PROCESS">In Process</option>
              <option value="VERIFIED">Verified</option>
              <option value="PUBLISHED">Published</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Patient Search
            </label>
            <input
              type="text"
              value={filters.patientSearch}
              onChange={e =>
                handleFilterChange('patientSearch', e.target.value)
              }
              placeholder="Name, phone, order #"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={applyFilters}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Apply Filters
          </button>
        </div>
      </div>

      {/* Orders Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Loading orders...</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-600">
            No orders found. Try adjusting your filters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {orders.map(order => (
            <div
              key={order.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow"
            >
              {/* Card Header */}
              <div className="bg-blue-700 text-white p-4 rounded-t-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-lg">
                      {order.order_no}
                    </h3>
                    <p className="text-sm text-blue-100">
                      {order.patient.full_name}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(order.status)}`}
                  >
                    {order.status}
                  </span>
                </div>
                <div className="mt-2 text-sm text-blue-100">
                  <span>
                    {order.patient.sex === 'M'
                      ? 'Male'
                      : order.patient.sex === 'F'
                        ? 'Female'
                        : 'Other'}
                  </span>
                  {order.patient.age_years !== undefined && order.patient.age_years !== null && (
                    <span>
                      {' '}
                      • {order.patient.age_years} years
                    </span>
                  )}
                </div>
              </div>

              {/* Card Body */}
              <div className="p-4">
                <div className="text-sm text-gray-600 mb-3">
                  <p>{formatDateTime(order.created_at)}</p>
                  {order.created_by && <p>By: {order.created_by.username}</p>}
                </div>

                {/* Test Items */}
                <div className="space-y-2 mb-4">
                  {order.items.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex justify-between items-center text-sm"
                    >
                      <span className="text-gray-700">{item.test.name}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-xs ${getStatusColor(item.status)}`}
                      >
                        {item.status}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="border-t pt-3 mb-3">
                  <div className="flex justify-between text-sm font-medium">
                    <span>Total:</span>
                    <span>{formatCurrency(order.items.reduce((sum, item) => sum + Number(item.test.price || 0), 0))}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Link
                    to={ROUTES.LAB_ORDER_DETAIL(order.id)}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white text-center rounded-lg hover:bg-blue-700 text-sm"
                  >
                    Open
                  </Link>
                  <button
                    type="button"
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm"
                  >
                    Print
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
