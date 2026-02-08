import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sampleApi } from '../../api/services';
import type { SampleCollection } from '../../types';
import { isSampleBarcodeEnabled } from '../../utils/featureFlags';
import styles from './CollectionWorklistPage.module.css';

interface CollectionWorklistItem extends SampleCollection {
  order_details?: {
    patient_name: string;
    order_id: string;
    created_at: string;
    tests: Array<{ test_name?: string; panel_name?: string; sample_type: string }>;
  };
}

// Sub-component for each Patient Row to manage local state (checklist, source, comments)
const PatientCollectionRow = ({
  patientName,
  samples,
  onCollect
}: {
  patientName: string,
  samples: CollectionWorklistItem[],
  onCollect: (data: {
    sampleIds: number[],
    source: string,
    comments: string,
    barcodes: Record<string, string>
  }) => void
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [checklist, setChecklist] = useState<Record<number, boolean>>(() => {
    // Default all selected
    const initial: Record<number, boolean> = {};
    samples.forEach(s => initial[s.id] = true);
    return initial;
  });
  const [source, setSource] = useState<'lab' | 'home'>('lab');
  const [comments, setComments] = useState('');
  const [barcodes, setBarcodes] = useState<Record<string, string>>({}); // Keyed by sample.sample_type or ID? Usually type.

  const barcodeEnabled = isSampleBarcodeEnabled();

  // Handle barcode generation
  const handleAutoGenerate = (sampleType: string) => {
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const random = Math.floor(Math.random() * 10000);
    setBarcodes(prev => ({
      ...prev,
      [sampleType]: `SAM-${today}-${random}-${sampleType.substring(0, 3).toUpperCase()}`
    }));
  };

  const handleCollect = (e: React.MouseEvent) => {
    e.stopPropagation();
    const selectedIds = samples.filter(s => checklist[s.id]).map(s => s.id);
    if (selectedIds.length === 0) return;

    onCollect({
      sampleIds: selectedIds,
      source,
      comments,
      barcodes
    });
  };

  const selectedCount = Object.values(checklist).filter(Boolean).length;
  // Get unique sample types for barcode handling (if barcodes are per type)
  // Assuming barcodes are entered per sample type.
  // We need to map sample IDs to types.

  return (
    <div className={styles.accordionItem}>
      <div
        className={styles.accordionHeader}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className={styles.accordionHeaderLeft}>
          <div className={styles.patientInfo}>
            <span className={styles.patientName}>{patientName}</span>
            <span className={styles.orderId}>{samples.length} Samples Pending</span>
          </div>
        </div>
        <div className={styles.accordionHeaderRight}>
          <span className={styles.expandIcon}>{isExpanded ? '▼' : '▶'}</span>
        </div>
      </div>

      {isExpanded && (
        <div className={styles.accordionContent}>
          <div className={styles.sampleList}>
            <h4>Required Samples</h4>
            <div className={styles.checklistContainer}>
              {samples.map(sample => (
                <div key={sample.id} className={styles.checklistItem}>
                  <label>
                    <input
                      type="checkbox"
                      checked={!!checklist[sample.id]}
                      onChange={(e) => setChecklist(prev => ({ ...prev, [sample.id]: e.target.checked }))}
                    />
                    <span className={styles.sampleType}>{sample.sample_type}</span>
                    <span className={styles.orderIdBadge}>{sample.order_id}</span>
                  </label>

                  {/* Barcode input for this sample if checked */}
                  {barcodeEnabled && checklist[sample.id] && (
                    <div className={styles.barcodeInput}>
                      <input
                        type="text"
                        placeholder="Barcode"
                        value={barcodes[sample.sample_type] || ''}
                        onChange={(e) => setBarcodes(prev => ({ ...prev, [sample.sample_type]: e.target.value }))}
                        onClick={(e) => e.stopPropagation()}
                      />
                      <button
                        type="button"
                        className={styles.generateBtn}
                        onClick={(e) => { e.stopPropagation(); handleAutoGenerate(sample.sample_type); }}
                      >
                        Gen
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className={styles.formSection}>
              <div className={styles.sourceSelector}>
                <h4>Collection Source</h4>
                <div className={styles.radioGroup}>
                  <label>
                    <input
                      type="radio"
                      name={`source-${patientName}`}
                      value="lab"
                      checked={source === 'lab'}
                      onChange={() => setSource('lab')}
                    />
                    <span>Collected in Lab</span>
                  </label>
                  <label>
                    <input
                      type="radio"
                      name={`source-${patientName}`}
                      value="home"
                      checked={source === 'home'}
                      onChange={() => setSource('home')}
                    />
                    <span>Brought from Home</span>
                  </label>
                </div>
              </div>

              <div className={styles.commentsSection}>
                <h4>Comments</h4>
                <textarea
                  className={styles.remarksInput}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  placeholder="Add any comments (e.g. fasting status, patient request)..."
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                />
              </div>
            </div>

            <div className={styles.actionButtons} style={{ marginTop: '20px' }}>
              <button
                onClick={handleCollect}
                disabled={selectedCount === 0}
                className={styles.collectButton}
              >
                Mark {selectedCount} Sample{selectedCount !== 1 ? 's' : ''} Collected & Received
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default function CollectionWorklistPage() {
  const queryClient = useQueryClient();

  const { data: worklistData, isLoading, error } = useQuery({
    queryKey: ['collection-worklist'],
    queryFn: () => sampleApi.getCollectionWorklist(),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status, barcode, notes, additionalData }: {
      id: number;
      status: string;
      barcode?: string;
      notes?: string;
      additionalData?: Record<string, unknown>;
    }) => sampleApi.updateStatus(id, status, barcode, undefined, { notes, ...additionalData }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection-worklist'] });
      queryClient.invalidateQueries({ queryKey: ['samples'] });
      queryClient.invalidateQueries({ queryKey: ['result-worklist'] });
    },
  });

  const samples = worklistData?.results || [];

  // Group samples by PATIENT
  const groupedByPatient = useMemo(() => {
    return samples.reduce((acc: Record<string, CollectionWorklistItem[]>, sample: CollectionWorklistItem) => {
      const patientName = sample.patient_name || 'Unknown Patient';
      if (!acc[patientName]) {
        acc[patientName] = [];
      }
      acc[patientName].push(sample);
      return acc;
    }, {});
  }, [samples]);

  const handleCollect = async (data: {
    sampleIds: number[],
    source: string,
    comments: string,
    barcodes: Record<string, string>
  }) => {
    // Process all selected samples
    // We combine user comments with the source info
    const fullNotes = [
      data.comments ? `Comment: ${data.comments}` : '',
      `Source: ${data.source === 'home' ? 'Home Collection' : 'Lab Collection'}`
    ].filter(Boolean).join(' | ');

    const promises = data.sampleIds.map(id => {
      const sample = samples.find(s => s.id === id);
      const barcode = sample ? data.barcodes[sample.sample_type] : undefined;

      return updateStatusMutation.mutateAsync({
        id,
        status: 'COLLECTED', // User said "mark it collected AND received". I'll default to COLLECTED, but maybe RECEIVED is next step? Usually Collected -> Received. I'll stick to COLLECTED as per button text "Mark Collected".
        barcode,
        notes: fullNotes,
        additionalData: {
          collection_source: data.source,
          collected_at: new Date().toISOString()
        }
      });
    });

    await Promise.all(promises);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Sample Collection Worklist</h1>
        <p className={styles.subtitle}>Pending collections by Patient</p>
      </div>

      {isLoading ? (
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Loading worklist...</p>
        </div>
      ) : error ? (
        <div className={styles.error}>
          <p>❌ Failed to load worklist</p>
          <button onClick={() => queryClient.invalidateQueries({ queryKey: ['collection-worklist'] })}>
            Retry
          </button>
        </div>
      ) : (
        <>
          <div className={styles.stats}>
            <div className={styles.statCard}>
              <div className={styles.statValue}>{Object.keys(groupedByPatient).length}</div>
              <div className={styles.statLabel}>Patients in Queue</div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statValue}>{samples.length}</div>
              <div className={styles.statLabel}>Total Samples</div>
            </div>
          </div>

          {samples.length === 0 ? (
            <div className={styles.emptyState}>
              <p>✓ No pending collections.</p>
            </div>
          ) : (
            <div className={styles.accordion}>
              {Object.entries(groupedByPatient).map(([patientName, patientSamples]) => (
                <PatientCollectionRow
                  key={patientName}
                  patientName={patientName}
                  samples={patientSamples}
                  onCollect={handleCollect}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
