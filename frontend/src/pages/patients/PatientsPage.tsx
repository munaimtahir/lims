import { useEffect, useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { laboratoryApi, orderApi, patientApi } from '../../api/services';
import type { Order, Patient, PatientCreateRequest, OrderCreateRequest } from '../../types';
import { calculateAgeFromDob, calculateDobFromAge } from '../../utils/ageDob';
import { formatDateDDMMYY, normalizeDateInputToISO } from '../../utils/dateFormat';
import { useBranding } from '../../contexts/BrandingContext';
import { formatCurrency } from '../../utils/currency';
import styles from './PatientsPage.module.css';

export default function PatientsPage() {
  const queryClient = useQueryClient();
  const { branding } = useBranding();
  const currency = branding?.currency || 'PKR';
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [isOrderModalOpen, setIsOrderModalOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  const { data: patientsData, isLoading, error } = useQuery({
    queryKey: ['patients', searchQuery],
    queryFn: () => patientApi.list({ search: searchQuery || undefined }),
  });

  const { data: ordersData, isLoading: ordersLoading } = useQuery({
    queryKey: ['patient-orders', selectedPatient?.id],
    queryFn: () => orderApi.list({ patient: selectedPatient?.id }),
    enabled: !!selectedPatient,
  });

  const createPatientMutation = useMutation({
    mutationFn: (data: PatientCreateRequest) => patientApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      setIsModalOpen(false);
    },
  });

  const patients = patientsData?.results || [];
  const orders = ordersData?.results || [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1>Patients</h1>
          <p className={styles.subtitle}>Search patients, view history, and create orders.</p>
        </div>
        <div className={styles.headerActions}>
          <button onClick={() => setIsModalOpen(true)} className={styles.addButton}>
            + Register Patient
          </button>
          <button
            onClick={() => setIsOrderModalOpen(true)}
            className={styles.primaryButton}
            disabled={!selectedPatient}
          >
            + New Order
          </button>
        </div>
      </div>

      <form onSubmit={handleSearch} className={styles.searchForm}>
        <input
          type="text"
          placeholder="Search by name, phone, or patient ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className={styles.searchInput}
        />
        <button type="submit" className={styles.searchButton}>
          Search
        </button>
      </form>

      <div className={styles.layoutGrid}>
        <div className={styles.listCard}>
          {isLoading ? (
            <div className={styles.loading}>Loading patients...</div>
          ) : error ? (
            <div className={styles.error}>Failed to load patients</div>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Patient ID</th>
                  <th>Name</th>
                  <th>Age/Gender</th>
                  <th>Phone</th>
                  <th>Last Visit</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {patients.map((patient) => (
                  <tr key={patient.id}>
                    <td>{patient.patient_id}</td>
                    <td>{patient.full_name}</td>
                    <td>{patient.age}y / {patient.gender}</td>
                    <td>{patient.phone}</td>
                    <td>{patient.last_visit || 'N/A'}</td>
                    <td>
                      <button
                        onClick={() => setSelectedPatient(patient)}
                        className={styles.viewButton}
                      >
                        Select
                      </button>
                    </td>
                  </tr>
                ))}
                {patients.length === 0 && (
                  <tr>
                    <td colSpan={6} className={styles.noData}>
                      No patients found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>

        <div className={styles.detailCard}>
          {selectedPatient ? (
            <>
              <div className={styles.detailHeader}>
                <h2>{selectedPatient.full_name}</h2>
                <span className={styles.badge}>{selectedPatient.patient_id}</span>
              </div>
              <div className={styles.detailGrid}>
                <div>
                  <span className={styles.detailLabel}>Mobile</span>
                  <span className={styles.detailValue}>{selectedPatient.phone}</span>
                </div>
                <div>
                  <span className={styles.detailLabel}>Gender</span>
                  <span className={styles.detailValue}>{selectedPatient.gender}</span>
                </div>
                <div>
                  <span className={styles.detailLabel}>DOB</span>
                  <span className={styles.detailValue}>{formatDateDDMMYY(selectedPatient.date_of_birth) || 'N/A'}</span>
                </div>
                <div>
                  <span className={styles.detailLabel}>Age</span>
                  <span className={styles.detailValue}>{selectedPatient.age ?? 'N/A'} years</span>
                </div>
                {selectedPatient.father_husband_name && (
                  <div>
                    <span className={styles.detailLabel}>Father/Husband</span>
                    <span className={styles.detailValue}>{selectedPatient.father_husband_name}</span>
                  </div>
                )}
                {selectedPatient.cnic && (
                  <div>
                    <span className={styles.detailLabel}>CNIC</span>
                    <span className={styles.detailValue}>{selectedPatient.cnic}</span>
                  </div>
                )}
              </div>

              <div className={styles.sectionHeader}>
                <h3>Orders</h3>
              </div>
              {ordersLoading ? (
                <div className={styles.loading}>Loading orders...</div>
              ) : (
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Order ID</th>
                      <th>Status</th>
                      <th>Amount</th>
                      <th>Date</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order) => (
                      <tr key={order.id}>
                        <td>{order.order_id}</td>
                        <td>{order.status.replace('_', ' ')}</td>
                        <td>{formatCurrency(order.net_amount, currency)}</td>
                        <td>{new Date(order.created_at).toLocaleDateString()}</td>
                        <td>
                          <button
                            onClick={() => setSelectedOrder(order)}
                            className={styles.viewButton}
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                    {orders.length === 0 && (
                      <tr>
                        <td colSpan={5} className={styles.noData}>
                          No orders found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}
            </>
          ) : (
            <div className={styles.emptyState}>Select a patient to see details and orders.</div>
          )}
        </div>
      </div>

      {isModalOpen && (
        <PatientFormModal
          onClose={() => setIsModalOpen(false)}
          onSubmit={(data) => createPatientMutation.mutate(data)}
          isSubmitting={createPatientMutation.isPending}
          error={createPatientMutation.error}
        />
      )}

      {isOrderModalOpen && selectedPatient && (
        <CreateOrderModal
          patient={selectedPatient}
          onClose={() => setIsOrderModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['patient-orders', selectedPatient.id] });
            setIsOrderModalOpen(false);
          }}
        />
      )}

      {selectedOrder && (
        <OrderDetailModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
        />
      )}
    </div>
  );
}

interface PatientFormModalProps {
  onClose: () => void;
  onSubmit: (data: PatientCreateRequest) => void;
  isSubmitting: boolean;
  error: Error | null;
}

function PatientFormModal({ onClose, onSubmit, isSubmitting, error }: PatientFormModalProps) {
  const [formError, setFormError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    gender: 'Male' as 'Male' | 'Female' | 'Other',
    date_of_birth: '',
    age_years: '',
    age_months: '',
    age_days: '',
    father_husband_name: '',
    cnic: '',
    email: '',
  });

  const handleDobChange = (value: string) => {
    setFormData((prev) => {
      const normalizedValue = normalizeDateInputToISO(value);
      if (!normalizedValue) {
        return {
          ...prev,
          date_of_birth: '',
          age_years: '',
          age_months: '',
          age_days: '',
        };
      }

      const age = calculateAgeFromDob(normalizedValue);
      if (age) {
        return {
          ...prev,
          date_of_birth: normalizedValue,
          age_years: age.years.toString(),
          age_months: age.months.toString(),
          age_days: age.days.toString(),
        };
      }

      return { ...prev, date_of_birth: normalizedValue };
    });
  };

  const handleAgeChange = (field: 'age_years' | 'age_months' | 'age_days', value: string) => {
    setFormData((prev) => {
      const next = { ...prev, [field]: value };

      const years = next.age_years === '' ? null : Number(next.age_years);
      const months = Number(next.age_months || 0);
      const days = Number(next.age_days || 0);

      if (years === null || Number.isNaN(years)) {
        return { ...next, date_of_birth: '' };
      }

      const dob = calculateDobFromAge(years, months, days);
      if (dob) {
        return { ...next, date_of_birth: dob };
      }

      return next;
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formData.date_of_birth && formData.age_years === '') {
      setFormError('Please provide date of birth or age in years.');
      return;
    }

    onSubmit({
      full_name: formData.full_name,
      phone: formData.phone,
      gender: formData.gender,
      date_of_birth: formData.date_of_birth || undefined,
      age_years: formData.age_years === '' ? undefined : Number(formData.age_years),
      age_months: formData.age_months === '' ? undefined : Number(formData.age_months),
      age_days: formData.age_days === '' ? undefined : Number(formData.age_days),
      father_husband_name: formData.father_husband_name || undefined,
      cnic: formData.cnic || undefined,
      email: formData.email || undefined,
    });
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h2>Register New Patient</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <label>Mobile Number *</label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              required
              minLength={10}
            />
          </div>
          <div className={styles.formGroup}>
            <label>Name *</label>
            <input
              type="text"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              required
            />
          </div>
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label>Age</label>
              <div className={styles.ageInputs}>
                <div className={styles.ageField}>
                  <input
                    type="number"
                    min="0"
                    value={formData.age_years}
                    onChange={(e) => handleAgeChange('age_years', e.target.value)}
                  />
                  <span>years</span>
                </div>
                <div className={styles.ageField}>
                  <input
                    type="number"
                    min="0"
                    value={formData.age_months}
                    onChange={(e) => handleAgeChange('age_months', e.target.value)}
                  />
                  <span>months</span>
                </div>
                <div className={styles.ageField}>
                  <input
                    type="number"
                    min="0"
                    value={formData.age_days}
                    onChange={(e) => handleAgeChange('age_days', e.target.value)}
                  />
                  <span>days</span>
                </div>
              </div>
            </div>
            <div className={styles.formGroup}>
              <label>Date of Birth</label>
              <input
                type="text"
                placeholder="DD/MM/YY"
                value={formatDateDDMMYY(formData.date_of_birth)}
                onChange={(e) => handleDobChange(e.target.value)}
              />
            </div>
          </div>
          <div className={styles.formGroup}>
            <label>Gender *</label>
            <select
              value={formData.gender}
              onChange={(e) => setFormData({ ...formData, gender: e.target.value as 'Male' | 'Female' | 'Other' })}
              required
            >
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div className={styles.formGroup}>
            <label>Father/Husband Name</label>
            <input
              type="text"
              value={formData.father_husband_name}
              onChange={(e) => setFormData({ ...formData, father_husband_name: e.target.value })}
            />
          </div>
          <div className={styles.formGroup}>
            <label>CNIC</label>
            <input
              type="text"
              value={formData.cnic}
              onChange={(e) => setFormData({ ...formData, cnic: e.target.value })}
            />
          </div>
          <div className={styles.formGroup}>
            <label>Email Address</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>
          {formError && <div className={styles.formError}>{formError}</div>}
          {error && <div className={styles.formError}>{error.message}</div>}
          <div className={styles.formActions}>
            <button type="button" onClick={onClose} className={styles.cancelButton}>
              Cancel
            </button>
            <button type="submit" disabled={isSubmitting} className={styles.submitButton}>
              {isSubmitting ? 'Registering...' : 'Register Patient'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function CreateOrderModal({ patient, onClose, onSuccess }: { patient: Patient; onClose: () => void; onSuccess: () => void }) {
  const { branding } = useBranding();
  const currency = branding?.currency || 'PKR';
  const [selectedTests, setSelectedTests] = useState<number[]>([]);
  const [selectedPanels, setSelectedPanels] = useState<number[]>([]);
  const [discount, setDiscount] = useState('0');
  const [referredBy, setReferredBy] = useState('');

  useEffect(() => {
    setReferredBy(patient.last_order_referred_by || patient.default_referred_by || '');
  }, [patient]);

  const { data: testsData } = useQuery({
    queryKey: ['tests'],
    queryFn: () => laboratoryApi.getTests({ is_active: true }),
  });

  const { data: panelsData } = useQuery({
    queryKey: ['panels'],
    queryFn: () => laboratoryApi.getPanels({ is_active: true }),
  });

  const createMutation = useMutation({
    mutationFn: (data: OrderCreateRequest) => orderApi.create(data),
    onSuccess,
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail ??
        error?.message ??
        'Failed to create order. Please try again.';
      alert(message);
    },
  });

  const tests = testsData?.results || [];
  const panels = panelsData?.results || [];

  // Memoize the Maps to avoid recreating them on every render
  const testsById = useMemo(() => new Map(tests.map((t) => [t.test_id, t])), [tests]);
  const panelsById = useMemo(() => new Map(panels.map((p) => [p.id, p])), [panels]);

  const calculateTotal = () => {
    let total = 0;
    selectedTests.forEach((id) => {
      const test = testsById.get(id);
      if (test) total += parseFloat(test.price);
    });
    selectedPanels.forEach((id) => {
      const panel = panelsById.get(id);
      if (panel) total += parseFloat(panel.price);
    });
    return total - parseFloat(discount || '0');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    createMutation.mutate({
      patient: patient.id,
      test_ids: selectedTests,
      panel_ids: selectedPanels,
      discount: discount || '0',
      referred_by: referredBy || undefined,
    });
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h2>Create New Order</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <label>Patient</label>
            <div className={styles.selectedPatient}>
              <span>{patient.full_name} ({patient.patient_id})</span>
            </div>
          </div>
          <div className={styles.formGroup}>
            <label>Referred By</label>
            <input
              type="text"
              value={referredBy}
              onChange={(e) => setReferredBy(e.target.value)}
              placeholder="Doctor/Clinic"
            />
          </div>
          <div className={styles.formGroup}>
            <label>Tests</label>
            <div className={styles.checkboxGrid}>
              {tests.map((test) => (
                <label key={test.test_id} className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={selectedTests.includes(test.test_id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTests([...selectedTests, test.test_id]);
                      } else {
                        setSelectedTests(selectedTests.filter((id) => id !== test.test_id));
                      }
                    }}
                  />
                  <span>{test.test_name} - {formatCurrency(test.price, currency)}</span>
                </label>
              ))}
            </div>
          </div>
          <div className={styles.formGroup}>
            <label>Panels</label>
            <div className={styles.checkboxGrid}>
              {panels.map((panel) => (
                <label key={panel.id} className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={selectedPanels.includes(panel.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedPanels([...selectedPanels, panel.id]);
                      } else {
                        setSelectedPanels(selectedPanels.filter((id) => id !== panel.id));
                      }
                    }}
                  />
                  <span>{panel.panel_name} - {formatCurrency(panel.price, currency)}</span>
                </label>
              ))}
            </div>
          </div>
          <div className={styles.formGroup}>
            <label>Discount ({currency})</label>
            <input
              type="number"
              value={discount}
              onChange={(e) => setDiscount(e.target.value)}
              min="0"
            />
          </div>
          <div className={styles.totalSection}>
            <span>Total Amount:</span>
            <span className={styles.totalAmount}>{formatCurrency(calculateTotal().toFixed(2), currency)}</span>
          </div>
          <div className={styles.formActions}>
            <button type="button" onClick={onClose} className={styles.cancelButton}>
              Cancel
            </button>
            <button
              type="submit"
              disabled={(selectedTests.length === 0 && selectedPanels.length === 0) || createMutation.isPending}
              className={styles.submitButton}
            >
              {createMutation.isPending ? 'Creating...' : 'Create Order'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function OrderDetailModal({ order, onClose }: { order: Order; onClose: () => void }) {
  const { branding } = useBranding();
  const currency = branding?.currency || 'PKR';
  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h2>Order Details</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <div className={styles.patientDetails}>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Order ID:</span>
            <span className={styles.detailValue}>{order.order_id}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Patient:</span>
            <span className={styles.detailValue}>{order.patient_name}</span>
          </div>
          {order.referred_by && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Referred By:</span>
              <span className={styles.detailValue}>{order.referred_by}</span>
            </div>
          )}
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Status:</span>
            <span className={styles.detailValue}>{order.status}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Total:</span>
            <span className={styles.detailValue}>{formatCurrency(order.net_amount, currency)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
