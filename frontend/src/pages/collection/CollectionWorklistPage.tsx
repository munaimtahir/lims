import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sampleApi } from '../../api/services';
import type { SampleCollection } from '../../types';
import { isSampleBarcodeCollectionEnabled } from '../../utils/featureFlags';
import styles from './CollectionWorklistPage.module.css';

export default function CollectionWorklistPage() {
  const queryClient = useQueryClient();
  const [selectedSample, setSelectedSample] = useState<SampleCollection | null>(null);
  const [isCollectModalOpen, setIsCollectModalOpen] = useState(false);
  const barcodeEnabled = isSampleBarcodeCollectionEnabled();

  const { data: worklistData, isLoading, error } = useQuery({
    queryKey: ['collection-worklist'],
    queryFn: () => sampleApi.getCollectionWorklist(),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status, barcode }: { id: number; status: string; barcode?: string }) => sampleApi.updateStatus(id, status, barcode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection-worklist'] });
      queryClient.invalidateQueries({ queryKey: ['samples'] });
      setIsCollectModalOpen(false);
      setSelectedSample(null);
    },
  });

  const samples = worklistData?.results || [];

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Collection Worklist</h1>
        <p className={styles.subtitle}>Pending sample collections for Phlebotomy</p>
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
            <div className={styles.emptyState}><p>No pending collections. Great job!</p></div>
          ) : (
            <div className={styles.grid}>
              {samples.map((sample: SampleCollection) => (
                <div key={sample.id} className={styles.card}>
                  <div className={styles.cardHeader}><h3>{sample.order_id}</h3><span className={styles.priority}>Routine</span></div>
                  <div className={styles.cardBody}>
                    <div className={styles.detailRow}><span className={styles.label}>Patient:</span><span className={styles.value}>{sample.patient_name}</span></div>
                    <div className={styles.detailRow}><span className={styles.label}>Sample:</span><span className={styles.value}>{sample.sample_type}</span></div>
                    {sample.notes && <div className={styles.detailRow}><span className={styles.label}>Notes:</span><span className={styles.value}>{sample.notes}</span></div>}
                  </div>

                  <div className={styles.cardActions}>
                    <button
                      onClick={() => {
                        if (!barcodeEnabled) {
                          updateStatusMutation.mutate({ id: sample.id, status: 'COLLECTED' });
                          return;
                        }
                        setSelectedSample(sample);
                        setIsCollectModalOpen(true);
                      }}
                      className={styles.collectButton}
                    >
                      Collect
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {isCollectModalOpen && selectedSample && barcodeEnabled && (
        <CollectSampleModal
          sample={selectedSample}
          onClose={() => setIsCollectModalOpen(false)}
          onConfirm={(barcode) => updateStatusMutation.mutate({ id: selectedSample.id, status: 'COLLECTED', barcode })}
          isSubmitting={updateStatusMutation.isPending}
        />
      )}
    </div>
  );
}

interface CollectSampleModalProps {
  sample: SampleCollection;
  onClose: () => void;
  onConfirm: (barcode: string) => void;
  isSubmitting: boolean;
}

function CollectSampleModal({ sample, onClose, onConfirm, isSubmitting }: CollectSampleModalProps) {
  const [barcode, setBarcode] = useState('');

  const handleAutoGenerate = () => {
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    setBarcode(`SAM-${today}-${Math.floor(Math.random() * 10000)}`);
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h2>Collect Sample</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <div className={styles.modalBody}>
          <p>Collecting <strong>{sample.sample_type}</strong> for <strong>{sample.patient_name}</strong></p>
          <div className={styles.formGroup}>
            <label>Barcode / Label ID</label>
            <div className={styles.inputGroup}>
              <input type="text" value={barcode} onChange={(e) => setBarcode(e.target.value)} placeholder="Scan or enter barcode" autoFocus />
              <button type="button" onClick={handleAutoGenerate} className={styles.secondaryButton}>Generate</button>
            </div>
          </div>
          <div className={styles.modalActions}>
            <button onClick={onClose} className={styles.cancelButton}>Cancel</button>
            <button onClick={() => onConfirm(barcode)} disabled={!barcode || isSubmitting} className={styles.submitButton}>
              {isSubmitting ? 'Confirming...' : 'Confirm Collection'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
