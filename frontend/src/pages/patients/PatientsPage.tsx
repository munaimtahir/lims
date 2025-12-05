import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { patientApi } from '../../api/services';
import type { Patient, PatientCreateRequest } from '../../types';
import styles from './PatientsPage.module.css';

export default function PatientsPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);

  const { data: patientsData, isLoading, error } = useQuery({
    queryKey: ['patients', searchQuery],
    queryFn: () => patientApi.list({ search: searchQuery || undefined }),
  });

  const createMutation = useMutation({
    mutationFn: (data: PatientCreateRequest) => patientApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      setIsModalOpen(false);
    },
  });

  const patients = patientsData?.results || [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Query will refetch automatically due to queryKey dependency
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Patients</h1>
        <button onClick={() => setIsModalOpen(true)} className={styles.addButton}>
          + Register Patient
        </button>
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
              <th>Actions</th>
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
                    View
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

      {isModalOpen && (
        <PatientFormModal
          onClose={() => setIsModalOpen(false)}
          onSubmit={(data) => createMutation.mutate(data)}
          isSubmitting={createMutation.isPending}
          error={createMutation.error}
        />
      )}

      {selectedPatient && (
        <PatientDetailModal
          patient={selectedPatient}
          onClose={() => setSelectedPatient(null)}
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
  const [formData, setFormData] = useState<PatientCreateRequest>({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'Male',
    phone: '',
    email: '',
    national_id: '',
    address: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h2>Register New Patient</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label>First Name *</label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label>Last Name *</label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                required
              />
            </div>
          </div>
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label>Date of Birth *</label>
              <input
                type="date"
                value={formData.date_of_birth}
                onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                required
              />
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
          </div>
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label>Phone *</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                required
                minLength={10}
              />
            </div>
            <div className={styles.formGroup}>
              <label>Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
          </div>
          <div className={styles.formGroup}>
            <label>National ID</label>
            <input
              type="text"
              value={formData.national_id}
              onChange={(e) => setFormData({ ...formData, national_id: e.target.value })}
            />
          </div>
          <div className={styles.formGroup}>
            <label>Address</label>
            <textarea
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              rows={2}
            />
          </div>
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

interface PatientDetailModalProps {
  patient: Patient;
  onClose: () => void;
}

function PatientDetailModal({ patient, onClose }: PatientDetailModalProps) {
  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h2>Patient Details</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <div className={styles.patientDetails}>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Patient ID:</span>
            <span className={styles.detailValue}>{patient.patient_id}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Name:</span>
            <span className={styles.detailValue}>{patient.full_name}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Date of Birth:</span>
            <span className={styles.detailValue}>{patient.date_of_birth}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Age:</span>
            <span className={styles.detailValue}>{patient.age} years</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Gender:</span>
            <span className={styles.detailValue}>{patient.gender}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Phone:</span>
            <span className={styles.detailValue}>{patient.phone}</span>
          </div>
          {patient.email && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Email:</span>
              <span className={styles.detailValue}>{patient.email}</span>
            </div>
          )}
          {patient.national_id && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>National ID:</span>
              <span className={styles.detailValue}>{patient.national_id}</span>
            </div>
          )}
          {patient.address && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Address:</span>
              <span className={styles.detailValue}>{patient.address}</span>
            </div>
          )}
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Total Orders:</span>
            <span className={styles.detailValue}>{patient.total_orders}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
