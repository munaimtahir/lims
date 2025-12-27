import { useState, useEffect } from 'react'
import { referenceRangeService, parameterService } from '../../services/lims'
import { Modal } from '../../components/Modal'
import type { ReferenceRange, ReferenceRangeFormData, Parameter } from '../../types'

interface ReferenceRangeFormProps {
  referenceRange?: ReferenceRange | null
  parameters: Parameter[]
  onSave: () => void
  onCancel: () => void
}

function ReferenceRangeForm({
  referenceRange,
  parameters,
  onSave,
  onCancel,
}: ReferenceRangeFormProps) {
  const [formData, setFormData] = useState<ReferenceRangeFormData>({
    parameter: -1,
    method_code: '',
    sex: 'All',
    age_min: 0,
    age_max: 999,
    age_unit: 'Years',
    population_group: 'Adult',
    unit: '',
    normal_low: null,
    normal_high: null,
    critical_low: null,
    critical_high: null,
    reference_text: '',
    effective_from: null,
    effective_to: null,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    if (referenceRange) {
      setFormData({
        parameter: referenceRange.parameter,
        method_code: referenceRange.method_code || '',
        sex: referenceRange.sex,
        age_min: referenceRange.age_min,
        age_max: referenceRange.age_max,
        age_unit: referenceRange.age_unit,
        population_group: referenceRange.population_group,
        unit: referenceRange.unit || '',
        normal_low: referenceRange.normal_low,
        normal_high: referenceRange.normal_high,
        critical_low: referenceRange.critical_low,
        critical_high: referenceRange.critical_high,
        reference_text: referenceRange.reference_text || '',
        effective_from: referenceRange.effective_from || null,
        effective_to: referenceRange.effective_to || null,
      })
    }
  }, [referenceRange])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (formData.parameter < 0) {
      setError('Please select a parameter')
      return
    }

    setLoading(true)
    try {
      if (referenceRange) {
        await referenceRangeService.update(referenceRange.id, formData)
      } else {
        await referenceRangeService.create(formData)
      }
      onSave()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to save reference range'
      )
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
    let fieldValue: string | number | null
    if (type === 'number') {
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

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Parameter *
          {referenceRange && (
            <span className="ml-2 text-xs text-gray-500">
              (Cannot be changed after creation)
            </span>
          )}
        </label>
        <select
          name="parameter"
          value={formData.parameter}
          onChange={handleChange}
          required
          disabled={!!referenceRange}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="-1">Select a parameter</option>
          {parameters.map(param => (
            <option key={param.id} value={param.id}>
              {param.code} - {param.name} {param.unit ? `(${param.unit})` : ''}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sex *
          </label>
          <select
            name="sex"
            value={formData.sex}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="All">All</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Population Group *
          </label>
          <select
            name="population_group"
            value={formData.population_group}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="Neonate">Neonate</option>
            <option value="Pediatric">Pediatric</option>
            <option value="Adult">Adult</option>
            <option value="Elderly">Elderly</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Age Unit *
          </label>
          <select
            name="age_unit"
            value={formData.age_unit}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="Days">Days</option>
            <option value="Months">Months</option>
            <option value="Years">Years</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Age Min
          </label>
          <input
            type="number"
            name="age_min"
            value={formData.age_min}
            onChange={handleChange}
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Age Max
          </label>
          <input
            type="number"
            name="age_max"
            value={formData.age_max}
            onChange={handleChange}
            min="0"
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
            value={formData.unit || ''}
            onChange={handleChange}
            placeholder="e.g., mg/dL"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Normal Low
          </label>
          <input
            type="number"
            name="normal_low"
            value={formData.normal_low ?? ''}
            onChange={handleChange}
            step="any"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Normal High
          </label>
          <input
            type="number"
            name="normal_high"
            value={formData.normal_high ?? ''}
            onChange={handleChange}
            step="any"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Critical Low
          </label>
          <input
            type="number"
            name="critical_low"
            value={formData.critical_low ?? ''}
            onChange={handleChange}
            step="any"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Critical High
          </label>
          <input
            type="number"
            name="critical_high"
            value={formData.critical_high ?? ''}
            onChange={handleChange}
            step="any"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Reference Text
        </label>
        <textarea
          name="reference_text"
          value={formData.reference_text || ''}
          onChange={handleChange}
          rows={2}
          placeholder="e.g., Normal: 0-5.5, Borderline: 5.5-6.5, High: >6.5"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
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
            : referenceRange
              ? 'Update Reference Range'
              : 'Create Reference Range'}
        </button>
      </div>
    </form>
  )
}

export function ReferenceRangesPage() {
  const [referenceRanges, setReferenceRanges] = useState<ReferenceRange[]>([])
  const [parameters, setParameters] = useState<Parameter[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [selectedReferenceRange, setSelectedReferenceRange] =
    useState<ReferenceRange | null>(null)
  const [error, setError] = useState<string>('')
  const [selectedParameterFilter, setSelectedParameterFilter] =
    useState<string>('')

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const [rangesData, parametersData] = await Promise.all([
        referenceRangeService.getAll(),
        parameterService.getAll(true),
      ])
      setReferenceRanges(rangesData)
      setParameters(parametersData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleAddReferenceRange = () => {
    setSelectedReferenceRange(null)
    setShowModal(true)
  }

  const handleEditReferenceRange = (referenceRange: ReferenceRange) => {
    setSelectedReferenceRange(referenceRange)
    setShowModal(true)
  }

  const handleDeleteReferenceRange = async (referenceRange: ReferenceRange) => {
    if (
      !confirm(
        `Are you sure you want to delete this reference range for ${referenceRange.parameter_name}?`
      )
    ) {
      return
    }

    try {
      await referenceRangeService.delete(referenceRange.id)
      await fetchData()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to delete reference range'
      )
    }
  }

  const handleSaveSuccess = async () => {
    setShowModal(false)
    setSelectedReferenceRange(null)
    await fetchData()
  }

  const filteredReferenceRanges = selectedParameterFilter
    ? referenceRanges.filter(
        rr => rr.parameter.toString() === selectedParameterFilter
      )
    : referenceRanges

  const formatRange = (low: number | null | undefined, high: number | null | undefined) => {
    if (low != null && high != null) return `${low} - ${high}`
    if (low != null) return `≥ ${low}`
    if (high != null) return `≤ ${high}`
    return '-'
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">
            Reference Ranges Management
          </h1>
          <p className="text-gray-600 mt-1">
            Define normal and critical value ranges for parameters
          </p>
        </div>
        <button
          onClick={handleAddReferenceRange}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Add Reference Range
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="mb-4 bg-white rounded-lg shadow p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Filter by Parameter
        </label>
        <select
          value={selectedParameterFilter}
          onChange={e => setSelectedParameterFilter(e.target.value)}
          className="w-full md:w-96 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Parameters</option>
          {parameters.map(param => (
            <option key={param.id} value={param.id.toString()}>
              {param.code} - {param.name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Loading reference ranges...</p>
        </div>
      ) : filteredReferenceRanges.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No reference ranges found
          </h3>
          <p className="text-gray-500 mb-6">
            Define normal and critical ranges for test parameters.
          </p>
          <button
            onClick={handleAddReferenceRange}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Reference Range
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Parameter
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Sex / Age
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Normal Range
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Critical Range
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Unit
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredReferenceRanges.map(rr => (
                <tr key={rr.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">
                      {rr.parameter_code}
                    </div>
                    <div className="text-xs text-gray-500">
                      {rr.parameter_name}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">{rr.sex}</div>
                    <div className="text-xs text-gray-500">
                      {rr.age_min}-{rr.age_max} {rr.age_unit}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 inline-flex text-sm font-medium rounded bg-green-100 text-green-800">
                      {formatRange(rr.normal_low, rr.normal_high)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 inline-flex text-sm font-medium rounded bg-red-100 text-red-800">
                      {formatRange(rr.critical_low, rr.critical_high)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {rr.unit || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleEditReferenceRange(rr)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteReferenceRange(rr)}
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
        title={
          selectedReferenceRange
            ? 'Edit Reference Range'
            : 'Add Reference Range'
        }
      >
        <ReferenceRangeForm
          referenceRange={selectedReferenceRange}
          parameters={parameters}
          onSave={handleSaveSuccess}
          onCancel={() => setShowModal(false)}
        />
      </Modal>
    </div>
  )
}
