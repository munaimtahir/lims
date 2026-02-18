
import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resultApi, reportApi, orderApi } from '../../api/services';
import type { TestResult, VerificationQueueOrder, VerificationDetails } from '../../types';
import styles from './VerificationQueuePage.module.css';

export default function VerificationQueuePage() {
  const queryClient = useQueryClient();
  const [selectedOrderInternalId, setSelectedOrderInternalId] = useState<number | null>(null);
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Fetch Queue
  const { data: queueResponse, isLoading: queueLoading, error: queueError } = useQuery({
    queryKey: ['verification-queue'],
    queryFn: () => resultApi.getVerificationQueue(),
  });

  const queue = useMemo(() => {
    // Check if response is { queue: [...] } (new) or something else
    // Typescript might complain if types aren't perfect yet, so we safeguard
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const data = queueResponse as any;
    return (data?.queue || []) as VerificationQueueOrder[];
  }, [queueResponse]);

  // Fetch Details for Selected Order
  const { data: detailData, isLoading: detailLoading, error: detailError } = useQuery({
    queryKey: ['verification-details', selectedOrderInternalId],
    queryFn: () => orderApi.getVerificationDetails(selectedOrderInternalId!),
    enabled: !!selectedOrderInternalId,
  });

  const detailResults = useMemo(() => {
    if (!detailData) return [];
    const order = detailData as VerificationDetails;
    // Flatten results from items
    return order.items.flatMap(item =>
      item.results.map(r => ({
        ...r,
        order_item: item, // Attach parent item for context
        // Ensure status mapping if needed? Backend serializer already maps.
      }))
    );
  }, [detailData]);

  // Derived State for Navigation
  const currentIndex = queue.findIndex(o => o.order_internal_id === selectedOrderInternalId);
  const currentOrder = currentIndex !== -1 ? queue[currentIndex] : null;
  const prevOrder = currentIndex > 0 ? queue[currentIndex - 1] : null;
  const nextOrder = currentIndex >= 0 && currentIndex < queue.length - 1 ? queue[currentIndex + 1] : null;

  // Mutations
  const verifyMutation = useMutation({
    mutationFn: (resultId: number) => resultApi.verify(resultId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verification-details'] });
      queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
    },
    onError: (err: any) => {
      const data = err?.response?.data;
      if (data?.blocking_reasons) {
        const reasons = data.blocking_reasons.map((r: any) => r.detail).join(' • ');
        setNotice({ type: 'error', message: reasons });
      } else {
        setNotice({ type: 'error', message: data?.message || data?.detail || 'Failed to verify result.' });
      }
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ resultId, reason }: { resultId: number; reason: string }) =>
      resultApi.reject(resultId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verification-details'] });
      queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
    },
    onError: (err: any) => {
      const data = err?.response?.data;
      setNotice({ type: 'error', message: data?.message || data?.detail || 'Failed to return result.' });
    },
  });

  const bulkVerifyMutation = useMutation({
    mutationFn: (resultIds: number[]) => resultApi.bulkVerify(resultIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verification-details'] });
      queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
      setNotice({ type: 'success', message: 'Selected results verified successfully.' });

      // Auto-advance if full order verified? 
      // If no results left unverified, maybe move to next?
      // For now, user controls navigation.
    },
    onError: (err: any) => {
      const data = err?.response?.data;
      if (data?.blocking_reasons) {
        const reasons = data.blocking_reasons.map((r: any) => r.detail).join(' • ');
        setNotice({ type: 'error', message: reasons });
      } else {
        setNotice({ type: 'error', message: data?.message || data?.detail || 'Failed to verify results.' });
      }
    },
  });

  const bulkRejectMutation = useMutation({
    mutationFn: ({ resultIds, reason }: { resultIds: number[]; reason: string }) =>
      resultApi.bulkReject(resultIds, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verification-details'] });
      queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
      setNotice({ type: 'success', message: 'Selected results returned to entry.' });
    },
    onError: (err: any) => {
      setNotice({ type: 'error', message: err?.response?.data?.detail || 'Failed to return results.' });
    },
  });


  // Handlers
  const handleVerify = async (result: TestResult) => {
    // Check missing values
    if ((!result.result_value || result.result_value.trim() === '') && result.result_value !== '*') {
      // allow '*' if implemented, but generally empty string is the issue.
      // Wait, backend logic for "required" is handled. Frontend can also check.
      // Let's rely on backend error for required fields, but warn user if obvious.
    }
    await verifyMutation.mutateAsync(result.id);
  };

  const handleReject = async (resultId: number) => {
    const reason = prompt('Enter reason for returning to entry:');
    if (reason) {
      await rejectMutation.mutateAsync({ resultId, reason });
    }
  };

  const handleVerifyAll = async () => {
    // Only verify non-verified processing/draft ones
    const toVerify = detailResults.filter(r => ['DRAFT', 'ENTERED', 'processed', 'pending'].includes(r.status) || !r.status);
    // Note: status from API should be matched. Assuming 'ENTERED' or 'DRAFT'.

    // Filter out verified/rejected
    const actionable = toVerify.filter(r => r.status !== 'VERIFIED' && r.status !== 'FINAL' && r.status !== 'REJECTED');

    if (actionable.length === 0) {
      setNotice({ type: 'error', message: 'No pending results to verify.' });
      return;
    }

    if (!confirm(`Verify ${actionable.length} results for this order?`)) return;
    await bulkVerifyMutation.mutateAsync(actionable.map(r => r.id));
  };

  const handlePreviewReport = async () => {
    if (!selectedOrderInternalId) return;
    try {
      // Generate draft report for preview
      const report = await reportApi.generate(selectedOrderInternalId, { is_final: false });
      if (report.report_file) {
        window.open(report.report_file, '_blank');
      } else {
        setNotice({ type: 'error', message: 'Report generated but no file URL returned.' });
      }
    } catch (err: any) {
      setNotice({ type: 'error', message: err?.response?.data?.detail || 'Failed to generate report preview.' });
    }
  };

  const handleReturnAll = async () => {
    const reason = prompt('Enter reason for returning all results to entry:');
    if (!reason) return;

    // Can return VERIFIED ones too if needed? Usually we return PENDING ones or ALL.
    // Logic: Return ALL displayed results that are editable or verified?
    // "Return Order" usually implies un-verifying everything or rejecting current batch.
    // Let's return all currently visible results for this order.
    // Or just pending? The prompt implies "Returning results".
    const ids = detailResults.map(r => r.id);
    await bulkRejectMutation.mutateAsync({ resultIds: ids, reason });
  };

  const publishMutation = useMutation({
    mutationFn: (orderId: number) => orderApi.publishReport(orderId),
    onSuccess: (response) => {
      setNotice({ type: 'success', message: 'Report published successfully.' });
      if (response.data && (response.data as any).pdf_url) {
        window.open((response.data as any).pdf_url, '_blank');
      }
      queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
    },
    onError: (err: any) => {
      const data = err?.response?.data;
      if (data?.code === 'REPORT_BLOCKED') {
        const reasons = data.blocking_reasons.map((r: any) => r.detail).join(' • ');
        setNotice({ type: 'error', message: `Publish Blocked: ${reasons}` });
      } else {
        setNotice({ type: 'error', message: data?.detail || 'Failed to publish report.' });
      }
    },
  });

  const handlePublishReport = async () => {
    if (!selectedOrderInternalId) return;
    if (!confirm('This will finalize the report and mark it as PUBLISHED. Continue?')) return;
    await publishMutation.mutateAsync(selectedOrderInternalId);
  };


  if (queueLoading) return <div className={styles.loading}>Loading queue...</div>;
  if (queueError) return <div className={styles.error}>Failed to load verification queue</div>;

  // Detail View
  if (selectedOrderInternalId) {
    if (detailLoading) return <div className={styles.loading}>Loading order details...</div>;

    return (
      <div className={styles.container}>
        {notice && (
          <div className={`${styles.notice} ${notice.type === 'success' ? styles.noticeSuccess : styles.noticeError}`}>
            {notice.message}
            <button className={styles.closeNotice} onClick={() => setNotice(null)}>×</button>
          </div>
        )}

        <div className={styles.detailView}>
          <div className={styles.topNav}>
            <button className={styles.backButton} onClick={() => setSelectedOrderInternalId(null)}>
              &larr; Back to Queue
            </button>
            <div className={styles.navControls}>
              <button
                disabled={!prevOrder}
                onClick={() => prevOrder && setSelectedOrderInternalId(prevOrder.order_internal_id)}
              >
                &uarr; Previous Order
              </button>
              <div className={styles.counter}>
                {currentIndex + 1} of {queue.length}
              </div>
              <button
                disabled={!nextOrder}
                onClick={() => nextOrder && setSelectedOrderInternalId(nextOrder.order_internal_id)}
              >
                Next Order &darr;
              </button>
            </div>
          </div>

          <div className={styles.detailHeader}>
            <div>
              <h2>{detailData?.patient?.full_name || 'Patient'}</h2>
              <div className={styles.meta}>
                <span className={styles.orderId}>{detailData?.lab_number || detailData?.order_id}</span>
                <span className={styles.separator}>|</span>
                <span>{detailData?.patient?.mrn || 'No MRN'}</span>
                <span className={styles.separator}>|</span>
                <span className={styles.details}>{detailData?.patient?.age}y / {detailData?.patient?.gender}</span>
                <span className={styles.separator}>|</span>
                <span className={styles.details}>{detailData?.priority || 'Normal'}</span>
                <span className={styles.separator}>|</span>
                <span className={styles.statusBadge}>{detailData?.status}</span>
              </div>
            </div>
            <div className={styles.headerActions}>
              <button className={`${styles.btn} ${styles.previewBtn}`} onClick={handlePreviewReport}>
                Preview
              </button>
              <button
                className={`${styles.btn} ${styles.publishBtn}`}
                onClick={handlePublishReport}
                disabled={publishMutation.isPending}
              >
                {publishMutation.isPending ? 'Publishing...' : 'Publish Report'}
              </button>
              <button className={`${styles.btn} ${styles.verifyAllBtn}`} onClick={handleVerifyAll}>
                Verify All
              </button>
              <button className={`${styles.btn} ${styles.returnAllBtn}`} onClick={handleReturnAll}>
                Return Order
              </button>
            </div>
          </div>

          <div className={styles.resultsList}>
            <table className={styles.verifyTable}>
              <thead>
                <tr>
                  <th>Test / Parameter</th>
                  <th>Result</th>
                  <th>Unit</th>
                  <th>Ref Range</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {detailResults.map(result => (
                  <tr key={result.id} className={result.status === 'VERIFIED' ? styles.verifiedRow : ''}>
                    <td>
                      <div className={styles.paramName}>
                        {result.parameter_name === 'Result' ? ((result.order_item as any)?.test_name || result.parameter_name) : result.parameter_name}
                      </div>
                      {result.parameter_name !== 'Result' && (
                        <div className={styles.testName}>{(result.order_item as any)?.test_name || ''}</div>
                      )}
                    </td>
                    <td>
                      <span className={`${styles.resultValue} ${result.flag ? styles[result.flag.toLowerCase()] : ''}`}>
                        {result.result_value}
                        {result.flag && <span className={styles.flagSymbol}>({result.flag})</span>}
                      </span>
                    </td>
                    <td>{result.unit}</td>
                    <td>{result.reference_range}</td>
                    <td>
                      <span className={`${styles.statusBadge} ${styles[result.status?.toLowerCase()]}`}>
                        {result.status}
                      </span>
                    </td>
                    <td>
                      <div className={styles.actions}>
                        {result.status !== 'VERIFIED' && result.status !== 'FINAL' && (
                          <button
                            className={styles.verifyBtn}
                            onClick={() => handleVerify(result)}
                            disabled={verifyMutation.isPending}
                          >
                            Verify
                          </button>
                        )}
                        {/* Allow unverify if verified */}
                        {(result.status === 'VERIFIED') && (
                          <button
                            className={styles.rejectBtn}
                            onClick={() => handleReject(result.id)}
                            disabled={rejectMutation.isPending}
                          >
                            Unverify
                          </button>
                        )}
                        {(result.status !== 'VERIFIED') && (
                          <button
                            className={styles.rejectBtn}
                            onClick={() => handleReject(result.id)}
                            disabled={rejectMutation.isPending}
                          >
                            Return
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {detailResults.length === 0 && (
                  <tr><td colSpan={6} style={{ textAlign: 'center', padding: '20px' }}>No results found for this order.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // List View
  return (
    <div className={styles.container}>
      {notice && (
        <div className={`${styles.notice} ${notice.type === 'success' ? styles.noticeSuccess : styles.noticeError}`}>
          {notice.message}
          <button className={styles.closeNotice} onClick={() => setNotice(null)}>×</button>
        </div>
      )}

      <div className={styles.header}>
        <h1>Verification Queue</h1>
        <p className={styles.subtitle}>{queue.length} orders pending verification</p>
      </div>

      <div className={styles.queueList}>
        {queue.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>✓</div>
            <h3>All Caught Up!</h3>
            <p>No results pending verification.</p>
          </div>
        ) : (
          <table className={styles.queueTable}>
            <thead>
              <tr>
                <th>Lab No</th>
                <th>Patient</th>
                <th>Details</th>
                <th>Tests</th>
                <th className={styles.center}>Pending</th>
                <th className={styles.right}>Action</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((order) => (
                <tr key={order.order_internal_id} onClick={() => setSelectedOrderInternalId(order.order_internal_id)} className={styles.clickableRow}>
                  <td className={styles.bold}>{order.lab_number || order.order_id}</td>
                  <td>
                    <div className={styles.patientName}>{order.patient_name}</div>
                    <div className={styles.mrn}>{order.mrn}</div>
                  </td>
                  <td className={styles.dimmed}>{order.details}</td>
                  <td>
                    <div className={styles.testList}>{order.tests}</div>
                  </td>
                  <td className={styles.center}>
                    <span className={styles.badge}>{order.pending_count}</span>
                  </td>
                  <td className={styles.right}>
                    <button
                      className={styles.reviewBtn}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedOrderInternalId(order.order_internal_id);
                      }}
                    >
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
