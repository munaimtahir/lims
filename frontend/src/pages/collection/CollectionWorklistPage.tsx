import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sampleApi, orderApi } from '../../api/services';
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

export default function CollectionWorklistPage() {
  const queryClient = useQueryClient();
  const [selectedItem, setSelectedItem] = useState<CollectionWorklistItem | null>(null);
  const [isCollectModalOpen, setIsCollectModalOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());
  const barcodeEnabled = isSampleBarcodeEnabled();

  const { data: worklistData, isLoading, error } = useQuery({
    queryKey: ['collection-worklist'],
    queryFn: () => sampleApi.getCollectionWorklist(),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status, barcode, sampleData }: {
      id: number;
      status: string;
      barcode?: string;
      sampleData?: { source: string; checklist: Record<string, boolean> };
    }) => sampleApi.updateStatus(id, status, barcode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection-worklist'] });
      queryClient.invalidateQueries({ queryKey: ['samples'] });
      queryClient.invalidateQueries({ queryKey: ['result-worklist'] });
      setIsCollectModalOpen(false);
      setSelectedItem(null);
    },
  });

  const toggleExpand = (id: number) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const samples = worklistData?.results || [];

  // Group samples by order for better display
  const groupedByOrder = samples.reduce((acc: Record<string, CollectionWorklistItem[]>, sample: CollectionWorklistItem) => {
    const orderId = sample.order_id;
    if (!acc[orderId]) {
      acc[orderId] = [];
    }
    acc[orderId].push(sample);
    return acc;
  }, {});

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Sample Collection Worklist</h1>
        <p className={styles.subtitle}>Pending sample collections for Phlebotomy</p>
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
              <div className={styles.statValue}>{Object.keys(groupedByOrder).length}</div>
              <div className={styles.statLabel}>Patients in Queue</div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statValue}>{samples.length}</div>
              <div className={styles.statLabel}>Total Samples</div>
            </div>
          </div>

          {samples.length === 0 ? (
            <div className={styles.emptyState}>
              <p>✓ No pending collections. Great job!</p>
            </div>
          ) : (
            <div className={styles.accordion}>
              {Object.entries(groupedByOrder).map(([orderId, orderSamples], queueIndex) => {
                const firstSample = orderSamples[0];
                const isExpanded = expandedItems.has(firstSample.id);

                // Extract unique sample types
                const sampleTypes = [...new Set(orderSamples.map(s => s.sample_type))];

                return (
                  <div key={orderId} className={styles.accordionItem}>
                    <div
                      className={styles.accordionHeader}
                      onClick={() => toggleExpand(firstSample.id)}
                    >
                      <div className={styles.accordionHeaderLeft}>
                        <span className={styles.queueNumber}>#{queueIndex + 1}</span>
                        <div className={styles.patientInfo}>
                          <span className={styles.patientName}>{firstSample.patient_name}</span>
                          <span className={styles.orderId}>{orderId}</span>
                        </div>
                      </div>
                      <div className={styles.accordionHeaderRight}>
                        <span className={styles.sampleCount}>{orderSamples.length} sample(s)</span>
                        <span className={styles.expandIcon}>{isExpanded ? '▼' : '▶'}</span>
                      </div>
                    </div>

                    {isExpanded && (
                      <div className={styles.accordionContent}>
                        <div className={styles.sampleList}>
                          <h4>Required Samples:</h4>
                          <ul>
                            {sampleTypes.map((type, idx) => (
                              <li key={idx}>
                                <span className={styles.sampleType}>{type}</span>
                                <span className={styles.sampleCount}>
                                  ({orderSamples.filter(s => s.sample_type === type).length} tube(s))
                                </span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div className={styles.actionButtons}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedItem(firstSample);
                              setIsCollectModalOpen(true);
                            }}
                            className={styles.collectButton}
                          >
                            Mark Collected
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {isCollectModalOpen && selectedItem && (
        <CollectSampleModal
          sample={selectedItem}
          allSamplesForOrder={groupedByOrder[selectedItem.order_id] || [selectedItem]}
          onClose={() => setIsCollectModalOpen(false)}
          onConfirm={(data) => {
            // Mark all samples for this order as collected
            const samplesToCollect = groupedByOrder[selectedItem.order_id] || [selectedItem];
            samplesToCollect.forEach(sample => {
              updateStatusMutation.mutate({
                id: sample.id,
                status: 'COLLECTED',
                barcode: data.barcodes[sample.sample_type] || undefined,
                sampleData: { source: data.source, checklist: data.checklist },
              });
            });
          }}
          isSubmitting={updateStatusMutation.isPending}
          barcodeEnabled={barcodeEnabled}
        />
      )}
    </div>
  );
}

interface CollectSampleModalProps {
  sample: CollectionWorklistItem;
  allSamplesForOrder: CollectionWorklistItem[];
  onClose: () => void;
  onConfirm: (data: {
    barcodes: Record<string, string>;
    source: string;
    checklist: Record<string, boolean>
  }) => void;
  isSubmitting: boolean;
  barcodeEnabled: boolean;
}

function CollectSampleModal({
  sample,
  allSamplesForOrder,
  onClose,
  onConfirm,
  isSubmitting,
  barcodeEnabled
}: CollectSampleModalProps) {
  const [barcodes, setBarcodes] = useState<Record<string, string>>({});
  const [source, setSource] = useState<'lab' | 'home'>('lab');
  const [checklist, setChecklist] = useState<Record<string, boolean>>({});

  // Get unique sample types
  const sampleTypes = [...new Set(allSamplesForOrder.map(s => s.sample_type))];

  // Initialize checklist - all checked by default
  useState(() => {
    const initialChecklist: Record<string, boolean> = {};
    sampleTypes.forEach(type => {
      initialChecklist[type] = true;
    });
    setChecklist(initialChecklist);
  });

  const handleAutoGenerate = (sampleType: string) => {
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const random = Math.floor(Math.random() * 10000);
    setBarcodes(prev => ({
      ...prev,
      [sampleType]: `SAM-${today}-${random}-${sampleType.substring(0, 3).toUpperCase()}`
    }));
  };

  const handleConfirm = () => {
    onConfirm({ barcodes, source, checklist });
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h3>Mark Samples Collected</h3>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <div className={styles.modalBody}>
          <div className={styles.patientInfoBox}>
            <strong>{sample.patient_name}</strong>
            <span className={styles.orderIdBadge}>{sample.order_id}</span>
          </div>

          <div className={styles.sampleChecklist}>
            <h4>Sample Checklist:</h4>
            {sampleTypes.map(type => (
              <div key={type} className={styles.checklistItem}>
                <label>
                  <input
                    type="checkbox"
                    checked={checklist[type] || false}
                    onChange={(e) => setChecklist(prev => ({ ...prev, [type]: e.target.checked }))}
                  />
                  <span className={styles.sampleTypeName}>{type}</span>
                  <span className={styles.tubeCount}>
                    ({allSamplesForOrder.filter(s => s.sample_type === type).length} tube(s))
                  </span>
                </label>

                {barcodeEnabled && checklist[type] && (
                  <div className={styles.barcodeInput}>
                    <input
                      type="text"
                      value={barcodes[type] || ''}
                      onChange={(e) => setBarcodes(prev => ({ ...prev, [type]: e.target.value }))}
                      placeholder="Scan or enter barcode"
                    />
                    <button
                      type="button"
                      onClick={() => handleAutoGenerate(type)}
                      className={styles.generateBtn}
                    >
                      Generate
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className={styles.sourceSelector}>
            <h4>Sample Source:</h4>
            <div className={styles.radioGroup}>
              <label>
                <input
                  type="radio"
                  name="source"
                  value="lab"
                  checked={source === 'lab'}
                  onChange={() => setSource('lab')}
                />
                <span>Collected at Lab</span>
              </label>
              <label>
                <input
                  type="radio"
                  name="source"
                  value="home"
                  checked={source === 'home'}
                  onChange={() => setSource('home')}
                />
                <span>Brought from Home</span>
              </label>
            </div>
          </div>

          <div className={styles.modalActions}>
            <button onClick={onClose} className={styles.cancelButton}>Cancel</button>
            <button
              onClick={handleConfirm}
              disabled={isSubmitting || Object.values(checklist).every(v => !v)}
              className={styles.submitButton}
            >
              {isSubmitting ? 'Processing...' : 'Confirm Collection'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
