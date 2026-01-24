import { useState, useEffect, useRef } from 'react';
import type { KeyboardEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import { patientApi, laboratoryApi, orderApi } from '../../api/services';
import type { PatientLookupResult, TestSearchResult, Patient, PatientCreateRequest } from '../../types';
import styles from './RegistrationPage.module.css';

export default function RegistrationPage() {
  // Patient form state
  const [mobileNumber, setMobileNumber] = useState('');
  const [patientSuggestions, setPatientSuggestions] = useState<PatientLookupResult[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const [loadingPatients, setLoadingPatients] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientFormData, setPatientFormData] = useState<Partial<PatientCreateRequest>>({
    phone: '',
    gender: 'Male',
  });

  // Order form state
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [testQuery, setTestQuery] = useState('');
  const [testSuggestions, setTestSuggestions] = useState<TestSearchResult[]>([]);
  const [showTestSuggestions, setShowTestSuggestions] = useState(false);
  const [selectedTestIndex, setSelectedTestIndex] = useState(-1);
  const [addedTests, setAddedTests] = useState<TestSearchResult[]>([]);
  const [discountPercent, setDiscountPercent] = useState('0');
  const [discountAmount, setDiscountAmount] = useState('0');
  const [paidAmount, setPaidAmount] = useState('0');
  const [referredBy, setReferredBy] = useState('');

  // Global Search State
  const [globalSearchQuery, setGlobalSearchQuery] = useState('');
  const [globalSuggestions, setGlobalSuggestions] = useState<PatientLookupResult[]>([]);
  const [showGlobalSuggestions, setShowGlobalSuggestions] = useState(false);
  const [loadingGlobalSearch, setLoadingGlobalSearch] = useState(false);
  const globalSearchRef = useRef<HTMLInputElement>(null);

  const mobileInputRef = useRef<HTMLInputElement>(null);
  const testSearchRef = useRef<HTMLInputElement>(null);

  // Focus mobile input on mount
  useEffect(() => {
    mobileInputRef.current?.focus();
  }, []);

  // Patient lookup debounced search
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

  // Global Patient Search
  useEffect(() => {
    if (globalSearchQuery.length >= 2) {
      setLoadingGlobalSearch(true);
      const timer = setTimeout(async () => {
        try {
          // Use the general search endpoint which likely searches name, mobile, etc.
          // If a dedicated general search doesn't exist, we can use lookup for mobile or list with search param
          const response = await patientApi.search(globalSearchQuery);
          // @ts-ignore - Assuming response structure matches, otherwise adapt
          setGlobalSuggestions(response.results || response.data || []);
          setShowGlobalSuggestions(true);
        } catch (error) {
          console.error('Failed to search patients:', error);
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

  // Test search debounced
  useEffect(() => {
    if (testQuery.length >= 2) {
      const timer = setTimeout(async () => {
        try {
          const response = await laboratoryApi.searchTests(testQuery);
          setTestSuggestions(response.data);
          setShowTestSuggestions(response.data.length > 0);
        } catch (error) {
          console.error('Failed to search tests:', error);
          setTestSuggestions([]);
        }
      }, 200);
      return () => clearTimeout(timer);
    } else {
      setTestSuggestions([]);
      setShowTestSuggestions(false);
    }
  }, [testQuery]);

  // Calculate totals
  const totalAmount = addedTests.reduce((sum, test) => sum + parseFloat(test.price), 0);
  const discountAmountValue = parseFloat(discountAmount) || 0;
  const netAmount = Math.max(totalAmount - discountAmountValue, 0);
  const paidAmountValue = parseFloat(paidAmount) || 0;
  const dueAmount = Math.max(netAmount - paidAmountValue, 0);

  // Auto-fill paid amount when discount changes
  useEffect(() => {
    const net = totalAmount - parseFloat(discountAmount || '0');
    setPaidAmount(Math.max(net, 0).toFixed(2));
  }, [totalAmount, discountAmount]);

  const handleMobileKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || patientSuggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex((prev) =>
          prev < patientSuggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex((prev) => (prev > 0 ? prev - 1 : 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedSuggestionIndex >= 0 && selectedSuggestionIndex < patientSuggestions.length) {
          loadPatient(patientSuggestions[selectedSuggestionIndex].id);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
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
        date_of_birth: patient.date_of_birth,
        age_years: patient.age_years,
        gender: patient.gender,
        father_husband_name: patient.father_husband_name,
        address: patient.address,
        email: patient.email,
        national_id: patient.national_id,
      });
      setMobileNumber(patient.phone);
      setReferredBy(patient.default_referred_by || '');
      setShowSuggestions(false);
      setSelectedSuggestionIndex(-1);
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
      setShowOrderForm(true);
      // Focus test search after short delay
      setTimeout(() => testSearchRef.current?.focus(), 100);
    },
    onError: (error: any) => {
      alert(`Error saving patient: ${error?.response?.data?.message || error?.message || 'Unknown error'}`);
    },
  });

  const createOrderMutation = useMutation({
    mutationFn: (data: any) => orderApi.create(data),
    onSuccess: (response) => {
      alert(`Order created successfully! Order ID: ${response.order_id}`);
      // Reset form
      setSelectedPatient(null);
      setPatientFormData({ phone: '', gender: 'Male' });
      setMobileNumber('');
      setAddedTests([]);
      setDiscountPercent('0');
      setDiscountAmount('0');
      setPaidAmount('0');
      setReferredBy('');
      setShowOrderForm(false);
      mobileInputRef.current?.focus();
    },
    onError: (error: any) => {
      alert(`Error creating order: ${error?.response?.data?.message || error?.message || 'Unknown error'}`);
    },
  });

  const handlePatientSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientFormData.phone) {
      alert('Mobile number is required');
      return;
    }
    savePatientMutation.mutate(patientFormData as PatientCreateRequest);
  };

  const handleTestKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!showTestSuggestions || testSuggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedTestIndex((prev) => (prev < testSuggestions.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedTestIndex((prev) => (prev > 0 ? prev - 1 : 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedTestIndex >= 0 && selectedTestIndex < testSuggestions.length) {
          addTest(testSuggestions[selectedTestIndex]);
        }
        break;
      case 'Escape':
        setShowTestSuggestions(false);
        setSelectedTestIndex(-1);
        break;
    }
  };

  const addTest = (test: TestSearchResult) => {
    if (!addedTests.find((t) => t.id === test.id)) {
      setAddedTests([...addedTests, test]);
    }
    setTestQuery('');
    setShowTestSuggestions(false);
    setSelectedTestIndex(-1);
    testSearchRef.current?.focus();
  };

  const removeTest = (testId: number) => {
    setAddedTests(addedTests.filter((t) => t.id !== testId));
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
    if (!selectedPatient) {
      alert('Please save patient first');
      return;
    }
    if (addedTests.length === 0) {
      alert('Please add at least one test');
      return;
    }

    const orderData = {
      patient: selectedPatient.id,
      test_ids: addedTests.map((t) => t.id),
      discount: discountAmount,
      discount_percent: discountPercent,
      paid_amount: paidAmount,
      referred_by: referredBy,
    };

    createOrderMutation.mutate(orderData);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Patient Registration & Order</h1>
        <p className={styles.subtitle}>Quick registration and order entry workflow</p>
      </div>

      {/* Global Patient Search */}
      <div className={styles.globalSearchSection}>
        <label className={styles.paymentLabel} style={{ marginBottom: '0.5rem', display: 'block' }}>Search Patient</label>
        <div className={styles.globalSearchWrapper}>
          <svg className={styles.searchIcon} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={globalSearchRef}
            type="text"
            value={globalSearchQuery}
            onChange={(e) => setGlobalSearchQuery(e.target.value)}
            className={styles.globalSearchInput}
            placeholder="Search by Patient Name or Mobile No..."
          />
          {loadingGlobalSearch && <span className={styles.loading} style={{ position: 'absolute', right: '1rem', top: '1rem' }}>...</span>}

          {showGlobalSuggestions && globalSuggestions.length > 0 && (
            <div className={styles.suggestions}>
              {globalSuggestions.map((patient) => (
                <div
                  key={patient.id}
                  className={styles.suggestionItem}
                  onClick={() => {
                    loadPatient(patient.id);
                    setGlobalSearchQuery('');
                    setShowGlobalSuggestions(false);
                  }}
                >
                  <div className={styles.suggestionMain}>{patient.full_name}</div>
                  <div className={styles.suggestionMeta}>
                    {patient.phone} • {patient.gender} • Age: {patient.age || 'N/A'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className={styles.splitView}>
        {/* Patient Form - Top Panel */}
        <div className={styles.card}>
          <h2 className={styles.sectionTitle}>
            {selectedPatient ? `Patient: ${selectedPatient.full_name}` : 'Patient Information'}
          </h2>

          {selectedPatient && (
            <div className={styles.patientIndicator}>
              Loaded existing patient - MRN: {selectedPatient.patient_id}
            </div>
          )}

          <form onSubmit={handlePatientSubmit} className={styles.form}>
            <div className={styles.formGroup}>
              <label>Mobile Number *</label>
              <div className={styles.autocompleteWrapper}>
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
                />
                {loadingPatients && <span className={styles.loading}>Searching...</span>}
                {showSuggestions && patientSuggestions.length > 0 && (
                  <div className={styles.suggestions}>
                    {patientSuggestions.map((patient, index) => (
                      <div
                        key={patient.id}
                        className={`${styles.suggestionItem} ${index === selectedSuggestionIndex ? styles.suggestionActive : ''
                          }`}
                        onClick={() => loadPatient(patient.id)}
                      >
                        <div className={styles.suggestionName}>{patient.full_name}</div>
                        <div className={styles.suggestionMeta}>
                          {patient.phone} • {patient.gender} • Age: {patient.age || 'N/A'}
                          {patient.last_visit && ` • Last visit: ${new Date(patient.last_visit).toLocaleDateString()}`}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>Full Name *</label>
                <input
                  type="text"
                  value={patientFormData.full_name || ''}
                  onChange={(e) => setPatientFormData({ ...patientFormData, full_name: e.target.value })}
                  className={styles.input}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Father/Husband Name</label>
                <input
                  type="text"
                  value={patientFormData.father_husband_name || ''}
                  onChange={(e) => setPatientFormData({ ...patientFormData, father_husband_name: e.target.value })}
                  className={styles.input}
                />
              </div>
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>Age (Years)</label>
                <input
                  type="number"
                  value={patientFormData.age_years || ''}
                  onChange={(e) =>
                    setPatientFormData({ ...patientFormData, age_years: parseInt(e.target.value) || undefined })
                  }
                  className={styles.input}
                  min="0"
                />
              </div>
              <div className={styles.formGroup}>
                <label>Gender *</label>
                <select
                  value={patientFormData.gender}
                  onChange={(e) => setPatientFormData({ ...patientFormData, gender: e.target.value as any })}
                  className={styles.select}
                  required
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div className={styles.formGroup}>
              <label>Address</label>
              <textarea
                value={patientFormData.address || ''}
                onChange={(e) => setPatientFormData({ ...patientFormData, address: e.target.value })}
                className={styles.textarea}
                rows={2}
              />
            </div>

            <div className={styles.formActions}>
              <button
                type="submit"
                className={styles.primaryButton}
                disabled={savePatientMutation.isPending}
              >
                {savePatientMutation.isPending
                  ? 'Saving...'
                  : selectedPatient
                    ? 'Update & Continue'
                    : 'Save & Continue'}
              </button>
            </div>
          </form>
        </div>

        {/* Order Form - Bottom Panel */}
        <div className={styles.card} style={{ opacity: selectedPatient ? 1 : 0.6, pointerEvents: selectedPatient ? 'auto' : 'none' }}>
          <h2 className={styles.sectionTitle}>Order Details</h2>

          <div className={styles.formGroup}>
            <label>Referred By</label>
            <input
              type="text"
              value={referredBy}
              onChange={(e) => setReferredBy(e.target.value)}
              className={styles.input}
              placeholder="Doctor name (optional)"
            />
          </div>

          <div className={styles.formGroup}>
            <label>Search & Add Tests</label>
            <div className={styles.autocompleteWrapper}>
              <input
                ref={testSearchRef}
                type="text"
                value={testQuery}
                onChange={(e) => setTestQuery(e.target.value)}
                onKeyDown={handleTestKeyDown}
                className={styles.input}
                placeholder="Type test name or code..."
              />
              {showTestSuggestions && testSuggestions.length > 0 && (
                <div className={styles.suggestions}>
                  {testSuggestions.map((test, index) => (
                    <div
                      key={test.id}
                      className={`${styles.suggestionItem} ${index === selectedTestIndex ? styles.suggestionActive : ''
                        }`}
                      onClick={() => addTest(test)}
                    >
                      <div className={styles.suggestionName}>
                        {test.test_code} - {test.test_name}
                      </div>
                      <div className={styles.suggestionMeta}>
                        {test.category_name} • Rs. {test.price}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {addedTests.length > 0 && (
            <div className={styles.testsList}>
              <h3>Added Tests</h3>
              <div className={styles.testsTable}>
                {addedTests.map((test) => (
                  <div key={test.id} className={styles.testRow}>
                    <div className={styles.testInfo}>
                      <strong>{test.test_code}</strong>
                      <span>{test.test_name}</span>
                    </div>
                    <div className={styles.testPrice}>Rs. {test.price}</div>
                    <button
                      type="button"
                      onClick={() => removeTest(test.id)}
                      className={styles.removeButton}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Payment Section - Inside the Bottom Card */}
          {addedTests.length > 0 && (
            <div className={styles.paymentSection}>
              <h2 className={styles.sectionTitle}>Payment</h2>

              <div className={styles.paymentSummary}>
                <div className={styles.paymentRow}>
                  <span>Total Amount:</span>
                  <strong>Rs. {totalAmount.toFixed(2)}</strong>
                </div>

                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Discount %</label>
                    <input
                      type="number"
                      value={discountPercent}
                      onChange={(e) => handleDiscountPercentChange(e.target.value)}
                      className={styles.input}
                      min="0"
                      max="100"
                      step="0.01"
                    />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Discount Amount</label>
                    <input
                      type="number"
                      value={discountAmount}
                      onChange={(e) => handleDiscountAmountChange(e.target.value)}
                      className={styles.input}
                      min="0"
                      step="0.01"
                    />
                  </div>
                </div>

                <div className={styles.paymentRow}>
                  <span>Net Payable:</span>
                  <strong className={styles.highlightAmount}>Rs. {netAmount.toFixed(2)}</strong>
                </div>

                <div className={styles.formGroup}>
                  <label>Paid Amount</label>
                  <input
                    type="number"
                    value={paidAmount}
                    onChange={(e) => setPaidAmount(e.target.value)}
                    className={styles.input}
                    min="0"
                    step="0.01"
                  />
                </div>

                <div className={styles.paymentRow}>
                  <span>Due Amount:</span>
                  <strong className={dueAmount > 0 ? styles.dueAmount : ''}>
                    Rs. {dueAmount.toFixed(2)}
                  </strong>
                </div>
              </div>

              <div className={styles.formActions}>
                <button
                  type="button"
                  onClick={handleCreateOrder}
                  className={styles.primaryButton}
                  disabled={createOrderMutation.isPending}
                >
                  {createOrderMutation.isPending ? 'Creating Order...' : 'Create Order / Invoice'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
