import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { labTerminalApi } from '../../api/services';
import type { LabTerminal, LabTerminalCreateRequest } from '../../types';
import styles from './LabTerminalsPage.module.css';

export default function LabTerminalsPage() {
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTerminal, setEditingTerminal] = useState<LabTerminal | null>(null);

  const { data: terminalsData, isLoading } = useQuery({
    queryKey: ['lab-terminals'],
    queryFn: () => labTerminalApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: (data: LabTerminalCreateRequest) => labTerminalApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lab-terminals'] });
      setIsCreateModalOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<LabTerminalCreateRequest> }) =>
      labTerminalApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lab-terminals'] });
      setEditingTerminal(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => labTerminalApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lab-terminals'] });
    },
  });

  const getNextMrnMutation = useMutation({
    mutationFn: (id: number) => labTerminalApi.getNextMrn(id),
    onSuccess: (data) => {
      alert(`Next MRN: ${data.next_mrn}`);
      queryClient.invalidateQueries({ queryKey: ['lab-terminals'] });
    },
  });

  const resetRangeMutation = useMutation({
    mutationFn: (id: number) => labTerminalApi.resetRange(id),
    onSuccess: () => {
      alert('Range reset successfully');
      queryClient.invalidateQueries({ queryKey: ['lab-terminals'] });
    },
  });

  const terminals = terminalsData?.results || [];

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data: LabTerminalCreateRequest = {
      code: formData.get('code') as string,
      name: formData.get('name') as string,
      offline_range_start: Number(formData.get('offline_range_start')),
      offline_range_end: Number(formData.get('offline_range_end')),
      is_active: formData.get('is_active') === 'on',
    };

    if (editingTerminal) {
      updateMutation.mutate({ id: editingTerminal.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Lab Terminals</h1>
        <button onClick={() => setIsCreateModalOpen(true)} className={styles.actionButton}>
          Create Terminal
        </button>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading...</div>
      ) : terminals.length === 0 ? (
        <div className={styles.noData}>No terminals found</div>
      ) : (
        <div className={styles.table}>
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Offline Range</th>
                <th>Current MRN</th>
                <th>Remaining</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {terminals.map((terminal) => {
                const remaining = terminal.offline_range_end - terminal.offline_current;
                return (
                  <tr key={terminal.id}>
                    <td>{terminal.code}</td>
                    <td>{terminal.name}</td>
                    <td>
                      {terminal.offline_range_start} - {terminal.offline_range_end}
                    </td>
                    <td>{terminal.offline_current || 'Not started'}</td>
                    <td>{remaining}</td>
                    <td>
                      <span className={terminal.is_active ? styles.active : styles.inactive}>
                        {terminal.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div className={styles.actionButtons}>
                        <button
                          onClick={() => getNextMrnMutation.mutate(terminal.id)}
                          className={styles.mrnButton}
                          disabled={!terminal.is_active || getNextMrnMutation.isPending}
                        >
                          Get Next MRN
                        </button>
                        <button
                          onClick={() => {
                            if (confirm('Are you sure you want to reset the MRN range? This action requires admin permissions.')) {
                              resetRangeMutation.mutate(terminal.id);
                            }
                          }}
                          className={styles.resetButton}
                        >
                          Reset Range
                        </button>
                        <button
                          onClick={() => setEditingTerminal(terminal)}
                          className={styles.editButton}
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => {
                            if (confirm('Are you sure you want to delete this terminal?')) {
                              deleteMutation.mutate(terminal.id);
                            }
                          }}
                          className={styles.deleteButton}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {(isCreateModalOpen || editingTerminal) && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h2>{editingTerminal ? 'Edit' : 'Create'} Lab Terminal</h2>
            <form onSubmit={handleSubmit}>
              <div className={styles.formGroup}>
                <label>Code *</label>
                <input
                  type="text"
                  name="code"
                  required
                  defaultValue={editingTerminal?.code}
                  className={styles.input}
                  placeholder="e.g., RECEP-1, LAB1-PC"
                />
              </div>

              <div className={styles.formGroup}>
                <label>Name *</label>
                <input
                  type="text"
                  name="name"
                  required
                  defaultValue={editingTerminal?.name}
                  className={styles.input}
                />
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label>Offline Range Start *</label>
                  <input
                    type="number"
                    name="offline_range_start"
                    required
                    defaultValue={editingTerminal?.offline_range_start}
                    className={styles.input}
                  />
                </div>
                <div className={styles.formGroup}>
                  <label>Offline Range End *</label>
                  <input
                    type="number"
                    name="offline_range_end"
                    required
                    defaultValue={editingTerminal?.offline_range_end}
                    className={styles.input}
                  />
                </div>
              </div>

              <div className={styles.formGroup}>
                <label>
                  <input
                    type="checkbox"
                    name="is_active"
                    defaultChecked={editingTerminal?.is_active ?? true}
                    className={styles.checkbox}
                  />
                  Active
                </label>
              </div>

              <div className={styles.modalActions}>
                <button type="submit" className={styles.submitButton}>
                  {editingTerminal ? 'Update' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsCreateModalOpen(false);
                    setEditingTerminal(null);
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


