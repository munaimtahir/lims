import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { resultApi } from '../../api/services';
import type { OrderItem, WorklistOrderItem } from '../../types';
import styles from './ResultEntryWorklistPage.module.css';

export default function ResultEntryWorklistPage() {
  const navigate = useNavigate();
  const [selectedItem, setSelectedItem] = useState<OrderItem | null>(null);

  const { data: worklistData, isLoading, error } = useQuery({
    queryKey: ['result-entry-worklist'],
    queryFn: () => resultApi.getWorklist(),
  });

  const worklistItems = worklistData?.results || [];

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Result Entry Worklist</h1>
        <p className={styles.subtitle}>Order items requiring result entry</p>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading worklist...</div>
      ) : error ? (
        <div className={styles.error}>Failed to load worklist</div>
      ) : (
        <>
          <div className={styles.stats}>
            <div className={styles.statCard}>
              <div className={styles.statValue}>{worklistItems.length}</div>
              <div className={styles.statLabel}>Items Pending Entry</div>
            </div>
          </div>

          {worklistItems.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No items pending result entry</p>
            </div>
          ) : (
            <div className={styles.worklist}>
              {worklistItems.map((item: WorklistOrderItem) => (
                <div
                  key={item.id}
                  className={`${styles.worklistItem} ${selectedItem?.id === item.id ? styles.selected : ''}`}
                  onClick={() => setSelectedItem(item as any)}
                >
                  <div className={styles.itemHeader}>
                    <div>
                      <h3 className={styles.patientName}>{item.order?.patient?.full_name || item.patient_name}</h3>
                      <p className={styles.testName}>{item.test_name || item.panel_name}</p>
                    </div>
                    <span className={styles.statusBadge}>{item.status}</span>
                  </div>

                  <div className={styles.itemDetails}>
                    <div className={styles.detail}>
                      <span className={styles.label}>Lab No:</span>
                      <span className={styles.value}>{item.order?.lab_number || item.order?.order_id || `ORD-${item.id}`}</span>
                    </div>
                    <div className={styles.detail}>
                      <span className={styles.label}>MRN:</span>
                      <span className={styles.value}>{item.order?.patient?.mrn || 'N/A'}</span>
                    </div>
                  </div>

                  <div className={styles.itemActions}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/dashboard/results?orderId=${item.order.id}&orderItemId=${item.id}`);
                      }}
                      className={styles.enterButton}
                    >
                      Enter Results
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
