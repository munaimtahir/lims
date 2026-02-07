import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sampleApi } from '../../api/services';
import { isSampleBarcodeEnabled } from '../../utils/featureFlags';
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
    mutationFn: ({
      id,
      status,
      barcode,
      postponement_reason,
    }: {
      id: number;
      status: string;
      barcode?: string;
      postponement_reason?: string;
    }) => sampleApi.updateStatus(id, status, barcode, postponement_reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples'] });
    },
  });

  const samples = samplesData?.results || [];
  const barcodeEnabled = isSampleBarcodeEnabled();

  const handleStatusUpdate = (sampleId: number, newStatus: string) => {
    if (newStatus === 'COLLECTED') {
      if (barcodeEnabled) {
        const barcodeInput = prompt('Enter barcode for this sample:');
        if (!barcodeInput) return;
        updateStatusMutation.mutate({ id: sampleId, status: newStatus, barcode: barcodeInput });
      } else {
        updateStatusMutation.mutate({ id: sampleId, status: newStatus });
      }
    } else if (newStatus === 'POSTPONED') {
      const reason = prompt('Enter reason for postponement:');
      if (!reason) return;
      updateStatusMutation.mutate({
        id: sampleId,
        status: newStatus,
        postponement_reason: reason,
      });
    } else {
      updateStatusMutation.mutate({ id: sampleId, status: newStatus });
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'PENDING':
        return styles.statusPending;
      case 'COLLECTED':
        return styles.statusCollected;
      case 'RECEIVED':
        return styles.statusReceived;
      case 'POSTPONED':
        return styles.statusPostponed;
      default:
        return styles.statusPending;
    }
  };

  const formatStatus = (status: string) => {
    if (!status) return '';
    return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase().replace('_', ' ');
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
            <option value="PENDING">Pending</option>
            <option value="COLLECTED">Collected</option>
            <option value="RECEIVED">Received</option>
            <option value="POSTPONED">Postponed</option>
            {/* Rejected hidden per current scope */}
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
                    {formatStatus(sample.status)}
                  </span>
                </td>
                <td>{sample.collected_at ? new Date(sample.collected_at).toLocaleString() : '-'}</td>
                <td>{sample.collected_by_name || '-'}</td>
                <td>
                  <div className={styles.actions}>
                    {(sample.status === 'PENDING' || sample.status === 'POSTPONED') && (
                      <>
                        <button
                          onClick={() => handleStatusUpdate(sample.id, 'COLLECTED')}
                          className={styles.actionButton}
                          disabled={updateStatusMutation.isPending}
                        >
                          Mark Collected
                        </button>
                        {sample.status !== 'POSTPONED' && (
                          <button
                            onClick={() => handleStatusUpdate(sample.id, 'POSTPONED')}
                            className={styles.rejectButton}
                            style={{ backgroundColor: '#64748b' }} // Grey for postpone
                            disabled={updateStatusMutation.isPending}
                          >
                            Postpone
                          </button>
                        )}
                      </>
                    )}
                    {sample.status === 'COLLECTED' && (
                      <button
                        onClick={() => handleStatusUpdate(sample.id, 'RECEIVED')}
                        className={styles.actionButton}
                        disabled={updateStatusMutation.isPending}
                      >
                        Mark Received
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
