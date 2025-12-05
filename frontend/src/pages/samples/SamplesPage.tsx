import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sampleApi } from '../../api/services';
import type { SampleCollection } from '../../types';
import styles from './SamplesPage.module.css';

export default function SamplesPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  const { data: samplesData, isLoading, error } = useQuery({
    queryKey: ['samples', statusFilter, searchQuery],
    queryFn: () => sampleApi.list({
      ...(statusFilter && { status: statusFilter }),
      ...(searchQuery && { search: searchQuery }),
    }),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status, barcode }: { id: number; status: string; barcode?: string }) =>
      sampleApi.updateStatus(id, status, barcode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples'] });
    },
  });

  const samples = samplesData?.results || [];

  const handleStatusUpdate = (sampleId: number, newStatus: string, barcode?: string) => {
    if (newStatus === 'collected' && !barcode) {
      const barcodeInput = prompt('Enter barcode for this sample:');
      if (!barcodeInput) return;
      updateStatusMutation.mutate({ id: sampleId, status: newStatus, barcode: barcodeInput });
    } else {
      updateStatusMutation.mutate({ id: sampleId, status: newStatus });
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'pending':
        return styles.statusPending;
      case 'collected':
        return styles.statusCollected;
      case 'received':
        return styles.statusReceived;
      case 'rejected':
        return styles.statusRejected;
      default:
        return styles.statusPending;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Sample Collections</h1>
      </div>

      <div className={styles.filters}>
        <div className={styles.statusFilter}>
          <label>Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className={styles.select}
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="collected">Collected</option>
            <option value="received">Received</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        <div className={styles.searchFilter}>
          <input
            type="text"
            placeholder="Search by order ID, barcode, or patient name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
        </div>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading samples...</div>
      ) : error ? (
        <div className={styles.error}>Failed to load samples</div>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Patient</th>
              <th>Sample Type</th>
              <th>Barcode</th>
              <th>Status</th>
              <th>Collected At</th>
              <th>Collected By</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {samples.map((sample) => (
              <tr key={sample.id}>
                <td>{sample.order_id}</td>
                <td>{sample.patient_name}</td>
                <td>{sample.sample_type}</td>
                <td>{sample.barcode || '-'}</td>
                <td>
                  <span className={`${styles.statusBadge} ${getStatusBadgeClass(sample.status)}`}>
                    {sample.status}
                  </span>
                </td>
                <td>{sample.collected_at ? new Date(sample.collected_at).toLocaleString() : '-'}</td>
                <td>{sample.collected_by_name || '-'}</td>
                <td>
                  <div className={styles.actions}>
                    {sample.status === 'pending' && (
                      <button
                        onClick={() => handleStatusUpdate(sample.id, 'collected')}
                        className={styles.actionButton}
                        disabled={updateStatusMutation.isPending}
                      >
                        Mark Collected
                      </button>
                    )}
                    {sample.status === 'collected' && (
                      <button
                        onClick={() => handleStatusUpdate(sample.id, 'received')}
                        className={styles.actionButton}
                        disabled={updateStatusMutation.isPending}
                      >
                        Mark Received
                      </button>
                    )}
                    {sample.status !== 'rejected' && (
                      <button
                        onClick={() => handleStatusUpdate(sample.id, 'rejected')}
                        className={styles.rejectButton}
                        disabled={updateStatusMutation.isPending}
                      >
                        Reject
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {samples.length === 0 && (
              <tr>
                <td colSpan={8} className={styles.noData}>
                  No samples found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
