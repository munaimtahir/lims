import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sampleApi } from '../../api/services';
import type { SampleCollection } from '../../types';
import styles from './CollectionWorklistPage.module.css';

export default function CollectionWorklistPage() {
  const queryClient = useQueryClient();

  const { data: worklistData, isLoading, error } = useQuery({
    queryKey: ['collection-worklist'],
    queryFn: () => sampleApi.getCollectionWorklist(),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status, barcode }: { id: number; status: string; barcode?: string }) =>
      sampleApi.updateStatus(id, status, barcode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection-worklist'] });
      queryClient.invalidateQueries({ queryKey: ['samples'] });
    },
  });

  const samples = worklistData?.results || [];

  const handleCollect = (sampleId: number) => {
    const barcode = prompt('Enter barcode for this sample:');
    if (barcode) {
      updateStatusMutation.mutate({ id: sampleId, status: 'collected', barcode });
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Collection Worklist</h1>
        <p className={styles.subtitle}>Pending sample collections</p>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading worklist...</div>
      ) : error ? (
        <div className={styles.error}>Failed to load worklist</div>
      ) : (
        <>
          <div className={styles.stats}>
            <div className={styles.statCard}>
              <div className={styles.statValue}>{samples.length}</div>
              <div className={styles.statLabel}>Pending Collections</div>
            </div>
          </div>

          {samples.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No pending collections</p>
            </div>
          ) : (
            <div className={styles.worklist}>
              {samples.map((sample) => (
                <div key={sample.id} className={styles.worklistItem}>
                  <div className={styles.itemHeader}>
                    <div>
                      <h3>{sample.order_id}</h3>
                      <p className={styles.patientName}>{sample.patient_name}</p>
                    </div>
                    <span className={styles.priority}>Priority</span>
                  </div>
                  
                  <div className={styles.itemDetails}>
                    <div className={styles.detail}>
                      <span className={styles.label}>Sample Type:</span>
                      <span className={styles.value}>{sample.sample_type}</span>
                    </div>
                    {sample.notes && (
                      <div className={styles.detail}>
                        <span className={styles.label}>Notes:</span>
                        <span className={styles.value}>{sample.notes}</span>
                      </div>
                    )}
                  </div>

                  <div className={styles.itemActions}>
                    <button
                      onClick={() => handleCollect(sample.id)}
                      className={styles.collectButton}
                      disabled={updateStatusMutation.isPending}
                    >
                      Collect Sample
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
