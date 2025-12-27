import { useState, useEffect, useCallback, useRef } from 'react'
import { Modal } from './Modal'
import { patientService } from '../services/patients'
import type { Patient } from '../types'

interface PatientSearchModalProps {
  isOpen: boolean
  onClose: () => void
  onSelect: (patient: Patient) => void
}

/**
 * A modal for searching and selecting patients.
 * Supports keyboard navigation with arrow keys and Enter.
 */
export function PatientSearchModal({
  isOpen,
  onClose,
  onSelect,
}: PatientSearchModalProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [patients, setPatients] = useState<Patient[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  // Focus search input when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        searchInputRef.current?.focus()
      }, 100)
    }
    // Reset state when modal closes
    if (!isOpen) {
      setSearchQuery('')
      setPatients([])
      setSelectedIndex(-1)
      setError(null)
    }
  }, [isOpen])

  // Search patients with debounce
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setPatients([])
      setSelectedIndex(-1)
      return
    }

    const searchPatients = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const results = await patientService.search(searchQuery)
        setPatients(results)
        setSelectedIndex(results.length > 0 ? 0 : -1)
      } catch (err) {
        console.error('Failed to search patients:', err)
        setError('Failed to search patients. Please try again.')
        setPatients([])
      } finally {
        setIsLoading(false)
      }
    }

    const debounce = setTimeout(searchPatients, 300)
    return () => clearTimeout(debounce)
  }, [searchQuery])

  // Handle select patient (must be defined before handleKeyDown)
  const handleSelectPatient = useCallback((patient: Patient) => {
    onSelect(patient)
    onClose()
  }, [onSelect, onClose])

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (patients.length === 0) return

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault()
          setSelectedIndex((prev) =>
            prev < patients.length - 1 ? prev + 1 : prev
          )
          break
        case 'ArrowUp':
          event.preventDefault()
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : prev))
          break
        case 'Enter':
          event.preventDefault()
          if (selectedIndex >= 0 && selectedIndex < patients.length) {
            handleSelectPatient(patients[selectedIndex])
          }
          break
        case 'Escape':
          onClose()
          break
      }
    },
    [patients, selectedIndex, onClose, handleSelectPatient]
  )

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && listRef.current) {
      const selectedElement = listRef.current.children[selectedIndex] as HTMLElement
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest' })
      }
    }
  }, [selectedIndex])

  const formatAge = (patient: Patient): string => {
    const parts = []
    if (patient.age_years) parts.push(`${patient.age_years}y`)
    if (patient.age_months) parts.push(`${patient.age_months}m`)
    if (patient.age_days) parts.push(`${patient.age_days}d`)
    return parts.length > 0 ? parts.join(' ') : patient.dob || 'Unknown'
  }

  const formatSex = (sex: string): string => {
    const sexMap: Record<string, string> = { M: 'Male', F: 'Female', O: 'Other' }
    return sexMap[sex] || sex
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Search Patient">
      <div className="space-y-4" onKeyDown={handleKeyDown}>
        {/* Search Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search by Name, Phone, CNIC, or MRN
          </label>
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter at least 2 characters to search..."
            autoFocus
          />
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-4">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600 text-sm">Searching...</p>
          </div>
        )}

        {/* No Results */}
        {!isLoading && searchQuery.length >= 2 && patients.length === 0 && (
          <div className="text-center py-4 text-gray-600">
            No patients found matching "{searchQuery}"
          </div>
        )}

        {/* Keyboard Navigation Hint */}
        {patients.length > 0 && (
          <div className="text-xs text-gray-500 flex items-center gap-2">
            <span className="bg-gray-100 px-2 py-1 rounded">↑↓</span>
            <span>Navigate</span>
            <span className="bg-gray-100 px-2 py-1 rounded">Enter</span>
            <span>Select</span>
            <span className="bg-gray-100 px-2 py-1 rounded">Esc</span>
            <span>Close</span>
          </div>
        )}

        {/* Patient List */}
        {patients.length > 0 && (
          <div
            ref={listRef}
            className="border border-gray-200 rounded-lg max-h-96 overflow-y-auto"
          >
            {patients.map((patient, index) => (
              <button
                key={patient.id}
                type="button"
                onClick={() => handleSelectPatient(patient)}
                onMouseEnter={() => setSelectedIndex(index)}
                className={`w-full px-4 py-3 text-left border-b border-gray-100 last:border-0 transition-colors ${
                  selectedIndex === index
                    ? 'bg-blue-50 border-l-4 border-l-blue-500'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">
                      {patient.full_name}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      <span className="inline-block mr-4">
                        <strong>MRN:</strong> {patient.mrn}
                      </span>
                      <span className="inline-block mr-4">
                        <strong>Phone:</strong> {patient.phone}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      <span className="inline-block mr-4">
                        <strong>Age:</strong> {formatAge(patient)}
                      </span>
                      <span className="inline-block mr-4">
                        <strong>Sex:</strong> {formatSex(patient.sex)}
                      </span>
                      {patient.cnic && (
                        <span className="inline-block">
                          <strong>CNIC:</strong> {patient.cnic}
                        </span>
                      )}
                    </div>
                    {patient.address && (
                      <div className="text-sm text-gray-500 mt-1 truncate">
                        <strong>Address:</strong> {patient.address}
                      </div>
                    )}
                  </div>
                  <div className="text-blue-600 text-sm font-medium ml-4">
                    Select
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Instructions */}
        {!isLoading && patients.length === 0 && searchQuery.length < 2 && (
          <div className="text-center py-8 text-gray-500">
            <p>Enter at least 2 characters to search for patients.</p>
            <p className="mt-2 text-sm">
              You can search by name, phone number, CNIC, or medical record
              number (MRN).
            </p>
          </div>
        )}
      </div>
    </Modal>
  )
}
