import { useState, useEffect } from 'react'
import { catalogService } from '../../services/catalog'
import { Modal } from '../../components/Modal'
import type { TestCatalog, TestCatalogFormData } from '../../types'

interface TestFormProps {
  test?: TestCatalog | null
  onSave: () => void
  onCancel: () => void
}

function TestForm({ test, onSave, onCancel }: TestFormProps) {
  const [formData, setFormData] = useState<TestCatalogFormData>({
    code: '',
    name: '',
    description: '',
    category: '',
    sample_type: '',
    price: 0,
    turnaround_time_hours: 24,
    is_active: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    if (test) {
      setFormData({
        code: test.code,
        name: test.name,
        description: test.description || '',
        category: test.category,
        sample_type: test.sample_type,
        price: test.price,
        turnaround_time_hours: test.turnaround_time_hours,
        is_active: test.is_active,
      })
    }
  }, [test])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (formData.price <= 0) {
      setError('Price must be greater than 0')
      return
    }

    setLoading(true)
    try {
      if (test) {
        await catalogService.update(test.id, formData)
      } else {
        await catalogService.create(formData)
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
            ? parseFloat(value) || 0
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
            placeholder="e.g., CBC, LFT"
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

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category *
          </label>
          <input
            type="text"
            name="category"
            value={formData.category}
            onChange={handleChange}
            required
            placeholder="e.g., Hematology, Chemistry"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sample Type *
          </label>
          <input
            type="text"
            name="sample_type"
            value={formData.sample_type}
            onChange={handleChange}
            required
            placeholder="e.g., Blood, Serum, Urine"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Price (PKR) *
          </label>
          <input
            type="number"
            name="price"
            value={formData.price}
            onChange={handleChange}
            required
            min="0"
            step="0.01"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Turnaround Time (hours) *
          </label>
          <input
            type="number"
            name="turnaround_time_hours"
            value={formData.turnaround_time_hours}
            onChange={handleChange}
            required
            min="1"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          name="is_active"
          id="is_active"
          checked={formData.is_active}
          onChange={handleChange}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
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

export function TestCatalogPage() {
  const [tests, setTests] = useState<TestCatalog[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [selectedTest, setSelectedTest] = useState<TestCatalog | null>(null)
  const [error, setError] = useState<string>('')

  const fetchTests = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await catalogService.getAll()
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

  const handleEditTest = (test: TestCatalog) => {
    setSelectedTest(test)
    setShowModal(true)
  }

  const handleDeleteTest = async (test: TestCatalog) => {
    if (!confirm(`Are you sure you want to delete ${test.name}?`)) {
      return
    }

    try {
      await catalogService.delete(test.id)
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
        <h1 className="text-3xl font-bold text-gray-800">Test Catalog</h1>
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
          <div className="text-gray-400 mb-4">
            <svg
              className="mx-auto h-12 w-12"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No tests in catalog
          </h3>
          <p className="text-gray-500 mb-6">
            Get started by adding your first test to the catalog.
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
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Sample
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Price
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
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {test.category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {test.sample_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    Rs. {test.price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs font-semibold rounded-full ${
                        test.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {test.is_active ? 'Active' : 'Inactive'}
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
