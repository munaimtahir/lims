import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resultApi } from '../../api/services';
import type { TestResult } from '../../types';
import styles from './VerificationQueuePage.module.css';

export default function VerificationQueuePage() {
  const queryClient = useQueryClient();
  const [selectedOrderItemId, setSelectedOrderItemId] = useState<number | null>(null);

  const { data: queueData, isLoading, error } = useQuery({
    queryKey: ['verification-queue'],
    queryFn: () => resultApi.getVerificationQueue(),
  });

  const verifyMutation = useMutation({
    mutationFn: (resultId: number) => resultApi.verify(resultId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ resultId, reason }: { resultId: number; reason: string }) =>
      resultApi.reject(resultId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
    },
  });

  const results = queueData?.results || [];

  // Group results by order_item
  const groupedResults = useMemo(() => {
    const groups: Record<number, {
      order_item_id: number,
      patient_name: string,
      order_id: string,
      test_name: string,
      results: TestResult[]
    }> = {};

    results.forEach((r) => {
      const orderItemId = typeof r.order_item === 'object' ? r.order_item.id : r.order_item;
      if (!groups[orderItemId]) {
        groups[orderItemId] = {
          order_item_id: orderItemId,
          patient_name: r.order_item.order?.patient?.full_name || 'Unknown',
          order_id: r.order_item.order?.order_id || 'Unknown',
          test_name: r.order_item.test_name || r.order_item.panel_name || 'Test',
          results: [],
        };
      }
      groups[orderItemId].results.push(r);
    });

    return Object.values(groups);
  }, [results]);

  const handleVerify = async (resultId: number) => {
    await verifyMutation.mutateAsync(resultId);
  };

  const handleRepeat = async (resultId: number) => {
    const reason = prompt('Enter reason for repeating results:');
    if (reason) {
      await rejectMutation.mutateAsync({ resultId, reason });
    }
  };

  const selectedGroup = groupedResults.find(g => g.order_item_id === selectedOrderItemId);

  if (isLoading) return <div className={styles.loading}>Loading queue...</div>;
  if (error) return <div className={styles.error}>Failed to load verification queue</div>;

  return (
    <div className={styles.container}>
      {selectedOrderItemId ? (
        <div className={styles.detailView}>
          <button className={styles.backButton} onClick={() => setSelectedOrderItemId(null)}>
            &larr; Back to Queue
          </button>

          <div className={styles.detailHeader}>
            <h2>Review Results: {selectedGroup?.patient_name}</h2>
            <p>{selectedGroup?.test_name} (#{selectedGroup?.order_id})</p>
          </div>

          <table className={styles.verifyTable}>
            <thead>
              <tr>
                <th>Parameter Name</th>
                <th>Result</th>
                <th>Units</th>
                <th>Normal Range</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {selectedGroup?.results.map((r) => (
                <tr key={r.id}>
                  <td>{r.parameter_name}</td>
                  <td className={styles.resultValueCell}>
                    <span className={`${styles.resultValue} ${styles[r.flag?.toLowerCase()]}`}>
                      {r.result_value}
                      {r.flag && <span className={styles.flagSymbol}>({r.flag})</span>}
                    </span>
                  </td>
                  <td>{r.unit}</td>
                  <td className={styles.rangeCell}>{r.reference_range || '-'}</td>
                  <td>
                    <div className={styles.btnGroup}>
                      <button
                        className={styles.verifyBtn}
                        onClick={() => handleVerify(r.id)}
                        disabled={verifyMutation.isPending}
                      >
                        Verify
                      </button>
                      <button
                        className={styles.repeatBtn}
                        onClick={() => handleRepeat(r.id)}
                        disabled={rejectMutation.isPending}
                      >
                        Repeat
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <>
          <div className={styles.header}>
            <h1>Verification Queue</h1>
            <p className={styles.subtitle}>{groupedResults.length} orders pending verification</p>
          </div>

          <div className={styles.queueList}>
            {groupedResults.length === 0 ? (
              <div className={styles.emptyState}>No results pending verification.</div>
            ) : (
              <table className={styles.queueTable}>
                <thead>
                  <tr>
                    <th>Order ID</th>
                    <th>Patient</th>
                    <th>Test / Panel</th>
                    <th>Pending</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {groupedResults.map((group) => (
                    <tr key={group.order_item_id}>
                      <td className={styles.bold}>{group.order_id}</td>
                      <td>{group.patient_name}</td>
                      <td>{group.test_name}</td>
                      <td>{group.results.length} parameters</td>
                      <td>
                        <button
                          className={styles.reviewBtn}
                          onClick={() => setSelectedOrderItemId(group.order_item_id)}
                        >
                          Review Results
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}
