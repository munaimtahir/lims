import { useState, useEffect } from 'react'
import {
  testParameterService,
  limsTestService,
  parameterService,
} from '../../services/lims'
import { Modal } from '../../components/Modal'
import type {
  TestParameter,
  TestParameterFormData,
  LIMSTest,
  Parameter,
} from '../../types'

interface TestParameterFormProps {
  testParameter?: TestParameter | null
  tests: LIMSTest[]
  parameters: Parameter[]
  onSave: () => void
  onCancel: () => void
}

function TestParameterForm({
  testParameter,
  tests,
  parameters,
  onSave,
  onCancel,
}: TestParameterFormProps) {
  const [formData, setFormData] = useState<TestParameterFormData>({
    test: 0,
    parameter: 0,
    display_order: 0,
    section_header: '',
    is_mandatory: true,
    show_on_report: true,
    default_reference_profile_id: '',
    delta_check_enabled: false,
    panic_low_override: null,
    panic_high_override: null,
    comment_template_id: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    if (testParameter) {
      setFormData({
        test: testParameter.test,
        parameter: testParameter.parameter,
        display_order: testParameter.display_order,
        section_header: testParameter.section_header || '',
        is_mandatory: testParameter.is_mandatory,
        show_on_report: testParameter.show_on_report,
        default_reference_profile_id:
          testParameter.default_reference_profile_id || '',
        delta_check_enabled: testParameter.delta_check_enabled,
        panic_low_override: testParameter.panic_low_override,
        panic_high_override: testParameter.panic_high_override,
        comment_template_id: testParameter.comment_template_id || '',
      })
    }
  }, [testParameter])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!formData.test || !formData.parameter) {
      setError('Please select both test and parameter')
      return
    }

    setLoading(true)
    try {
      if (testParameter) {
        await testParameterService.update(testParameter.id, formData)
      } else {
        await testParameterService.create(formData)
      }
      onSave()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to save test-parameter'
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
            Test *
          </label>
          <select
            name="test"
            value={formData.test}
            onChange={handleChange}
            required
            disabled={!!testParameter}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          >
            <option value="">Select a test</option>
            {tests.map(test => (
              <option key={test.id} value={test.id}>
                {test.code} - {test.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Parameter *
          </label>
          <select
            name="parameter"
            value={formData.parameter}
            onChange={handleChange}
            required
            disabled={!!testParameter}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          >
            <option value="">Select a parameter</option>
            {parameters.map(parameter => (
              <option key={parameter.id} value={parameter.id}>
                {parameter.code} - {parameter.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Display Order *
          </label>
          <input
            type="number"
            name="display_order"
            value={formData.display_order}
            onChange={handleChange}
            required
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Section Header
          </label>
          <input
            type="text"
            name="section_header"
            value={formData.section_header}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex items-center space-x-6">
        <div className="flex items-center">
          <input
            type="checkbox"
            name="is_mandatory"
            id="is_mandatory"
            checked={formData.is_mandatory}
            onChange={handleChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="is_mandatory" className="ml-2 text-sm text-gray-700">
            Mandatory
          </label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            name="show_on_report"
            id="show_on_report"
            checked={formData.show_on_report}
            onChange={handleChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label
            htmlFor="show_on_report"
            className="ml-2 text-sm text-gray-700"
          >
            Show on Report
          </label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            name="delta_check_enabled"
            id="delta_check_enabled"
            checked={formData.delta_check_enabled}
            onChange={handleChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label
            htmlFor="delta_check_enabled"
            className="ml-2 text-sm text-gray-700"
          >
            Delta Check
          </label>
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
          {loading ? 'Saving...' : testParameter ? 'Update' : 'Create'}
        </button>
      </div>
    </form>
  )
}

export function TestParametersPage() {
  const [testParameters, setTestParameters] = useState<TestParameter[]>([])
  const [tests, setTests] = useState<LIMSTest[]>([])
  const [parameters, setParameters] = useState<Parameter[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [selectedTestParameter, setSelectedTestParameter] =
    useState<TestParameter | null>(null)
  const [error, setError] = useState<string>('')
  const [selectedTestFilter, setSelectedTestFilter] = useState<string>('')

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const [testParamsData, testsData, parametersData] = await Promise.all([
        testParameterService.getAll(),
        limsTestService.getAll(true),
        parameterService.getAll(true),
      ])
      setTestParameters(testParamsData)
      setTests(testsData)
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

  const handleAddTestParameter = () => {
    setSelectedTestParameter(null)
    setShowModal(true)
  }

  const handleEditTestParameter = (testParameter: TestParameter) => {
    setSelectedTestParameter(testParameter)
    setShowModal(true)
  }

  const handleDeleteTestParameter = async (testParameter: TestParameter) => {
    if (
      !confirm(
        `Are you sure you want to remove this parameter from the test?`
      )
    ) {
      return
    }

    try {
      await testParameterService.delete(testParameter.id)
      await fetchData()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to delete test-parameter'
      )
    }
  }

  const handleSaveSuccess = async () => {
    setShowModal(false)
    setSelectedTestParameter(null)
    await fetchData()
  }

  const filteredTestParameters = selectedTestFilter
    ? testParameters.filter(tp => tp.test.toString() === selectedTestFilter)
    : testParameters

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">
            Test-Parameter Relationships
          </h1>
          <p className="text-gray-600 mt-1">
            Link parameters to tests and manage display order
          </p>
        </div>
        <button
          onClick={handleAddTestParameter}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Add Test-Parameter Link
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="mb-4 bg-white rounded-lg shadow p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Filter by Test
        </label>
        <select
          value={selectedTestFilter}
          onChange={e => setSelectedTestFilter(e.target.value)}
          className="w-full md:w-96 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Tests</option>
          {tests.map(test => (
            <option key={test.id} value={test.id.toString()}>
              {test.code} - {test.name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Loading test-parameters...</p>
        </div>
      ) : filteredTestParameters.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No test-parameter relationships found
          </h3>
          <p className="text-gray-500 mb-6">
            Link parameters to tests to define what gets measured.
          </p>
          <button
            onClick={handleAddTestParameter}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Test-Parameter Link
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Test
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Parameter
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Unit
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Order
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Flags
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredTestParameters.map(tp => (
                <tr key={tp.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">
                      {tp.test_code}
                    </div>
                    <div className="text-xs text-gray-500">{tp.test_name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">
                      {tp.parameter_code}
                    </div>
                    <div className="text-xs text-gray-500">
                      {tp.parameter_name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {tp.parameter_unit || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {tp.display_order}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-xs">
                    {tp.is_mandatory && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-blue-100 text-blue-800 mr-1">
                        Required
                      </span>
                    )}
                    {tp.show_on_report && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-green-100 text-green-800 mr-1">
                        Report
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleEditTestParameter(tp)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteTestParameter(tp)}
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
          selectedTestParameter
            ? 'Edit Test-Parameter'
            : 'Add Test-Parameter Link'
        }
      >
        <TestParameterForm
          testParameter={selectedTestParameter}
          tests={tests}
          parameters={parameters}
          onSave={handleSaveSuccess}
          onCancel={() => setShowModal(false)}
        />
      </Modal>
    </div>
  )
}
