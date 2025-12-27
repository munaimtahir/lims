import { useState, useEffect } from 'react'
import { terminalService } from '../../services/terminals'
import { Modal } from '../../components/Modal'
import {
  calculateTerminalUtilization,
  calculateRangeCapacity,
} from '../../utils/terminal'
import type { LabTerminal, LabTerminalFormData } from '../../types'

interface TerminalFormProps {
  terminal?: LabTerminal | null
  onSave: () => void
  onCancel: () => void
}

function TerminalForm({ terminal, onSave, onCancel }: TerminalFormProps) {
  const [formData, setFormData] = useState<LabTerminalFormData>({
    code: '',
    name: '',
    offline_range_start: 0,
    offline_range_end: 0,
    is_active: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    if (terminal) {
      setFormData({
        code: terminal.code,
        name: terminal.name,
        offline_range_start: terminal.offline_range_start,
        offline_range_end: terminal.offline_range_end,
        is_active: terminal.is_active,
      })
    }
  }, [terminal])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (formData.offline_range_start >= formData.offline_range_end) {
      setError('Start MRN must be less than End MRN')
      return
    }

    setLoading(true)
    try {
      if (terminal) {
        await terminalService.update(terminal.id, formData)
      } else {
        await terminalService.create(formData)
      }
      onSave()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save terminal')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target
    const checked = e.target.checked
    setFormData(prev => ({
      ...prev,
      [name]:
        type === 'checkbox'
          ? checked
          : type === 'number'
            ? parseInt(value) || 0
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
            Terminal Code *
          </label>
          <input
            type="text"
            name="code"
            value={formData.code}
            onChange={handleChange}
            required
            disabled={!!terminal}
            placeholder="e.g., LAB1-PC, RECEP-1"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 uppercase"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Terminal Name *
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            placeholder="e.g., Lab 1 PC"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            MRN Range Start *
          </label>
          <input
            type="number"
            name="offline_range_start"
            value={formData.offline_range_start}
            onChange={handleChange}
            required
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            MRN Range End *
          </label>
          <input
            type="number"
            name="offline_range_end"
            value={formData.offline_range_end}
            onChange={handleChange}
            required
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded p-3">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> Ensure MRN ranges do not overlap with existing
          terminals. Range: {formData.offline_range_start} -{' '}
          {formData.offline_range_end} (
          {calculateRangeCapacity(
            formData.offline_range_start,
            formData.offline_range_end
          )}{' '}
          MRNs)
        </p>
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
          {loading
            ? 'Saving...'
            : terminal
              ? 'Update Terminal'
              : 'Create Terminal'}
        </button>
      </div>
    </form>
  )
}

export function LabTerminalsPage() {
  const [terminals, setTerminals] = useState<LabTerminal[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [selectedTerminal, setSelectedTerminal] = useState<LabTerminal | null>(
    null
  )
  const [error, setError] = useState<string>('')

  const fetchTerminals = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await terminalService.getAll()
      setTerminals(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch terminals')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTerminals()
  }, [])

  const handleAddTerminal = () => {
    setSelectedTerminal(null)
    setShowModal(true)
  }

  const handleEditTerminal = (terminal: LabTerminal) => {
    setSelectedTerminal(terminal)
    setShowModal(true)
  }

  const handleDeleteTerminal = async (terminal: LabTerminal) => {
    if (!confirm(`Are you sure you want to delete ${terminal.name}?`)) {
      return
    }

    try {
      await terminalService.delete(terminal.id)
      await fetchTerminals()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete terminal')
    }
  }

  const handleSaveSuccess = async () => {
    setShowModal(false)
    setSelectedTerminal(null)
    await fetchTerminals()
  }

  const getRangeUtilization = (terminal: LabTerminal) => {
    return calculateTerminalUtilization(terminal)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Lab Terminals</h1>
        <button
          onClick={handleAddTerminal}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Add Terminal
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
          <p className="mt-2 text-gray-600">Loading terminals...</p>
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
                  MRN Range
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Current MRN
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Utilization
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
              {terminals.map(terminal => (
                <tr key={terminal.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {terminal.code}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{terminal.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {terminal.offline_range_start} -{' '}
                    {terminal.offline_range_end}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {terminal.offline_current || 'Not used'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {getRangeUtilization(terminal)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs font-semibold rounded-full ${
                        terminal.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {terminal.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleEditTerminal(terminal)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteTerminal(terminal)}
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
        title={selectedTerminal ? 'Edit Terminal' : 'Add New Terminal'}
      >
        <TerminalForm
          terminal={selectedTerminal}
          onSave={handleSaveSuccess}
          onCancel={() => setShowModal(false)}
        />
      </Modal>
    </div>
  )
}
