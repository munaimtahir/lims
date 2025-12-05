import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { patientService } from '../../services/patients'
import { catalogService } from '../../services/catalog'
import { orderService } from '../../services/orders'
import { PatientSearchModal } from '../../components/PatientSearchModal'
import type { Patient, TestCatalog } from '../../types'
import {
  validateCNIC,
  validatePhone,
  validateDOB,
  formatCNIC,
  formatPhone,
  calculateAgeFromDOB,
  calculateDOBFromAge,
  formatCurrency,
} from '../../utils/validators'
import { ROUTES } from '../../utils/constants'

interface PatientFormData {
  cnic: string
  phone: string
  full_name: string
  patient_id: string
  sex: 'M' | 'F' | 'O'
  dob: string
  age_years: number
  age_months: number
  age_days: number
}

export function NewLabSlipPage() {
  const navigate = useNavigate()

  // Patient form state
  const [patientData, setPatientData] = useState<PatientFormData>({
    cnic: '',
    phone: '',
    full_name: '',
    patient_id: '',
    sex: 'M',
    dob: '',
    age_years: 0,
    age_months: 0,
    age_days: 0,
  })

  const [existingPatient, setExistingPatient] = useState<Patient | null>(null)
  const [patientSuggestions, setPatientSuggestions] = useState<Patient[]>([])

  // Patient search modal state
  const [isPatientSearchOpen, setIsPatientSearchOpen] = useState(false)

  // Test selection state
  const [testSearch, setTestSearch] = useState('')
  const [testSuggestions, setTestSuggestions] = useState<TestCatalog[]>([])
  const [selectedTests, setSelectedTests] = useState<TestCatalog[]>([])
  const [testSearchIndex, setTestSearchIndex] = useState(-1)
  const testSearchInputRef = useRef<HTMLInputElement>(null)

  // Billing state
  const [discount, setDiscount] = useState(0)
  const [amountPaid, setAmountPaid] = useState(0)
  const [reportDate, setReportDate] = useState(
    new Date().toISOString().split('T')[0]
  )
  const [reportTime, setReportTime] = useState(
    new Date().toTimeString().slice(0, 5)
  )

  // UI state
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Search for existing patients by CNIC or phone
  useEffect(() => {
    const searchPatients = async () => {
      if (patientData.phone.length >= 5 || patientData.cnic.length >= 5) {
        const query = patientData.phone || patientData.cnic
        try {
          const patients = await patientService.search(query)
          setPatientSuggestions(patients)
        } catch (error) {
          console.error('Failed to search patients:', error)
          setPatientSuggestions([])
        }
      } else {
        setPatientSuggestions([])
      }
    }

    const debounce = setTimeout(searchPatients, 300)
    return () => clearTimeout(debounce)
  }, [patientData.phone, patientData.cnic])

  // Search tests with live autocomplete
  useEffect(() => {
    const searchTests = async () => {
      if (testSearch.length >= 1) {
        try {
          const tests = await catalogService.search(testSearch)
          const filteredTests = tests.filter(t => !selectedTests.find(s => s.id === t.id))
          setTestSuggestions(filteredTests)
          // Reset selection index when results change
          setTestSearchIndex(filteredTests.length > 0 ? 0 : -1)
        } catch (error) {
          console.error('Failed to search tests:', error)
          setTestSuggestions([])
          setTestSearchIndex(-1)
        }
      } else {
        setTestSuggestions([])
        setTestSearchIndex(-1)
      }
    }

    const debounce = setTimeout(searchTests, 200)
    return () => clearTimeout(debounce)
  }, [testSearch, selectedTests])

  // Define addTest callback before it's used in handleTestSearchKeyDown
  const addTest = useCallback((test: TestCatalog) => {
    setSelectedTests(prev => [...prev, test])
    setTestSearch('')
    setTestSuggestions([])
    setTestSearchIndex(-1)
    // Focus back on the search input after selection
    setTimeout(() => {
      testSearchInputRef.current?.focus()
    }, 50)
  }, [])

  // Handle test search keyboard navigation
  const handleTestSearchKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (testSuggestions.length === 0) return

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault()
        setTestSearchIndex((prev) =>
          prev < testSuggestions.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        event.preventDefault()
        setTestSearchIndex((prev) => (prev > 0 ? prev - 1 : prev))
        break
      case 'Enter':
        event.preventDefault()
        if (testSearchIndex >= 0 && testSearchIndex < testSuggestions.length) {
          addTest(testSuggestions[testSearchIndex])
        }
        break
      case 'Escape':
        setTestSuggestions([])
        setTestSearchIndex(-1)
        break
    }
  }, [testSuggestions, testSearchIndex, addTest])

  // Define selectPatient callback before it's used in handlePatientSelect
  const selectPatient = useCallback((patient: Patient) => {
    setExistingPatient(patient)
    
    // Use age fields from patient if available, otherwise calculate from DOB
    let ageYears = patient.age_years || 0
    let ageMonths = patient.age_months || 0
    let ageDays = patient.age_days || 0
    
    // If no age fields but DOB exists, calculate age
    if (!patient.age_years && !patient.age_months && !patient.age_days && patient.dob && validateDOB(patient.dob)) {
      const age = calculateAgeFromDOB(patient.dob)
      ageYears = age.years
      ageMonths = age.months
      ageDays = age.days
    }
    
    setPatientData({
      cnic: patient.cnic || '',
      phone: patient.phone,
      full_name: patient.full_name,
      patient_id: patient.mrn,
      sex: patient.sex,
      dob: patient.dob || '',
      age_years: ageYears,
      age_months: ageMonths,
      age_days: ageDays,
    })
    setPatientSuggestions([])
  }, [])

  // Handle patient selection from modal
  const handlePatientSelect = useCallback((patient: Patient) => {
    selectPatient(patient)
    setIsPatientSearchOpen(false)
  }, [selectPatient])

  const handlePatientChange = (
    field: keyof PatientFormData,
    value: string | number
  ) => {
    let formattedValue = value

    if (field === 'cnic' && typeof value === 'string') {
      formattedValue = formatCNIC(value)
    } else if (field === 'phone' && typeof value === 'string') {
      formattedValue = formatPhone(value)
    }

    // Update the specific field
    const updates: Partial<PatientFormData> = { [field]: formattedValue }

    // If DOB changed, recalculate age
    if (field === 'dob' && typeof value === 'string') {
      if (validateDOB(value)) {
        const age = calculateAgeFromDOB(value)
        updates.age_years = age.years
        updates.age_months = age.months
        updates.age_days = age.days
      }
    }

    // If any age field changed, recalculate DOB
    if (
      field === 'age_years' ||
      field === 'age_months' ||
      field === 'age_days'
    ) {
      const years =
        field === 'age_years'
          ? Number(value) || 0
          : patientData.age_years || 0
      const months =
        field === 'age_months'
          ? Number(value) || 0
          : patientData.age_months || 0
      const days =
        field === 'age_days'
          ? Number(value) || 0
          : patientData.age_days || 0

      // Recalculate DOB from age
      updates.dob = calculateDOBFromAge(years, months, days)
    }

    setPatientData(prev => ({ ...prev, ...updates }))
    setExistingPatient(null)
    setErrors(prev => ({ ...prev, [field]: '' }))
  }

  const removeTest = (testId: number) => {
    setSelectedTests(prev => prev.filter(t => t.id !== testId))
  }

  // Fix cash calculation to handle NaN properly
  const billAmount = selectedTests.reduce((sum, test) => {
    const price = Number(test.price) || 0
    return sum + price
  }, 0)
  const netAmount = billAmount - discount
  const change = amountPaid - netAmount

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!patientData.full_name.trim()) {
      newErrors.full_name = 'Full name is required'
    }
    // CNIC is now optional
    if (patientData.cnic && !validateCNIC(patientData.cnic)) {
      newErrors.cnic = 'Valid CNIC format required (e.g., 12345-1234567-1)'
    }
    if (!patientData.phone || !validatePhone(patientData.phone)) {
      newErrors.phone = 'Valid phone number is required'
    }
    
    // Either DOB or at least one age field must be provided
    const hasAge =
      patientData.age_years > 0 ||
      patientData.age_months > 0 ||
      patientData.age_days > 0
    const hasDOB = patientData.dob && validateDOB(patientData.dob)
    
    if (!hasAge && !hasDOB) {
      newErrors.age = 'Either date of birth or at least one age field is required'
    }
    
    if (selectedTests.length === 0) {
      newErrors.tests = 'At least one test must be selected'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (printImmediately: boolean) => {
    if (!validateForm()) return

    setIsSubmitting(true)
    try {
      // Create or use existing patient
      let patientId = existingPatient?.id

      if (!patientId) {
        // Prepare patient data - send only required fields and non-empty optional fields
        const patientPayload: Record<string, string | number | undefined> = {
          phone: patientData.phone,
          full_name: patientData.full_name,
          sex: patientData.sex,
        }
        
        // Add CNIC only if provided (optional field)
        if (patientData.cnic && validateCNIC(patientData.cnic)) {
          patientPayload.cnic = patientData.cnic
        }
        
        // Add age fields if provided
        if (patientData.age_years > 0 || patientData.age_months > 0 || patientData.age_days > 0) {
          patientPayload.age_years = patientData.age_years || 0
          patientPayload.age_months = patientData.age_months || 0
          patientPayload.age_days = patientData.age_days || 0
        }
        
        // Add DOB if provided
        if (patientData.dob && validateDOB(patientData.dob)) {
          patientPayload.dob = patientData.dob
        }
        
        const newPatient = await patientService.create(patientPayload)
        patientId = newPatient.id
      }

      // Create order
      const order = await orderService.create({
        patient: patientId,
        test_ids: selectedTests.map(t => t.id),
        priority: 'ROUTINE',
        notes: '',
      })

      if (printImmediately) {
        // TODO: Trigger PDF generation and download
        console.log('Print order:', order.id)
      }

      // Navigate to order detail or lab home
      navigate(ROUTES.LAB_ORDER_DETAIL(order.id))
    } catch (error: unknown) {
      console.error('Failed to create order:', error)
      const err = error as { response?: { data?: { detail?: string } }; message?: string }
      const errorMessage = err?.response?.data?.detail || 
                          err?.message || 
                          'Failed to create order. Please try again.'
      setErrors({ submit: errorMessage })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">New Lab Slip</h1>

      {errors.submit && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{errors.submit}</p>
        </div>
      )}

      {/* Patient Information Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-blue-700">
            Patient Information
          </h2>
          <button
            type="button"
            onClick={() => setIsPatientSearchOpen(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            Search Patient
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* CNIC - Now Optional */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              CNIC <span className="text-gray-400 text-xs">(Optional)</span>
            </label>
            <input
              type="text"
              value={patientData.cnic}
              onChange={e => handlePatientChange('cnic', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
                errors.cnic
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              placeholder="12345-1234567-1"
            />
            {errors.cnic && (
              <p className="text-xs text-red-500 mt-1">{errors.cnic}</p>
            )}

            {/* Patient suggestions */}
            {patientSuggestions.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                {patientSuggestions.map(patient => (
                  <button
                    key={patient.id}
                    type="button"
                    onClick={() => selectPatient(patient)}
                    className="w-full px-3 py-2 text-left hover:bg-blue-50 border-b border-gray-100 last:border-0"
                  >
                    <div className="font-medium">{patient.full_name}</div>
                    <div className="text-xs text-gray-600">
                      MRN: {patient.mrn} | {patient.phone}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Mobile - with patient search */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mobile <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={patientData.phone}
              onChange={e => handlePatientChange('phone', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
                errors.phone
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              placeholder="03001234567"
            />
            {errors.phone && (
              <p className="text-xs text-red-500 mt-1">{errors.phone}</p>
            )}
          </div>

          {/* Full Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={patientData.full_name}
              onChange={e => handlePatientChange('full_name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
                errors.full_name
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              placeholder="Enter full name"
            />
            {errors.full_name && (
              <p className="text-xs text-red-500 mt-1">{errors.full_name}</p>
            )}
          </div>

          {/* Patient ID (read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Patient ID
            </label>
            <input
              type="text"
              value={patientData.patient_id}
              readOnly
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
              placeholder="Auto-generated"
            />
          </div>

          {/* Gender */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Gender
            </label>
            <select
              value={patientData.sex}
              onChange={e => handlePatientChange('sex', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="M">Male</option>
              <option value="F">Female</option>
              <option value="O">Other</option>
            </select>
          </div>

          {/* DOB - Now editable and synced with Age */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date of Birth{' '}
              <span className="text-gray-400 text-xs">(or enter age below)</span>
            </label>
            <input
              type="date"
              value={patientData.dob}
              max={new Date().toISOString().split('T')[0]}
              onChange={e =>
                handlePatientChange('dob', e.target.value)
              }
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
                errors.age
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
            />
          </div>

          {/* Age - Split into 3 editable fields */}
          <div className="col-span-1 md:col-span-2 lg:col-span-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Age{' '}
              <span className="text-red-500">*</span>{' '}
              <span className="text-gray-400 text-xs">
                (at least one field required)
              </span>
            </label>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <input
                  type="number"
                  min="0"
                  max="150"
                  value={patientData.age_years || ''}
                  onChange={e =>
                    handlePatientChange(
                      'age_years',
                      e.target.value ? Number(e.target.value) : 0
                    )
                  }
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
                    errors.age
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300 focus:ring-blue-500'
                  }`}
                  placeholder="Years"
                />
                <p className="text-xs text-gray-500 mt-1">Years</p>
              </div>
              <div>
                <input
                  type="number"
                  min="0"
                  max="11"
                  value={patientData.age_months || ''}
                  onChange={e =>
                    handlePatientChange(
                      'age_months',
                      e.target.value ? Number(e.target.value) : 0
                    )
                  }
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
                    errors.age
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300 focus:ring-blue-500'
                  }`}
                  placeholder="Months"
                />
                <p className="text-xs text-gray-500 mt-1">Months</p>
              </div>
              <div>
                <input
                  type="number"
                  min="0"
                  max="30"
                  value={patientData.age_days || ''}
                  onChange={e =>
                    handlePatientChange(
                      'age_days',
                      e.target.value ? Number(e.target.value) : 0
                    )
                  }
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
                    errors.age
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300 focus:ring-blue-500'
                  }`}
                  placeholder="Days"
                />
                <p className="text-xs text-gray-500 mt-1">Days</p>
              </div>
            </div>
            {errors.age && (
              <p className="text-xs text-red-500 mt-1">{errors.age}</p>
            )}
          </div>
        </div>
      </div>

      {/* Test Selection Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-blue-700 mb-4">
          Test Selection
        </h2>

        {/* Test Search */}
        <div className="mb-4 relative">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search Tests{' '}
            <span className="text-gray-400 text-xs">
              (Use ↑↓ to navigate, Enter to select)
            </span>
          </label>
          <input
            ref={testSearchInputRef}
            type="text"
            value={testSearch}
            onChange={e => setTestSearch(e.target.value)}
            onKeyDown={handleTestSearchKeyDown}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Search by test name or code"
          />
          {errors.tests && (
            <p className="text-xs text-red-500 mt-1">{errors.tests}</p>
          )}

          {/* Test suggestions */}
          {testSuggestions.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
              {testSuggestions.map((test, index) => (
                <button
                  key={test.id}
                  type="button"
                  onClick={() => addTest(test)}
                  onMouseEnter={() => setTestSearchIndex(index)}
                  className={`w-full px-3 py-2 text-left border-b border-gray-100 last:border-0 ${
                    testSearchIndex === index
                      ? 'bg-blue-50 border-l-4 border-l-blue-500'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-medium">{test.name}</div>
                      <div className="text-xs text-gray-600">
                        {test.code} - {test.sample_type}
                      </div>
                    </div>
                    <div className="text-sm font-semibold text-blue-600">
                      {formatCurrency(test.price)}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Selected Tests Table */}
        {selectedTests.length > 0 && (
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
                    Sample Type
                  </th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">
                    Price
                  </th>
                  <th className="text-center py-2 px-3 text-sm font-medium text-gray-700">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {selectedTests.map(test => (
                  <tr key={test.id} className="border-b border-gray-100">
                    <td className="py-2 px-3">{test.name}</td>
                    <td className="py-2 px-3 text-sm text-gray-600">
                      {test.code}
                    </td>
                    <td className="py-2 px-3 text-sm text-gray-600">
                      {test.sample_type}
                    </td>
                    <td className="py-2 px-3 text-right font-medium">
                      {formatCurrency(test.price)}
                    </td>
                    <td className="py-2 px-3 text-center">
                      <button
                        type="button"
                        onClick={() => removeTest(test.id)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Billing Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-blue-700 mb-4">
          Billing & Report Details
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-700">Bill Amount:</span>
              <span className="font-semibold text-lg">
                {formatCurrency(billAmount)}
              </span>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Discount
              </label>
              <input
                type="number"
                min="0"
                max={billAmount}
                value={discount}
                onChange={e => setDiscount(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex justify-between items-center py-2 border-b border-gray-400">
              <span className="text-gray-700 font-medium">Net Amount:</span>
              <span className="font-bold text-xl text-blue-600">
                {formatCurrency(netAmount)}
              </span>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Amount Paid
              </label>
              <input
                type="number"
                min="0"
                value={amountPaid}
                onChange={e => setAmountPaid(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex justify-between items-center py-2">
              <span className="text-gray-700">Change:</span>
              <span
                className={`font-semibold ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}
              >
                {formatCurrency(Math.abs(change))}
              </span>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Report Date
              </label>
              <input
                type="date"
                value={reportDate}
                onChange={e => setReportDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Report Time
              </label>
              <input
                type="time"
                value={reportTime}
                onChange={e => setReportTime(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 justify-end">
        <button
          type="button"
          onClick={() => navigate(ROUTES.LAB)}
          disabled={isSubmitting}
          className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={() => handleSubmit(false)}
          disabled={isSubmitting}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Saving...' : 'Save Only'}
        </button>
        <button
          type="button"
          onClick={() => handleSubmit(true)}
          disabled={isSubmitting}
          className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Saving...' : 'Save & Print'}
        </button>
      </div>

      {/* Patient Search Modal */}
      <PatientSearchModal
        isOpen={isPatientSearchOpen}
        onClose={() => setIsPatientSearchOpen(false)}
        onSelect={handlePatientSelect}
      />
    </div>
  )
}
