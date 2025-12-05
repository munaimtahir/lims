import { useState, useEffect } from 'react'
import { parameterService } from '../../services/lims'
import { Modal } from '../../components/Modal'
import type { Parameter, ParameterFormData } from '../../types'

interface ParameterFormProps {
  parameter?: Parameter | null
  onSave: () => void
  onCancel: () => void
}

function ParameterForm({ parameter, onSave, onCancel }: ParameterFormProps) {
  const [formData, setFormData] = useState<ParameterFormData>({
    code: '',
    name: '',
    short_name: '',
    unit: '',
    data_type: 'Numeric',
    editor_type: 'Plain',
    decimal_places: 2,
    allowed_values: '',
    is_calculated: false,
    calculation_formula: '',
    flag_direction: 'Both',
    has_quick_text: false,
    external_code_type: '',
    external_code_value: '',
    active: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    if (parameter) {
      setFormData({
        code: parameter.code,
        name: parameter.name,
        short_name: parameter.short_name || '',
        unit: parameter.unit || '',
        data_type: parameter.data_type,
        editor_type: parameter.editor_type,
        decimal_places: parameter.decimal_places ?? 2,
        allowed_values: parameter.allowed_values || '',
        is_calculated: parameter.is_calculated,
        calculation_formula: parameter.calculation_formula || '',
        flag_direction: parameter.flag_direction,
        has_quick_text: parameter.has_quick_text,
        external_code_type: parameter.external_code_type || '',
        external_code_value: parameter.external_code_value || '',
        active: parameter.active,
      })
    }
  }, [parameter])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (parameter) {
        await parameterService.update(parameter.id, formData)
      } else {
        await parameterService.create(formData)
      }
      onSave()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save parameter')
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
    let fieldValue: string | number | boolean | null
    if (type === 'checkbox') {
      fieldValue = checked
    } else if (type === 'number') {
      fieldValue = value === '' ? null : parseFloat(value)
    } else {
      fieldValue = value
    }
    
    setFormData(prev => ({
      ...prev,
      [name]: fieldValue,
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
            Parameter Code *
          </label>
          <input
            type="text"
            name="code"
            value={formData.code}
            onChange={handleChange}
            required
            disabled={!!parameter}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 uppercase"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Parameter Name *
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

      <div className="grid grid-cols-3 gap-4">
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
            Unit
          </label>
          <input
            type="text"
            name="unit"
            value={formData.unit}
            onChange={handleChange}
            placeholder="e.g., mg/dL, %"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Decimal Places
          </label>
          <input
            type="number"
            name="decimal_places"
            value={formData.decimal_places ?? ''}
            onChange={handleChange}
            min="0"
            max="4"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Data Type *
          </label>
          <select
            name="data_type"
            value={formData.data_type}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="Numeric">Numeric</option>
            <option value="Text">Text</option>
            <option value="Option">Option</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Editor Type *
          </label>
          <select
            name="editor_type"
            value={formData.editor_type}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="Plain">Plain</option>
            <option value="RichText">Rich Text</option>
            <option value="Dropdown">Dropdown</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Flag Direction *
          </label>
          <select
            name="flag_direction"
            value={formData.flag_direction}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="Both">Both</option>
            <option value="High">High</option>
            <option value="Low">Low</option>
            <option value="None">None</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center space-x-6">
          <div className="flex items-center">
            <input
              type="checkbox"
              name="is_calculated"
              id="is_calculated"
              checked={formData.is_calculated}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label
              htmlFor="is_calculated"
              className="ml-2 text-sm text-gray-700"
            >
              Calculated
            </label>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              name="has_quick_text"
              id="has_quick_text"
              checked={formData.has_quick_text}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label
              htmlFor="has_quick_text"
              className="ml-2 text-sm text-gray-700"
            >
              Has Quick Text
            </label>
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
        </div>
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
          {loading
            ? 'Saving...'
            : parameter
              ? 'Update Parameter'
              : 'Create Parameter'}
        </button>
      </div>
    </form>
  )
}

export function ParametersPage() {
  const [parameters, setParameters] = useState<Parameter[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [selectedParameter, setSelectedParameter] = useState<Parameter | null>(
    null
  )
  const [error, setError] = useState<string>('')

  const fetchParameters = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await parameterService.getAll()
      setParameters(data)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch parameters'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchParameters()
  }, [])

  const handleAddParameter = () => {
    setSelectedParameter(null)
    setShowModal(true)
  }

  const handleEditParameter = (parameter: Parameter) => {
    setSelectedParameter(parameter)
    setShowModal(true)
  }

  const handleDeleteParameter = async (parameter: Parameter) => {
    if (!confirm(`Are you sure you want to delete ${parameter.name}?`)) {
      return
    }

    try {
      await parameterService.delete(parameter.id)
      await fetchParameters()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to delete parameter'
      )
    }
  }

  const handleSaveSuccess = async () => {
    setShowModal(false)
    setSelectedParameter(null)
    await fetchParameters()
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">
            Parameters Management
          </h1>
          <p className="text-gray-600 mt-1">
            Manage test parameters and analytes
          </p>
        </div>
        <button
          onClick={handleAddParameter}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Add Parameter
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
          <p className="mt-2 text-gray-600">Loading parameters...</p>
        </div>
      ) : parameters.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No parameters found
          </h3>
          <p className="text-gray-500 mb-6">
            Get started by adding your first parameter definition.
          </p>
          <button
            onClick={handleAddParameter}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Parameter
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
                  Unit
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Data Type
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
              {parameters.map(parameter => (
                <tr key={parameter.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {parameter.code}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">
                      {parameter.name}
                    </div>
                    {parameter.short_name && (
                      <div className="text-xs text-gray-500">
                        {parameter.short_name}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {parameter.unit || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {parameter.data_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs font-semibold rounded-full ${
                        parameter.active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {parameter.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleEditParameter(parameter)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteParameter(parameter)}
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
        title={selectedParameter ? 'Edit Parameter' : 'Add New Parameter'}
      >
        <ParameterForm
          parameter={selectedParameter}
          onSave={handleSaveSuccess}
          onCancel={() => setShowModal(false)}
        />
      </Modal>
    </div>
  )
}
