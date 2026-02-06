import { useState, useEffect, useRef } from 'react';
import type { KeyboardEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import { patientApi, laboratoryApi, orderApi } from '../../api/services';
import type { PatientLookupResult, TestSearchResult, Patient, PatientCreateRequest, OrderCreateRequest } from '../../types';
import { useBranding } from '../../contexts/BrandingContext';
import { formatCurrency } from '../../utils/currency';
import styles from './RegistrationPage.module.css';

// Simple Receipt Modal Component
const ReceiptModal = ({
  orderId,
  onClose,
  onPrint
}: {
  orderId: string;
  onClose: () => void;
  onPrint: () => void
}) => {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      backdropFilter: 'blur(4px)'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '2rem',
        width: '400px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        textAlign: 'center'
      }}>
        <div style={{
          fontSize: '3rem',
          marginBottom: '1rem',
          color: '#22c55e'
        }}>✓</div>
        <h2 style={{ marginBottom: '0.5rem', fontSize: '1.5rem', fontWeight: '600' }}>Order Created!</h2>
        <p style={{ color: '#666', marginBottom: '2rem' }}>
          Lab Number / Order ID: <strong>{orderId}</strong>
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button
            onClick={onPrint}
            style={{
              backgroundColor: '#2563eb',
              color: 'white',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              border: 'none',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Print Receipt
          </button>
          <button
            onClick={onClose}
            style={{
              backgroundColor: 'white',
              color: '#374151',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              border: '1px solid #d1d5db',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default function RegistrationPage() {
  const { branding } = useBranding();
  const currency = branding?.currency || 'PKR';

  // Patient form state
  const [mobileNumber, setMobileNumber] = useState('');
  const [patientSuggestions, setPatientSuggestions] = useState<PatientLookupResult[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const [, setLoadingPatients] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);

  // Expanded Patient Data
  const [patientFormData, setPatientFormData] = useState<Partial<PatientCreateRequest>>({
    phone: '',
    gender: 'Male',
    email: '',
    address: '',
    father_husband_name: '',
    cnic: '',
  });

  // Age & Date Logic
  const [dob, setDob] = useState('');
  const [ageYears, setAgeYears] = useState<number | ''>('');
  const [ageMonths, setAgeMonths] = useState<number | ''>('');
  const [ageDays, setAgeDays] = useState<number | ''>('');

  // Order form state
  const [testQuery, setTestQuery] = useState('');
  const [testSuggestions, setTestSuggestions] = useState<TestSearchResult[]>([]);
  const [showTestSuggestions, setShowTestSuggestions] = useState(false);
  const [selectedTestIndex, setSelectedTestIndex] = useState(-1);
  const [addedTests, setAddedTests] = useState<TestSearchResult[]>([]);

  // Payment State
  const [discountPercent, setDiscountPercent] = useState('0');
  const [discountAmount, setDiscountAmount] = useState('0');
  const [paidAmount, setPaidAmount] = useState('0');
  const [, setIsPaidManuallyEdited] = useState(false);
  const [referredBy, setReferredBy] = useState('');

  // Global Search State
  const [globalSearchQuery, setGlobalSearchQuery] = useState('');
  const [globalSuggestions, setGlobalSuggestions] = useState<PatientLookupResult[]>([]);
  const [showGlobalSuggestions, setShowGlobalSuggestions] = useState(false);
  const [, setLoadingGlobalSearch] = useState(false);

  // Receipt Modal State
  const [showReceipt, setShowReceipt] = useState(false);
  const [lastOrderId, setLastOrderId] = useState('');

  const globalSearchRef = useRef<HTMLInputElement>(null);
  const mobileInputRef = useRef<HTMLInputElement>(null);
  const testSearchRef = useRef<HTMLInputElement>(null);

  // Focus mobile input on mount
  useEffect(() => {
    mobileInputRef.current?.focus();
  }, []);

  // --- AGE / DOB SYNC LOGIC ---

  // Update Age when DOB changes
  const handleDobChange = (value: string) => {
    setDob(value);
    setPatientFormData(prev => ({ ...prev, date_of_birth: value }));

    if (value) {
      const birthDate = new Date(value);
      const today = new Date();

      let years = today.getFullYear() - birthDate.getFullYear();
      let months = today.getMonth() - birthDate.getMonth();
      let days = today.getDate() - birthDate.getDate();

      if (days < 0) {
        months--;
        // Get days in previous month
        const prevMonth = new Date(today.getFullYear(), today.getMonth(), 0);
        days += prevMonth.getDate();
      }
      if (months < 0) {
        years--;
        months += 12;
      }

      setAgeYears(Math.max(0, years));
      setAgeMonths(Math.max(0, months));
      setAgeDays(Math.max(0, days));

      setPatientFormData(prev => ({
        ...prev,
        age_years: Math.max(0, years),
        age_months: Math.max(0, months),
        age_days: Math.max(0, days)
      }));
    } else {
      setAgeYears('');
      setAgeMonths('');
      setAgeDays('');
    }
  };

  // Update DOB when Age changes (Years/Months/Days)
  const handleAgeChange = (years: number | '', months: number | '', days: number | '') => {
    setAgeYears(years);
    setAgeMonths(months);
    setAgeDays(days);

    // Calculate approximate DOB
    const date = new Date();
    date.setFullYear(date.getFullYear() - (typeof years === 'number' ? years : 0));
    date.setMonth(date.getMonth() - (typeof months === 'number' ? months : 0));
    date.setDate(date.getDate() - (typeof days === 'number' ? days : 0));

    // Format as YYYY-MM-DD
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    const formattedDate = `${yyyy}-${mm}-${dd}`;

    setDob(formattedDate);
    setPatientFormData(prev => ({
      ...prev,
      date_of_birth: formattedDate,
      age_years: typeof years === 'number' ? years : 0,
      age_months: typeof months === 'number' ? months : 0,
      age_days: typeof days === 'number' ? days : 0,
    }));
  };

  // --- PATIENT LOOKUP ---
  useEffect(() => {
    if (mobileNumber.length >= 3) {
      setLoadingPatients(true);
      const timer = setTimeout(async () => {
        try {
          const response = await patientApi.lookup(mobileNumber);
          setPatientSuggestions(response.data);
          setShowSuggestions(response.data.length > 0);
        } catch (error) {
          console.error('Failed to lookup patients:', error);
          setPatientSuggestions([]);
        } finally {
          setLoadingPatients(false);
        }
      }, 300);
      return () => clearTimeout(timer);
    } else {
      setPatientSuggestions([]);
      setShowSuggestions(false);
    }
  }, [mobileNumber]);

  // --- GLOBAL PATIENT SEARCH ---
  useEffect(() => {
    if (globalSearchQuery.length >= 2) {
      setLoadingGlobalSearch(true);
      const timer = setTimeout(async () => {
        try {
          const response = await patientApi.search(globalSearchQuery);
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          setGlobalSuggestions((response.results || (response as any).data || []) as PatientLookupResult[]);
          setShowGlobalSuggestions(true);
        } catch {
          setGlobalSuggestions([]);
        } finally {
          setLoadingGlobalSearch(false);
        }
      }, 300);
      return () => clearTimeout(timer);
    } else {
      setGlobalSuggestions([]);
      setShowGlobalSuggestions(false);
    }
  }, [globalSearchQuery]);

  // --- TEST SEARCH ---
  useEffect(() => {
    if (testQuery.length >= 2) {
      const timer = setTimeout(async () => {
        try {
          const response = await laboratoryApi.searchTests(testQuery);
          setTestSuggestions(response.data);
          setShowTestSuggestions(response.data.length > 0);
          setSelectedTestIndex(0); // Select first by default for easier Enter key usage
        } catch {
          setTestSuggestions([]);
        }
      }, 200);
      return () => clearTimeout(timer);
    } else {
      setTestSuggestions([]);
      setShowTestSuggestions(false);
    }
  }, [testQuery]);

  // --- CALCULATIONS ---
  const totalAmount = addedTests.reduce((sum, test) => sum + parseFloat(test.price), 0);
  const discountAmountValue = parseFloat(discountAmount) || 0;
  const netAmount = Math.max(totalAmount - discountAmountValue, 0);
  const paidAmountValue = parseFloat(paidAmount) || 0;
  const dueAmount = Math.max(netAmount - paidAmountValue, 0);

  // Auto-fill paid amount when discount/total changes, UNLESS user manually edited it
  // Actually, the requirement says "always update it out keep it editable".
  // "show paid month equial to total payable amunt, always update it but keep keep it editable"
  useEffect(() => {
    const net = totalAmount - parseFloat(discountAmount || '0');
    // If we want to "always update it", we should just update it:
    setPaidAmount(Math.max(net, 0).toFixed(2));

    // Note: If we really want to support manual override that persists across total changes, 
    // we would need more complex logic, but "always update it" suggests resetting to Net is preferred behavior 
    // until user edits it *for that transaction*. 
    // But since `totalAmount` changes when tests are added, usually you want Paid to match Net.
  }, [totalAmount, discountAmount]);

  const handleMobileKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || patientSuggestions.length === 0) return;
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => prev < patientSuggestions.length - 1 ? prev + 1 : prev);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => prev > 0 ? prev - 1 : 0);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedSuggestionIndex >= 0 && selectedSuggestionIndex < patientSuggestions.length) {
          loadPatient(patientSuggestions[selectedSuggestionIndex].id);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        break;
    }
  };

  const loadPatient = async (patientId: number) => {
    try {
      const response = await patientApi.get(patientId);
      const patient = response.data;
      setSelectedPatient(patient);

      setPatientFormData({
        phone: patient.phone,
        full_name: patient.full_name,
        first_name: patient.first_name,
        last_name: patient.last_name,
        gender: patient.gender,
        father_husband_name: patient.father_husband_name,
        address: patient.address,
        email: patient.email,
        national_id: patient.national_id,
        cnic: patient.cnic,
      });

      // Load Age/DOB
      if (patient.date_of_birth) {
        handleDobChange(patient.date_of_birth);
      } else if (patient.age_years) {
        // Fallback if only age_years is known
        handleAgeChange(patient.age_years, patient.age_months || 0, patient.age_days || 0);
      }

      setMobileNumber(patient.phone);
      setReferredBy(patient.default_referred_by || '');
      setShowSuggestions(false);

      // Reset search
      setGlobalSearchQuery('');
      setShowGlobalSuggestions(false);

    } catch (error) {
      console.error('Failed to load patient:', error);
      alert('Failed to load patient details');
    }
  };

  const savePatientMutation = useMutation({
    mutationFn: (data: PatientCreateRequest) =>
      selectedPatient ? patientApi.update(selectedPatient.id, data) : patientApi.create(data),
    onSuccess: (response) => {
      const patient = response.data;
      setSelectedPatient(patient);
      // Focus test search
      setTimeout(() => testSearchRef.current?.focus(), 100);
    },
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { message?: string } } };
      alert(`Error saving patient: ${error?.response?.data?.message || 'Unknown error'}`);
    },
  });

  const createOrderMutation = useMutation({
    mutationFn: (data: OrderCreateRequest) => orderApi.create(data),
    onSuccess: (response) => {
      setLastOrderId(response.order_id || 'Unknown');
      setShowReceipt(true);

      // Reset form handled after receipt close or separately?
      // Usually we reset after successful order.
      resetForm();
    },
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { message?: string } } };
      alert(`Error creating order: ${error?.response?.data?.message || 'Unknown error'}`);
    },
  });

  const resetForm = () => {
    setSelectedPatient(null);
    setPatientFormData({ phone: '', gender: 'Male', email: '', address: '', father_husband_name: '', cnic: '' });
    setMobileNumber('');
    setDob('');
    setAgeYears('');
    setAgeMonths('');
    setAgeDays('');
    setAddedTests([]);
    setDiscountPercent('0');
    setDiscountAmount('0');
    setPaidAmount('0');
    setReferredBy('');
    if (mobileInputRef.current) mobileInputRef.current.focus();
  };

  const handlePatientSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientFormData.phone) return alert('Mobile number is required');
    if (!patientFormData.full_name) return alert('Full Name is required');

    // Ensure Age/DOB is populated
    const dataToSubmit = {
      ...patientFormData,
      age_years: typeof ageYears === 'number' ? ageYears : 0,
      age_months: typeof ageMonths === 'number' ? ageMonths : 0,
      age_days: typeof ageDays === 'number' ? ageDays : 0,
    };

    savePatientMutation.mutate(dataToSubmit as PatientCreateRequest);
  };

  const handleTestKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      // If suggestions are visible and one is selected
      if (showTestSuggestions && testSuggestions.length > 0 && selectedTestIndex >= 0) {
        addTest(testSuggestions[selectedTestIndex]);
      }
      // Or if query exactly matches a test code (optional enhancement, sticking to selection for now)
    } else if (e.key === 'ArrowDown') {
      if (showTestSuggestions) {
        e.preventDefault();
        setSelectedTestIndex(prev => prev < testSuggestions.length - 1 ? prev + 1 : prev);
      }
    } else if (e.key === 'ArrowUp') {
      if (showTestSuggestions) {
        e.preventDefault();
        setSelectedTestIndex(prev => prev > 0 ? prev - 1 : 0);
      }
    } else if (e.key === 'Escape') {
      setShowTestSuggestions(false);
    }
  };

  const addTest = (test: TestSearchResult) => {
    const testId = test.test_id ?? test.id;
    if (!addedTests.find((t) => (t.test_id ?? t.id) === testId)) {
      setAddedTests([...addedTests, { ...test, id: testId }]);
    }
    setTestQuery('');
    setShowTestSuggestions(false);
    setSelectedTestIndex(-1);
    testSearchRef.current?.focus();
  };

  const removeTest = (testId: number) => {
    setAddedTests(addedTests.filter((t) => (t.test_id ?? t.id) !== testId));
  };

  const handleDiscountPercentChange = (value: string) => {
    const percent = parseFloat(value) || 0;
    setDiscountPercent(value);
    const amount = (totalAmount * percent) / 100;
    setDiscountAmount(amount.toFixed(2));
  };

  const handleDiscountAmountChange = (value: string) => {
    const amount = parseFloat(value) || 0;
    setDiscountAmount(value);
    const percent = totalAmount > 0 ? (amount / totalAmount) * 100 : 0;
    setDiscountPercent(percent.toFixed(2));
  };

  const handleCreateOrder = () => {
    if (!selectedPatient) return alert('Please save patient first');
    if (addedTests.length === 0) return alert('Please add at least one test');

    const orderData = {
      patient: selectedPatient.id,
      test_ids: addedTests.map((t) => t.test_id ?? t.id),
      discount: discountAmount,
      discount_percent: discountPercent,
      paid_amount: paidAmount,
      referred_by: referredBy,
    };

    createOrderMutation.mutate(orderData);
  };

  const handlePrintReceipt = () => {
    // Open print URL
    const printUrl = `/print/receipt/${lastOrderId}`; // Assuming this route exists or backend provides it
    window.open(printUrl, '_blank');
  };

  return (
    <div className={styles.container}>
      {showReceipt && (
        <ReceiptModal
          orderId={lastOrderId}
          onClose={() => setShowReceipt(false)}
          onPrint={handlePrintReceipt}
        />
      )}

      {/* Modern Header */}
      <div className={styles.header}>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">New Registration</h1>
          <p className={styles.subtitle}>Enter patient details and select tests</p>
        </div>

        {/* Global Patient Search - Top Right */}
        <div className={styles.globalSearchWrapper}>
          <div className={styles.searchIconWrapper}>
            <svg className={styles.searchIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            ref={globalSearchRef}
            type="text"
            value={globalSearchQuery}
            onChange={(e) => setGlobalSearchQuery(e.target.value)}
            className={styles.globalSearchInput}
            placeholder="Looking for existing patient? Search here..."
          />
          {showGlobalSuggestions && globalSuggestions.length > 0 && (
            <div className={styles.suggestions}>
              {globalSuggestions.map((patient) => (
                <div
                  key={patient.id}
                  className={styles.suggestionItem}
                  onClick={() => loadPatient(patient.id)}
                >
                  <div className={styles.suggestionMain}>{patient.full_name}</div>
                  <div className={styles.suggestionMeta}>
                    {patient.phone} • {patient.gender} • MRN: {patient.patient_id}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className={styles.splitView}>
        {/* PATIENT REGISTRATION FORM */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.sectionTitle}>
              <span style={{ marginRight: '10px' }}>👤</span>
              {selectedPatient ? 'Edit Patient Details' : 'Patient Information'}
            </h2>
            {selectedPatient && (
              <span className={styles.sectionStatus}>
                MRN: {selectedPatient.patient_id}
              </span>
            )}
          </div>

          <form onSubmit={handlePatientSubmit} className={styles.formGrid}>

            {/* Row 1: Mobile & Name */}
            <div className={styles.formGroup}>
              <label>Mobile Number <span className="text-red-500">*</span></label>
              <div className={styles.lookupWrapper}>
                <input
                  ref={mobileInputRef}
                  type="text"
                  value={mobileNumber}
                  onChange={(e) => {
                    setMobileNumber(e.target.value);
                    setPatientFormData({ ...patientFormData, phone: e.target.value });
                  }}
                  onKeyDown={handleMobileKeyDown}
                  className={styles.input}
                  placeholder="03xxxxxxxxx"
                  required
                  autoComplete="off"
                />
                {showSuggestions && patientSuggestions.length > 0 && (
                  <div className={styles.suggestions}>
                    {patientSuggestions.map((patient, index) => (
                      <div
                        key={patient.id}
                        className={`${styles.suggestionItem} ${index === selectedSuggestionIndex ? styles.suggestionActive : ''} `}
                        onClick={() => loadPatient(patient.id)}
                      >
                        <div className={styles.suggestionName}>{patient.full_name}</div>
                        <div className={styles.suggestionMeta}>{patient.phone} • {patient.gender}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className={styles.formGroup}>
              <label>Full Name <span className="text-red-500">*</span></label>
              <input
                type="text"
                value={patientFormData.full_name || ''}
                onChange={(e) => setPatientFormData({ ...patientFormData, full_name: e.target.value })}
                className={styles.input}
                required
              />
            </div>

            {/* Row 2: Age & DOB (Synced) */}
            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                <div className={styles.formGroup}>
                  <label>Date of Birth</label>
                  <input
                    type="date"
                    value={dob}
                    onChange={(e) => handleDobChange(e.target.value)}
                    className={styles.input}
                  />
                </div>
                <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                  <label>Age (Y / M / D)</label>
                  <div className={styles.ageGroup}>
                    <div className={styles.ageInput}>
                      <input
                        type="number"
                        placeholder="Y"
                        value={ageYears}
                        onChange={e => handleAgeChange(parseInt(e.target.value) || '', ageMonths, ageDays)}
                      />
                      <span>Yrs</span>
                    </div>
                    <div className={styles.ageInput}>
                      <input
                        type="number"
                        placeholder="M"
                        value={ageMonths}
                        onChange={e => handleAgeChange(ageYears, parseInt(e.target.value) || '', ageDays)}
                      />
                      <span>Mth</span>
                    </div>
                    <div className={styles.ageInput}>
                      <input
                        type="number"
                        placeholder="D"
                        value={ageDays}
                        onChange={e => handleAgeChange(ageYears, ageMonths, parseInt(e.target.value) || '')}
                      />
                      <span>Day</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Row 3: Gender & Father Name */}
            <div className={styles.formGroup}>
              <label>Gender <span className="text-red-500">*</span></label>
              <select
                value={patientFormData.gender}
                onChange={(e) => setPatientFormData({ ...patientFormData, gender: e.target.value as 'Male' | 'Female' | 'Other' })}
                className={styles.select}
                required
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className={styles.formGroup}>
              <label>Father / Husband Name</label>
              <input
                type="text"
                value={patientFormData.father_husband_name || ''}
                onChange={(e) => setPatientFormData({ ...patientFormData, father_husband_name: e.target.value })}
                className={styles.input}
              />
            </div>

            {/* Optional Fields Toggle or Just visible */}
            <div className={styles.formGroup}>
              <label>CNIC / National ID</label>
              <input
                type="text"
                value={patientFormData.cnic || patientFormData.national_id || ''}
                onChange={(e) => setPatientFormData({ ...patientFormData, cnic: e.target.value })}
                className={styles.input}
              />
            </div>

            <div className={styles.formGroup}>
              <label>Email (Optional)</label>
              <input
                type="email"
                value={patientFormData.email || ''}
                onChange={(e) => setPatientFormData({ ...patientFormData, email: e.target.value })}
                className={styles.input}
              />
            </div>

            <div className={styles.formGroup} style={{ gridColumn: '1 / -1' }}>
              <label>Address</label>
              <textarea
                value={patientFormData.address || ''}
                onChange={(e) => setPatientFormData({ ...patientFormData, address: e.target.value })}
                className={styles.input}
                style={{ minHeight: '60px', resize: 'vertical' }}
              />
            </div>

            <div className={styles.formActions}>
              <button
                type="submit"
                className={styles.primaryButton}
                disabled={savePatientMutation.isPending}
              >
                {savePatientMutation.isPending ? 'Saving...' : selectedPatient ? 'Update & Proceed to Tests' : 'Save Patient & Proceed'}
              </button>
            </div>
          </form>
        </div>

        {/* ORDER / TEST BOOKING FORM */}
        <div
          className={styles.card}
          style={{
            opacity: selectedPatient ? 1 : 0.5,
            pointerEvents: selectedPatient ? 'auto' : 'none',
            transition: 'opacity 0.3s ease'
          }}
        >
          <div className={styles.cardHeader}>
            <h2 className={styles.sectionTitle}>
              <span style={{ marginRight: '10px' }}>🧪</span>
              Order Tests & Billing
            </h2>
          </div>

          <div className={styles.orderContainer}>
            {/* 1. Search Bar */}
            <div className={styles.searchSection}>
              <div className={styles.autocompleteWrapper}>
                <input
                  ref={testSearchRef}
                  type="text"
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  onKeyDown={handleTestKeyDown}
                  className={styles.largeSearchInput}
                  placeholder="🔍 Search tests by name or code... (Press Enter to select)"
                />
                {showTestSuggestions && testSuggestions.length > 0 && (
                  <div className={styles.suggestions}>
                    {testSuggestions.map((test, index) => (
                      <div
                        key={test.test_id ?? test.id}
                        className={`${styles.suggestionItem} ${index === selectedTestIndex ? styles.suggestionActive : ''} `}
                        onClick={() => addTest(test)}
                      >
                        <div className={styles.suggestionName}>
                          <span style={{ fontWeight: 'bold', color: 'var(--color-primary)' }}>{test.test_code}</span> - {test.test_name}
                        </div>
                        <div className={styles.suggestionMeta}>
                          {test.category_name} • {formatCurrency(test.price, currency)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 2. Added Tests List (Shopping Cart Style) */}
            <div className={styles.addedTestsSection}>
              {addedTests.length === 0 ? (
                <div className={styles.emptyState}>
                  <p>No tests selected. Search above to add tests.</p>
                </div>
              ) : (
                <div className={styles.testsTableContainer}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Test Name</th>
                        <th style={{ textAlign: 'right' }}>Price</th>
                        <th style={{ width: '50px' }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {addedTests.map(test => (
                        <tr key={test.test_id ?? test.id}>
                          <td><strong>{test.test_code}</strong></td>
                          <td>{test.test_name}</td>
                          <td style={{ textAlign: 'right' }}>{formatCurrency(test.price, currency)}</td>
                          <td>
                            <button onClick={() => removeTest(test.test_id ?? test.id)} className={styles.removeButton}>
                              &times;
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* 3. Payment Section */}
            <div className={styles.paymentSection}>
              <div className={styles.paymentGrid}>
                <div className={styles.paymentCol}>
                  <div className={styles.formGroup}>
                    <label>Referred By</label>
                    <input
                      type="text"
                      value={referredBy}
                      onChange={(e) => setReferredBy(e.target.value)}
                      className={styles.input}
                      placeholder="Consultant Name"
                    />
                  </div>
                </div>

                <div className={styles.paymentColRight}>
                  <div className={styles.summaryRow}>
                    <span>Total Amount</span>
                    <span className={styles.amountLarge}>{formatCurrency(totalAmount.toFixed(2), currency)}</span>
                  </div>

                  <div className={styles.discountRow}>
                    <div className={styles.discountInputGroup}>
                      <label>Disc %</label>
                      <input
                        type="number"
                        value={discountPercent}
                        onChange={e => handleDiscountPercentChange(e.target.value)}
                        className={styles.compactInput}
                      />
                    </div>
                    <div className={styles.discountInputGroup}>
                      <label>Disc Amt</label>
                      <input
                        type="number"
                        value={discountAmount}
                        onChange={e => handleDiscountAmountChange(e.target.value)}
                        className={styles.compactInput}
                      />
                    </div>
                  </div>

                  <div className={styles.summaryRow}>
                    <span>Net Payable</span>
                    <span className={styles.amountHighlight}>{formatCurrency(netAmount.toFixed(2), currency)}</span>
                  </div>

                  <div className={styles.summaryRow}>
                    <span>Paid Amount</span>
                    <input
                      type="number"
                      value={paidAmount}
                      onChange={e => {
                        setPaidAmount(e.target.value);
                        setIsPaidManuallyEdited(true);
                      }}
                      className={styles.paymentInput}
                    />
                  </div>

                  <div className={styles.summaryRow}>
                    <span>Due Balance</span>
                    <span className={`${styles.amountHighlight} ${dueAmount > 0 ? styles.textRed : styles.textGreen} `}>
                      {formatCurrency(dueAmount.toFixed(2), currency)}
                    </span>
                  </div>
                </div>
              </div>

              <div className={styles.formActions}>
                <button
                  onClick={handleCreateOrder}
                  className={styles.primaryButtonLarge}
                  disabled={createOrderMutation.isPending || addedTests.length === 0}
                >
                  {createOrderMutation.isPending ? 'Processing...' : 'CONFIRM & PRINT RECEIPT'}
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
