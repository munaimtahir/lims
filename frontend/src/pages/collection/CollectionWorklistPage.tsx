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
  sample_type: string;
  order_item: number;
  order_id: string; // from serializer
  patient_name: string; // from serializer
  created_at: string; // from serializer
}

// Modal Component for Sample Collection Checklist
const CollectionModal = ({
  patientName,
  samples,
  onConfirm,
  onCancel,
}: {
  patientName: string;
  samples: CollectionWorklistItem[];
  onConfirm: (data: { ids: number[], source: string, barcodes: Record<string, string>, comments: string }) => void;
  onCancel: () => void;
}) => {
  const [checklist, setChecklist] = useState<Record<number, boolean>>(() => {
    const initial: Record<number, boolean> = {};
    samples.forEach(s => initial[s.id] = true);
    return initial;
  });
  const [source, setSource] = useState<'lab' | 'home'>('lab');
  const [comments, setComments] = useState('');
  const [barcodes, setBarcodes] = useState<Record<string, string>>({});

  const barcodeEnabled = isSampleBarcodeEnabled();

  const handleAutoGenerate = (sampleType: string) => {
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const random = Math.floor(Math.random() * 10000);
    setBarcodes(prev => ({
      ...prev,
      [sampleType]: `SAM-${today}-${random}-${sampleType.substring(0, 3).toUpperCase()}`
    }));
  };

  const selectedCount = Object.values(checklist).filter(Boolean).length;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <div className={styles.modalHeader}>
          <h3>Confirm Collection</h3>
          <button onClick={onCancel} className={styles.closeButton}>&times;</button>
        </div>

        <div className={styles.modalBody}>
          <div className={styles.patientSummary}>
            <strong>Patient:</strong> {patientName} <br />
            <small>Lab ID/Order: {samples[0]?.order_id}</small>
          </div>

          <h4>Select Samples to Collect</h4>
          <div className={styles.checklistContainer}>
            {samples.map(sample => (
              <div key={sample.id} className={styles.checklistItem}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '100%' }}>
                  <input
                    type="checkbox"
                    checked={!!checklist[sample.id]}
                    onChange={(e) => setChecklist(prev => ({ ...prev, [sample.id]: e.target.checked }))}
                  />
                  <div>
                    <span className={styles.sampleType}>{sample.sample_type}</span>
                    <div style={{ fontSize: '0.8em', color: '#666' }}>ID: {sample.id}</div>
                  </div>
                </label>

                {barcodeEnabled && checklist[sample.id] && (
                  <div className={styles.barcodeInput}>
                    <input
                      type="text"
                      placeholder="Barcode"
                      value={barcodes[sample.sample_type] || ''}
                      onChange={(e) => setBarcodes(prev => ({ ...prev, [sample.sample_type]: e.target.value }))}
                    />
                    <button
                      type="button"
                      className={styles.generateBtn}
                      onClick={() => handleAutoGenerate(sample.sample_type)}
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
                    name="source"
                    value="lab"
                    checked={source === 'lab'}
                    onChange={() => setSource('lab')}
                  />
                  Collected in Lab
                </label>
                <label>
                  <input
                    type="radio"
                    name="source"
                    value="home"
                    checked={source === 'home'}
                    onChange={() => setSource('home')}
                  />
                  Brought from Home
                </label>
              </div>
            </div>

            <div className={styles.commentsSection}>
              <h4>Comments (Optional)</h4>
              <textarea
                className={styles.remarksInput}
                rows={2}
                placeholder="Notes..."
                value={comments}
                onChange={(e) => setComments(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className={styles.modalFooter}>
          <button onClick={onCancel} className={styles.cancelButton}>Cancel</button>
          <button
            onClick={() => {
              const ids = samples.filter(s => checklist[s.id]).map(s => s.id);
              if (ids.length > 0) {
                onConfirm({ ids, source, barcodes, comments });
              }
            }}
            disabled={selectedCount === 0}
            className={styles.collectButton}
          >
            Confirm & Mark Received ({selectedCount})
          </button>
        </div>
      </div>
    </div>
  );
};

// Patient Row Component
const PatientCollectionRow = ({
  patientName,
  samples,
  onOpenModal
}: {
  patientName: string,
  samples: CollectionWorklistItem[],
  onOpenModal: () => void
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const firstSample = samples[0];
  const orderId = firstSample?.order_id || 'Unknown';
  const registeredAt = firstSample?.created_at ? new Date(firstSample.created_at).toLocaleString() : 'N/A';

  // Group samples by type to show summary
  const sampleTypes = Array.from(new Set(samples.map(s => s.sample_type)));

  return (
    <div className={styles.accordionItem}>
      <div className={styles.accordionHeader} onClick={() => setIsExpanded(!isExpanded)}>
        <div className={styles.accordionHeaderLeft}>
          <div className={styles.patientInfo}>
            <span className={styles.patientName}>{patientName}</span>
            <div className={styles.metaInfo}>
              <span>Order #{orderId}</span>
              <span>• Registered: {registeredAt}</span>
              <span>• {samples.length} Samples</span>
            </div>
          </div>
        </div>
        <div className={styles.accordionHeaderRight}>
          <button
            className={styles.collectActionButton}
            onClick={(e) => { e.stopPropagation(); onOpenModal(); }}
          >
            Mark Collected
          </button>
          <span className={styles.expandIcon}>{isExpanded ? '▼' : '▶'}</span>
        </div>
      </div>

      {isExpanded && (
        <div className={styles.accordionContent}>
          <div className={styles.sampleList}>
            <div className={styles.detailsGrid}>
              <div className={styles.detailColumn}>
                <h4>Required Tubes/Samples</h4>
                <ul className={styles.requirementsList}>
                  {sampleTypes.map(type => {
                    const count = samples.filter(s => s.sample_type === type).length;
                    return <li key={type}>{type} (x{count})</li>;
                  })}
                </ul>
              </div>
              <div className={styles.detailColumn}>
                {/* Place for Test List if available in `order_details` (not fully implemented in backend serializer yet but we can iterate samples) */}
                <h4>Tests Ordered</h4>
                {/* Since we don't have direct test names in basic sample serializer, we might need to rely on what's available or fetching more data. 
                     However, the previous code definition suggested `order_details` might be available if added to serializer or synthesized.
                     Assuming basic info for now. */}
                <div style={{ color: '#666', fontStyle: 'italic' }}>
                  Refer to Order #{orderId}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default function CollectionWorklistPage() {
  const queryClient = useQueryClient();
  const [modalData, setModalData] = useState<{ patientName: string, samples: CollectionWorklistItem[] } | null>(null);

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
      // invalidation happens after all promises resolve in handleConfirm
    },
  });

  const [searchTerm, setSearchTerm] = useState('');

  const samples = (worklistData?.results || []) as CollectionWorklistItem[];

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

  // Filter based on search/barcode
  const filteredPatients = useMemo(() => {
    if (!searchTerm) return groupedByPatient;
    const term = searchTerm.toLowerCase();
    const filtered: Record<string, CollectionWorklistItem[]> = {};

    Object.entries(groupedByPatient).forEach(([name, list]) => {
      const matchesName = name.toLowerCase().includes(term);
      const matchesOrder = list.some(s => s.order_id?.toLowerCase().includes(term) || String(s.order).includes(term));
      const matchesSampleId = list.some(s => String(s.id).includes(term));

      if (matchesName || matchesOrder || matchesSampleId) {
        filtered[name] = list;
      }
    });
    return filtered;
  }, [groupedByPatient, searchTerm]);




  const handleConfirmCollection = async (data: { ids: number[], source: string, barcodes: Record<string, string>, comments: string }) => {
    if (!modalData) return;

    const fullNotes = [
      data.comments ? `Comment: ${data.comments}` : '',
      `Source: ${data.source === 'home' ? 'Home Collection' : 'Lab Collection'}`
    ].filter(Boolean).join(' | ');

    try {
      const promises = data.ids.map(id => {
        const sample = modalData.samples.find(s => s.id === id);
        const barcode = sample ? data.barcodes[sample.sample_type] : undefined;

        return updateStatusMutation.mutateAsync({
          id,
          // Collected == Received requirement: "collected" action should set status that moves it to results. 
          // Previous backend edit allows RECEIVED to trigger ensured results.
          // Setting RECEIVED here to skip a separate receive step.
          status: 'RECEIVED',
          barcode,
          notes: fullNotes,
          additionalData: {
            collection_source: data.source,
            collected_at: new Date().toISOString(), // Even though backend sets it, we send implicit data
            received_at: new Date().toISOString()
          }
        });
      });

      await Promise.all(promises);

      // Close modal and refresh
      setModalData(null);
      queryClient.invalidateQueries({ queryKey: ['collection-worklist'] });
      queryClient.invalidateQueries({ queryKey: ['samples'] });
      queryClient.invalidateQueries({ queryKey: ['result-worklist'] });

    } catch (err) {
      console.error("Failed to update samples", err);
      alert("Failed to update some samples. Please try again.");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Sample Collection Worklist</h1>
        <p className={styles.subtitle}>Queue Management</p>
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
              <div className={styles.statValue}>{Object.keys(filteredPatients).length}</div>
              <div className={styles.statLabel}>Patients Check-in</div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statValue}>{samples.length}</div>
              <div className={styles.statLabel}>Total Samples</div>
            </div>
          </div>

          <div className={styles.searchBarContainer} style={{ marginBottom: '16px' }}>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="🔍 Scan Barcode or Search Patient..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '1.1em',
                borderRadius: '8px',
                border: '1px solid #ccc'
              }}
              autoFocus
            />
          </div>

          {samples.length === 0 ? (
            <div className={styles.emptyState}>
              <p>✓ No pending collections.</p>
            </div>
          ) : (
            <div className={styles.accordion}>
              {Object.entries(filteredPatients).map(([patientName, patientSamples]) => (
                <PatientCollectionRow
                  key={patientName}
                  patientName={patientName}
                  samples={patientSamples}
                  onOpenModal={() => setModalData({ patientName, samples: patientSamples })}
                />
              ))}
            </div>
          )}
        </>
      )}

      {modalData && (
        <CollectionModal
          patientName={modalData.patientName}
          samples={modalData.samples}
          onConfirm={handleConfirmCollection}
          onCancel={() => setModalData(null)}
        />
      )}
    </div>
  );
}
