import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { patientService } from '../../services/patients'
import { orderService } from '../../services/orders'
import type { Patient, Order } from '../../types'
import { ROUTES, COLORS } from '../../utils/constants'

export function PatientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [patient, setPatient] = useState<Patient | null>(null)
  const [orders, setOrders] = useState<Order[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadPatientData = async () => {
      if (!id) return

      setIsLoading(true)
      setError(null)
      try {
        // Load patient details
        const patientData = await patientService.getById(parseInt(id))
        setPatient(patientData)

        // Load patient's orders
        const allOrders = await orderService.getAll()
        const patientOrders = allOrders.filter(
          (order) => order.patient.id === parseInt(id)
        )
        setOrders(patientOrders)
      } catch (err) {
        console.error('Failed to load patient data:', err)
        setError('Failed to load patient information. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }

    loadPatientData()
  }, [id])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-gray-600">Loading patient details...</p>
      </div>
    )
  }

  if (error || !patient) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        {error || 'Patient not found'}
        <div className="mt-4">
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Patient Details</h1>
        <div className="flex gap-2">
          <Link
            to={ROUTES.LAB_NEW}
            state={{ patient }}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            New Order
          </Link>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            Back
          </button>
        </div>
      </div>

      {/* Patient Information Card */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">
          Patient Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium text-gray-500">MRN</label>
            <p className="text-gray-900 font-semibold">{patient.mrn}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Full Name</label>
            <p className="text-gray-900">{patient.full_name}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Father's Name</label>
            <p className="text-gray-900">{patient.father_name || '-'}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Gender</label>
            <p className="text-gray-900">
              {patient.sex === 'M' ? 'Male' : patient.sex === 'F' ? 'Female' : 'Other'}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Age</label>
            <p className="text-gray-900">
              {patient.age_years} years, {patient.age_months} months,{' '}
              {patient.age_days} days
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Date of Birth</label>
            <p className="text-gray-900">
              {patient.dob ? formatDate(patient.dob) : '-'}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Phone</label>
            <p className="text-gray-900">{patient.phone}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">CNIC</label>
            <p className="text-gray-900">{patient.cnic || '-'}</p>
          </div>
          <div className="md:col-span-2">
            <label className="text-sm font-medium text-gray-500">Address</label>
            <p className="text-gray-900">{patient.address || '-'}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">
              Registration Date
            </label>
            <p className="text-gray-900">{formatDate(patient.created_at)}</p>
          </div>
        </div>
      </div>

      {/* Orders History */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Order History</h2>

        {orders.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No orders found for this patient.
            <div className="mt-4">
              <Link
                to={ROUTES.LAB_NEW}
                state={{ patient }}
                className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Create First Order
              </Link>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Order ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Tests
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Priority
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {orders.map((order) => (
                  <tr key={order.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{order.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatDate(order.created_at)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {order.items?.length || 0} test(s)
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          COLORS.status[order.status as keyof typeof COLORS.status] ||
                          'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {order.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {order.priority}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <Link
                        to={ROUTES.LAB_ORDER_DETAIL(order.id)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
