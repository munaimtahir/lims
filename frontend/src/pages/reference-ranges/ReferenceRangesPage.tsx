import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { referenceRangeApi, laboratoryApi } from '../../api/services';
import type { ReferenceRange, ReferenceRangeCreateRequest, TestParameter } from '../../types';
import styles from './ReferenceRangesPage.module.css';

export default function ReferenceRangesPage() {
  const queryClient = useQueryClient();
  const [selectedParameter, setSelectedParameter] = useState<number | null>(null);
  const [genderFilter, setGenderFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingRange, setEditingRange] = useState<ReferenceRange | null>(null);

  const { data: parametersData } = useQuery({
    queryKey: ['test-parameters'],
    queryFn: () => laboratoryApi.getParameters({}),
  });

  const { data: rangesData, isLoading } = useQuery({
    queryKey: ['reference-ranges', selectedParameter, genderFilter, searchQuery],
    queryFn: () => referenceRangeApi.list({
      ...(selectedParameter && { parameter: selectedParameter }),
      ...(genderFilter && { gender: genderFilter }),
      ...(searchQuery && { search: searchQuery }),
    }),
  });

  const createMutation = useMutation({
    mutationFn: (data: ReferenceRangeCreateRequest) => referenceRangeApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reference-ranges'] });
      setIsCreateModalOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ReferenceRangeCreateRequest> }) =>
      referenceRangeApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reference-ranges'] });
      setEditingRange(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => referenceRangeApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reference-ranges'] });
    },
  });

  const ranges = rangesData?.results || [];
  const parameters = (parametersData?.results || []) as TestParameter[];

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data: ReferenceRangeCreateRequest = {
      parameter: Number(formData.get('parameter')),
      age_min: formData.get('age_min') ? Number(formData.get('age_min')) : undefined,
      age_max: formData.get('age_max') ? Number(formData.get('age_max')) : undefined,
      gender: formData.get('gender') as 'Male' | 'Female' | 'Both',
      reference_min: formData.get('reference_min') ? Number(formData.get('reference_min')) : undefined,
      reference_max: formData.get('reference_max') ? Number(formData.get('reference_max')) : undefined,
      critical_low: formData.get('critical_low') ? Number(formData.get('critical_low')) : undefined,
      critical_high: formData.get('critical_high') ? Number(formData.get('critical_high')) : undefined,
      notes: formData.get('notes')?.toString() || undefined,
    };

    if (editingRange) {
      updateMutation.mutate({ id: editingRange.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Reference Range Management</h1>
        <button onClick={() => setIsCreateModalOpen(true)} className={styles.actionButton}>
          Create Reference Range
        </button>
      </div>

      <div className={styles.filters}>
        <div className={styles.filter}>
          <label>Parameter:</label>
          <select
            value={selectedParameter || ''}
            onChange={(e) => setSelectedParameter(e.target.value ? Number(e.target.value) : null)}
            className={styles.select}
          >
            <option value="">All Parameters</option>
            {parameters.map((param: TestParameter) => (
              <option key={param.id} value={param.id}>
                {param.parameter_name} (ID: {param.id})
              </option>
            ))}
          </select>
        </div>

        <div className={styles.filter}>
          <label>Gender:</label>
          <select
            value={genderFilter}
            onChange={(e) => setGenderFilter(e.target.value)}
            className={styles.select}
          >
            <option value="">All</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Both">Both</option>
          </select>
        </div>

        <div className={styles.searchFilter}>
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
        </div>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading...</div>
      ) : ranges.length === 0 ? (
        <div className={styles.noData}>No reference ranges found</div>
      ) : (
        <div className={styles.table}>
          <table>
            <thead>
              <tr>
                <th>Parameter</th>
                <th>Test</th>
                <th>Age Range</th>
                <th>Gender</th>
                <th>Reference Range</th>
                <th>Critical Range</th>
                <th>Version</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {ranges.map((range) => (
                <tr key={range.id}>
                  <td>{range.parameter_name}</td>
                  <td>{range.test_name}</td>
                  <td>
                    {range.age_min !== null && range.age_min !== undefined
                      ? `${range.age_min}`
                      : '0'}-{range.age_max !== null && range.age_max !== undefined
                      ? `${range.age_max}`
                      : '∞'} years
                  </td>
                  <td>{range.gender}</td>
                  <td>
                    {range.reference_min !== null && range.reference_min !== undefined
                      ? range.reference_min
                      : '-'} - {range.reference_max !== null && range.reference_max !== undefined
                      ? range.reference_max
                      : '-'}
                  </td>
                  <td>
                    {range.critical_low !== null && range.critical_low !== undefined
                      ? range.critical_low
                      : '-'} / {range.critical_high !== null && range.critical_high !== undefined
                      ? range.critical_high
                      : '-'}
                  </td>
                  <td>{range.version}</td>
                  <td>
                    <span className={range.is_active ? styles.active : styles.inactive}>
                      {range.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => setEditingRange(range)}
                      className={styles.editButton}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Are you sure you want to delete this reference range?')) {
                          deleteMutation.mutate(range.id);
                        }
                      }}
                      className={styles.deleteButton}
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

      {(isCreateModalOpen || editingRange) && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h2>{editingRange ? 'Edit' : 'Create'} Reference Range</h2>
            <form onSubmit={handleSubmit}>
              <div className={styles.formGroup}>
                <label>Parameter *</label>
                <select
                  name="parameter"
                  required
                  defaultValue={editingRange?.parameter}
                  className={styles.select}
                >
                  <option value="">Select Parameter</option>
                  {parameters.map((param: TestParameter) => (
                    <option key={param.id} value={param.id}>
                      {param.parameter_name} (ID: {param.id})
                    </option>
                  ))}
                </select>
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label>Age Min (years)</label>
                  <input
                    type="number"
                    name="age_min"
                    defaultValue={editingRange?.age_min}
                    className={styles.input}
                  />
                </div>
                <div className={styles.formGroup}>
                  <label>Age Max (years)</label>
                  <input
                    type="number"
                    name="age_max"
                    defaultValue={editingRange?.age_max}
                    className={styles.input}
                  />
                </div>
              </div>

              <div className={styles.formGroup}>
                <label>Gender *</label>
                <select
                  name="gender"
                  required
                  defaultValue={editingRange?.gender || 'Both'}
                  className={styles.select}
                >
                  <option value="Both">Both</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label>Reference Min</label>
                  <input
                    type="number"
                    step="0.01"
                    name="reference_min"
                    defaultValue={editingRange?.reference_min}
                    className={styles.input}
                  />
                </div>
                <div className={styles.formGroup}>
                  <label>Reference Max</label>
                  <input
                    type="number"
                    step="0.01"
                    name="reference_max"
                    defaultValue={editingRange?.reference_max}
                    className={styles.input}
                  />
                </div>
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label>Critical Low</label>
                  <input
                    type="number"
                    step="0.01"
                    name="critical_low"
                    defaultValue={editingRange?.critical_low}
                    className={styles.input}
                  />
                </div>
                <div className={styles.formGroup}>
                  <label>Critical High</label>
                  <input
                    type="number"
                    step="0.01"
                    name="critical_high"
                    defaultValue={editingRange?.critical_high}
                    className={styles.input}
                  />
                </div>
              </div>

              <div className={styles.formGroup}>
                <label>Notes</label>
                <textarea
                  name="notes"
                  defaultValue={editingRange?.notes}
                  className={styles.textarea}
                  rows={3}
                />
              </div>

              <div className={styles.modalActions}>
                <button type="submit" className={styles.submitButton}>
                  {editingRange ? 'Update' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsCreateModalOpen(false);
                    setEditingRange(null);
                  }}
                  className={styles.cancelButton}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

