import { useState, useEffect } from 'react'
import { limsTestService } from '../../services/lims'
import { Modal } from '../../components/Modal'
import type { LIMSTest, LIMSTestFormData } from '../../types'

// Helper function to format currency values
function formatCurrency(value: number | string): string {
  const numValue = typeof value === 'number' ? value : parseFloat(value || '0')
  return numValue.toFixed(2)
}

interface TestFormProps {
  test?: LIMSTest | null
  onSave: () => void
  onCancel: () => void
}

function TestForm({ test, onSave, onCancel }: TestFormProps) {
  const [formData, setFormData] = useState<LIMSTestFormData>({
    code: '',
    name: '',
    short_name: '',
    test_type: 'Single',
    department: '',
    specimen_type: '',
    container_type: '',
    result_scale: '',
    default_method: '',
    default_tat_minutes: 0,
    default_print_group: '',
    default_report_template: '',
    default_printer_code: '',
    billing_code: '',
    default_charge: 0,
    external_code_type: '',
    external_code_value: '',
    active: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    if (test) {
      setFormData({
        code: test.code,
        name: test.name,
        short_name: test.short_name || '',
        test_type: test.test_type,
        department: test.department || '',
        specimen_type: test.specimen_type || '',
        container_type: test.container_type || '',
        result_scale: test.result_scale || '',
        default_method: test.default_method || '',
        default_tat_minutes: test.default_tat_minutes,
        default_print_group: test.default_print_group || '',
        default_report_template: test.default_report_template || '',
        default_printer_code: test.default_printer_code || '',
        billing_code: test.billing_code || '',
        default_charge: test.default_charge,
        external_code_type: test.external_code_type || '',
        external_code_value: test.external_code_value || '',
        active: test.active,
      })
    }
  }, [test])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (test) {
        await limsTestService.update(test.id, formData)
      } else {
        await limsTestService.create(formData)
      }
      onSave()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save test')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    setFormData(prev => ({
      ...prev,
      [name]:
        type === 'checkbox'
          ? checked
          : type === 'number'
            ? value === ''
              ? 0
              : parseFloat(value)
            : value,
    }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Test Code *
          </label>
          <input
            type="text"
            name="code"
            value={formData.code}
            onChange={handleChange}
            required
            disabled={!!test}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 uppercase"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Test Name *
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Short Name
          </label>
          <input
            type="text"
            name="short_name"
            value={formData.short_name}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Test Type *
          </label>
          <select
            name="test_type"
            value={formData.test_type}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="Single">Single</option>
            <option value="Profile">Profile</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Department
          </label>
          <input
            type="text"
            name="department"
            value={formData.department}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Specimen Type
          </label>
          <input
            type="text"
            name="specimen_type"
            value={formData.specimen_type}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Default Charge (PKR) *
          </label>
          <input
            type="number"
            name="default_charge"
            value={formData.default_charge}
            onChange={handleChange}
            required
            min="0"
            step="0.01"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            TAT (minutes) *
          </label>
          <input
            type="number"
            name="default_tat_minutes"
            value={formData.default_tat_minutes}
            onChange={handleChange}
            required
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          name="active"
          id="active"
          checked={formData.active}
          onChange={handleChange}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="active" className="ml-2 text-sm text-gray-700">
          Active
        </label>
      </div>

      <div className="flex justify-end space-x-3 pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Saving...' : test ? 'Update Test' : 'Create Test'}
        </button>
      </div>
    </form>
  )
}

export function TestsPage() {
  const [tests, setTests] = useState<LIMSTest[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [selectedTest, setSelectedTest] = useState<LIMSTest | null>(null)
  const [error, setError] = useState<string>('')

  const fetchTests = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await limsTestService.getAll()
      setTests(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tests')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTests()
  }, [])

  const handleAddTest = () => {
    setSelectedTest(null)
    setShowModal(true)
  }

  const handleEditTest = (test: LIMSTest) => {
    setSelectedTest(test)
    setShowModal(true)
  }

  const handleDeleteTest = async (test: LIMSTest) => {
    if (!confirm(`Are you sure you want to delete ${test.name}?`)) {
      return
    }

    try {
      await limsTestService.delete(test.id)
      await fetchTests()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete test')
    }
  }

  const handleSaveSuccess = async () => {
    setShowModal(false)
    setSelectedTest(null)
    await fetchTests()
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Tests Management</h1>
          <p className="text-gray-600 mt-1">
            Manage LIMS test definitions and configurations
          </p>
        </div>
        <button
          onClick={handleAddTest}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Add Test
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Loading tests...</p>
        </div>
      ) : tests.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No tests found
          </h3>
          <p className="text-gray-500 mb-6">
            Get started by adding your first test definition.
          </p>
          <button
            onClick={handleAddTest}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Test
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Code
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Charge
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tests.map(test => (
                <tr key={test.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {test.code}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">{test.name}</div>
                    {test.short_name && (
                      <div className="text-xs text-gray-500">
                        {test.short_name}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {test.test_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {test.department || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    Rs. {formatCurrency(test.default_charge)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs font-semibold rounded-full ${
                        test.active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {test.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleEditTest(test)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteTest(test)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={selectedTest ? 'Edit Test' : 'Add New Test'}
      >
        <TestForm
          test={selectedTest}
          onSave={handleSaveSuccess}
          onCancel={() => setShowModal(false)}
        />
      </Modal>
    </div>
  )
}
