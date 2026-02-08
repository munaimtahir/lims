import { useState, useEffect, useRef, type KeyboardEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { resultApi, orderApi } from '../../api/services/index';
import { useAuth } from '../../contexts';
import type { TestResult } from '../../types';
import styles from './ResultsPage.module.css';
import type { AxiosError } from 'axios';

// Types for the Worklist Item (inferred from backend response)
interface WorklistOrderItem {
  id: number;
  order: {
    id: number;
    order_id: string;
    patient: {
      id: number;
      full_name: string;
      age: number;
      gender: string;
      mrn: string;
    };
    priority: string;
    created_at?: string;
    lab_number?: string | null;
    status?: string;
  };
  test_name?: string;
  panel_name?: string;
  test_code?: string;
  panel_code?: string;
  status: string;
  patient_name?: string;
  patient_age?: number;
  patient_gender?: string;
}

const ResultWorklist = ({ onSelect }: { onSelect: (id: number) => void }) => {
  const { data: worklistData, isLoading } = useQuery({
    queryKey: ['result-worklist'],
    queryFn: () => resultApi.getWorklist(),
  });

  const [searchTerm, setSearchTerm] = useState('');

  // Handle potential pagination or list response
  const rawItems: WorklistOrderItem[] = Array.isArray(worklistData?.data.results)
    ? worklistData?.data.results
    : worklistData?.data.results || [];

  const items = rawItems.filter(item => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    const patientName = (item.order?.patient?.full_name || item.patient_name || '').toLowerCase();
    return (
      item.order?.order_id?.toLowerCase().includes(term) ||
      patientName.includes(term) ||
      item.order?.patient?.mrn?.toLowerCase().includes(term) ||
      (item.test_name || '').toLowerCase().includes(term) ||
      (item.panel_name || '').toLowerCase().includes(term)
    );
  });

  if (isLoading) return <div className={styles.message}>Loading worklist...</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <h1>Pending Results Worklist</h1>
        </div>
        <div className={styles.controls}>
          <input
            type="text"
            placeholder="Search by Order ID, Patient, or Test..."
            className={styles.resultInput}
            style={{ maxWidth: '400px' }}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className={styles.tableContainer}>
        {items.length === 0 ? (
          <div className={styles.message}>
            {searchTerm ? 'No matching orders found.' : 'No pending results found.'}
          </div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ width: '15%' }}>Lab / Visit ID</th>
                <th style={{ width: '26%' }}>Patient</th>
                <th style={{ width: '24%' }}>Test / Panel</th>
                <th style={{ width: '12%' }}>Created</th>
                <th style={{ width: '8%' }}>Status</th>
                <th style={{ width: '15%' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className={styles.resultRow}>
                  <td>
                    <span className={styles.orderId}>{item.order?.order_id || item.order?.lab_number || '—'}</span>
                  </td>
                  <td>
                    <div className={styles.patientInfo}>
                      {(() => {
                        const patientName = [item.order?.patient?.full_name, item.patient_name]
                          .map((value) => (value ?? '').trim())
                          .find(Boolean);
                        const age = item.order?.patient?.age ?? item.patient_age;
                        const gender = item.order?.patient?.gender || item.patient_gender;
                        const mrn = item.order?.patient?.mrn;
                        const agePart = age ? `${age}y${gender ? ' / ' : ''}` : '';
                        const genderPart = gender || '';
                        const mrnPart = mrn ? ` • ${mrn}` : '';
                        const subline = `${agePart}${genderPart}${mrnPart}`.trim();

                        return (
                          <>
                            <span className={styles.patientName} data-testid="results-patient-name">{patientName || '—'}</span>
                            <span className={styles.patientSub}>{subline || '—'}</span>
                          </>
                        );
                      })()}
                    </div>
                  </td>
                  <td>
                    <span className={styles.paramName}>
                      {item.test_name || item.panel_name || 'Unknown Test'}
                    </span>
                    {item.panel_name && item.test_name && (
                      <span className={styles.paramUnit}>part of {item.panel_name}</span>
                    )}
                  </td>
                  <td>
                    <span className={styles.patientSub}>
                      {item.order?.created_at ? new Date(item.order.created_at).toLocaleString() : '—'}
                    </span>
                  </td>
                  <td>
                    <span className={`${styles.statusBadge} ${styles['status-' + (item.status?.toLowerCase() || 'pending')]}`}>
                      {item.status}
                    </span>
                  </td>
                  <td>
                    <button
                      type="button"
                      className={styles.verifyMainButton}
                      style={{ fontSize: '13px', padding: '8px 16px' }}
                      onClick={() => onSelect(item.id)}
                    >
                      Enter Results
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
};

const useResultEntry = (orderItemId: number) => {
  const queryClient = useQueryClient();
  const [results, setResults] = useState<Record<number, string>>({});
  const [remarks, setRemarks] = useState<Record<number, string>>({});
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const toastTimeoutRef = useRef<number | null>(null);

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    if (toastTimeoutRef.current) {
      window.clearTimeout(toastTimeoutRef.current);
    }
    toastTimeoutRef.current = window.setTimeout(() => setToast(null), 4000);
  };

  const { data: existingResultsData, isLoading: isLoadingResults, isError, error } = useQuery({
    queryKey: ['results', orderItemId],
    queryFn: () => resultApi.getByOrderItem(orderItemId),
    enabled: !!orderItemId,
  });

  const initializedRef = useRef(false);
  // Reset initialization if orderItemId changes (though key prop should handle this, safety first)
  useEffect(() => {
    initializedRef.current = false;
  }, [orderItemId]);

  useEffect(() => {
    if (existingResultsData?.data.results && !initializedRef.current) {
      const initialResults: Record<number, string> = {};
      const initialRemarks: Record<number, string> = {};
      existingResultsData.data.results.forEach((r: TestResult) => {
        const value = r.result_value === '*' ? '' : (r.result_value || '');
        initialResults[r.test_parameter] = value;
        initialRemarks[r.test_parameter] = r.remarks || '';
      });
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setResults(initialResults);
      setRemarks(initialRemarks);
      initializedRef.current = true;
    }
  }, [existingResultsData]);

  const saveMutation = useMutation({
    mutationFn: async (resultsToSave: TestResult[]) => {
      const payload = resultsToSave.map(r => {
        const rawValue = (results[r.test_parameter] ?? '').toString();
        const trimmedValue = rawValue.trim();
        const resultValue = trimmedValue === '' ? '*' : trimmedValue;
        return {
          order_item: orderItemId,
          test_parameter: r.test_parameter,
          result_value: resultValue,
          remarks: remarks[r.test_parameter] ?? '',
        };
      });
      return resultApi.bulkEntry(payload);
    },
    onSuccess: () => {
      showToast('success', 'Results saved.');
      queryClient.invalidateQueries({ queryKey: ['results', orderItemId] });
      queryClient.invalidateQueries({ queryKey: ['result-worklist'] });
    },
    onError: (error: AxiosError<{ error?: string; error_details?: Array<{ error?: string }> }>) => {
      const errorDetails = error.response?.data?.error_details || [];
      const detailMessage = errorDetails
        .map((detail) => detail?.error)
        .filter(Boolean)
        .join(' • ');
      const backendMessage =
        detailMessage ||
        error.response?.data?.error ||
        error.message ||
        'Unable to save results.';
      showToast('error', backendMessage);
    },
  });

  const verifyMutation = useMutation({
    mutationFn: async (resultIds: number[]) => {
      return resultApi.bulkVerify(resultIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['results', orderItemId] });
      queryClient.invalidateQueries({ queryKey: ['result-worklist'] });
    },
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { error?: string; details?: string[] } } };
      const errorData = error.response?.data;
      const detailMessage = errorData?.details?.length ? errorData.details.join(' • ') : '';
      const backendMessage = detailMessage || errorData?.error || 'An unexpected error occurred during verification.';
      showToast('error', backendMessage);
    },
  });

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>, result: TestResult, index: number, total: number) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (e.ctrlKey) {
        // Save all results
        saveMutation.mutate(existingResultsData?.data.results || []);
        return;
      }
      if (e.shiftKey) {
        // Save current row
        saveMutation.mutate([result]);
        return;
      }

      const nextInput = document.querySelector(`input[data-index="${index + 1}"]`) as HTMLInputElement;
      if (nextInput) {
        nextInput.focus();
      } else if (index === total - 1) {
        (e.target as HTMLInputElement).blur();
      }
    }
  };

  return {
    results,
    setResults,
    remarks,
    setRemarks,
    existingResultsData,
    isLoadingResults,
    isError,
    error,
    saveMutation,
    verifyMutation,
    handleKeyDown,
    toast,
    showToast,
  };
};

const ResultEntry = ({ orderItemId, onBack }: { orderItemId: number; onBack: () => void }) => {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const {
    results,
    setResults,
    remarks,
    setRemarks,
    existingResultsData,
    isLoadingResults,
    isError,
    error,
    saveMutation,
    verifyMutation,
    handleKeyDown,
    toast,
    showToast,
  } = useResultEntry(orderItemId);

  const [loadingTimeout, setLoadingTimeout] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const canVerify = user?.role === 'Admin' || user?.role === 'Pathologist';

  const { data: orderItemDetails, isLoading: isLoadingDetails, isError: isDetailsError, error: detailsError, refetch: refetchDetails } = useQuery({
    queryKey: ['order-item-details', orderItemId],
    queryFn: () => orderApi.getOrderItem(orderItemId),
    enabled: !!orderItemId,
    retry: 2,
    retryDelay: 1000,
  });

  // Timeout detection for stuck loading
  useEffect(() => {
    if (isLoadingResults || isLoadingDetails) {
      const timer = setTimeout(() => {
        setLoadingTimeout(true);
      }, 15000); // 15 second timeout
      return () => clearTimeout(timer);
    }
  }, [isLoadingResults, isLoadingDetails]);

  const handleRetry = () => {
    setLoadingTimeout(false);
    setRetryCount(prev => prev + 1);
    queryClient.invalidateQueries({ queryKey: ['order-item-details', orderItemId] });
    queryClient.invalidateQueries({ queryKey: ['results', orderItemId] });
    refetchDetails();
  };

  const handleSaveAndVerify = async () => {
    if (!canVerify) {
      showToast('error', 'You do not have permission to verify results.');
      return;
    }
    if (!existingResultsData?.data.results?.length) {
      showToast('error', 'No results found to verify.');
      return;
    }
    try {
      const resultItems = existingResultsData?.data.results || [];
      await saveMutation.mutateAsync(resultItems);

      if (!confirm('This will lock all results and prevent edits. Continue?')) {
        return;
      }
      // Fetch latest results to avoid stale IDs/status before verification
      const refreshed = await queryClient.fetchQuery({
        queryKey: ['results', orderItemId],
        queryFn: () => resultApi.getByOrderItem(orderItemId),
      });
      const latestResults: TestResult[] = refreshed?.data?.results || [];
      const resultIds = latestResults.map((r: TestResult) => r.id).filter(Boolean) as number[];
      if (!resultIds.length) {
        showToast('error', 'No results found to verify.');
        return;
      }
      await verifyMutation.mutateAsync(resultIds);
      showToast('success', 'Results saved and verified.');
    } catch (err) {
      console.error('Save and verify failed:', err);
    }
  };

  const isLoading = isLoadingResults || isLoadingDetails;

  // Loading timeout state
  if (loadingTimeout && isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.errorContainer}>
          <div className={styles.errorIcon}>⚠️</div>
          <h2>Loading Timeout</h2>
          <p>The request is taking longer than expected. This might be due to network issues or server load.</p>
          <div className={styles.errorActions}>
            <button className={styles.retryButton} onClick={handleRetry}>
              Retry Loading
            </button>
            <button className={styles.backButton} onClick={onBack}>
              Back to Worklist
            </button>
          </div>
          {retryCount > 0 && <p className={styles.retryInfo}>Retry attempt: {retryCount}</p>}
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Loading results data...</p>
          <p className={styles.loadingHint}>This should only take a few seconds</p>
        </div>
      </div>
    );
  }

  // Error states with retry
  if (isError || isDetailsError) {
    const errorMessage = (error as Error)?.message || (detailsError as Error)?.message || 'Unknown error occurred';
    return (
      <div className={styles.container}>
        <div className={styles.errorContainer}>
          <div className={styles.errorIcon}>❌</div>
          <h2>Failed to Load Results</h2>
          <p className={styles.errorMessage}>{errorMessage}</p>
          <div className={styles.errorActions}>
            <button className={styles.retryButton} onClick={handleRetry}>
              Retry
            </button>
            <button className={styles.backButton} onClick={onBack}>
              Back to Worklist
            </button>
          </div>
        </div>
      </div>
    );
  }

  const resultItems = existingResultsData?.data.results || [];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const orderDetails = orderItemDetails?.data as any;
  const orderInfo = orderDetails?.order;
  const patientInfo = orderInfo?.patient;
  const testInfo = orderDetails?.test_name || orderDetails?.panel_name;
  const allVerified = resultItems.every((r: TestResult) => r.status === 'verified');
  const rejectedResults = resultItems.filter((r: TestResult) => r.status?.toLowerCase() === 'rejected');
  const verifyDisabled = !canVerify || saveMutation.isPending || verifyMutation.isPending;
  const saveAndVerifyLabel = saveMutation.isPending
    ? 'Saving...'
    : verifyMutation.isPending
      ? 'Verifying...'
      : '✓ Save & Verify All';
  const verifyDisabledReason = !canVerify ? 'Only Admin or Pathologist can verify results.' : undefined;


  return (
    <div className={styles.container}>
      {toast && (
        <div className={`${styles.toast} ${toast.type === 'success' ? styles.toastSuccess : styles.toastError}`}>
          {toast.message}
        </div>
      )}
      <button className={styles.backButton} onClick={onBack}>
        &larr; Back to Worklist
      </button>

      <div className={styles.header}>
        <div className={styles.headerTop}>
          <h1>Result Entry</h1>
          <span className={styles.orderId}>#{orderInfo?.order_id || 'ID Loading...'}</span>
        </div>

        <div className={styles.subtitle}>
          Test: <strong>{testInfo || 'Loading...'}</strong>
        </div>

        {patientInfo && (
          <div className={styles.patientBanner}>
            <div className={styles.patientField}>
              <span className={styles.fieldLabel}>Patient Name</span>
              <span className={styles.fieldValue}>{patientInfo.full_name}</span>
            </div>
            <div className={styles.patientField}>
              <span className={styles.fieldLabel}>MRN</span>
              <span className={styles.fieldValue}>{patientInfo.mrn}</span>
            </div>
            <div className={styles.patientField}>
              <span className={styles.fieldLabel}>Age / Gender</span>
              <span className={styles.fieldValue}>{patientInfo.age}y / {patientInfo.gender}</span>
            </div>
          </div>
        )}
      </div>

      {resultItems.length === 0 ? (
        <div className={styles.message}>Initializing result form...</div>
      ) : (
        <div className={styles.form}>
          {/* Sticky Action Bar at Top */}
          <div className={styles.stickyActionBar}>
            {!allVerified && (
              <>
                <button
                  type="button"
                  className={styles.saveButton}
                  onClick={() => saveMutation.mutate(resultItems)}
                  disabled={saveMutation.isPending || verifyMutation.isPending}
                >
                  {saveMutation.isPending ? 'Saving...' : '💾 Save Draft'}
                </button>
                <button
                  type="button"
                  className={`${styles.verifyMainButton} ${styles.saveButton}`}
                  onClick={handleSaveAndVerify}
                  disabled={verifyDisabled}
                  title={verifyDisabledReason}
                >
                  {saveAndVerifyLabel}
                </button>
              </>
            )}
            {allVerified && (
              <div className={styles.allVerifiedMessage}>
                ✓ All results have been verified.
              </div>
            )}
          </div>

          <div className={styles.tableContainer}>
            <table className={styles.resultTable}>
              <thead>
                <tr>
                  <th style={{ width: '35%' }}>Test Parameter</th>
                  <th style={{ width: '25%' }}>Result Value</th>
                  <th style={{ width: '15%' }}>Unit</th>
                  <th style={{ width: '25%' }}>Reference / Status</th>
                </tr>
              </thead>
              <tbody>
                {resultItems.map((result: TestResult, index: number) => {
                  const isVerified = result.status?.toLowerCase() === 'verified' || result.status?.toLowerCase() === 'published';

                  return (
                    <tr key={result.test_parameter} className={`${styles.resultRow} ${isVerified ? styles.verifiedRow : ''}`}>
                      <td>
                        <span className={styles.paramName}>
                          {result.parameter_name || `Param ${result.test_parameter}`}
                        </span>
                      </td>
                      <td>
                        {isVerified ? (
                          <div className={styles.verifiedField}>
                            <span className={styles.verifiedText}>{result.result_value}</span>
                          </div>
                        ) : (
                          <div className={styles.inputWrapper}>
                            <input
                              type="text"
                              data-index={index}
                              value={results[result.test_parameter] || ''}
                              onChange={(e) => setResults(prev => ({ ...prev, [result.test_parameter]: e.target.value }))}
                              onKeyDown={(e) => handleKeyDown(e, result, index, resultItems.length)}
                              className={styles.resultInput}
                              placeholder="Enter value"
                              autoFocus={index === 0}
                              required
                              disabled={isVerified}
                            />
                          </div>
                        )}
                      </td>
                      <td>
                        <span className={styles.paramUnit}>{result.unit || '-'}</span>
                      </td>
                      <td>
                        <div className={styles.refRange}>
                          <span className={styles.refValue}>
                            {result.reference_range || '—'}
                          </span>
                          <span className={`${styles.statusBadge} ${styles['status-' + (result.status?.toLowerCase() || 'pending')]}`}>
                            {result.status || 'Pending'}
                          </span>
                          {result.flag && <span className={`${styles.flag} ${styles['flag' + result.flag]}`}>{result.flag}</span>}
                        </div>
                        {isVerified && result.verified_by_name && (
                          <div className={styles.verifiedBy}>
                            Verified by {result.verified_by_name} at {new Date(result.verified_at!).toLocaleString()}
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Footer buttons for convenience */}
          <div className={styles.footer}>
            {!allVerified && (
              <>
                <button
                  type="button"
                  className={styles.saveButton}
                  onClick={() => saveMutation.mutate(resultItems)}
                  disabled={saveMutation.isPending || verifyMutation.isPending}
                >
                  {saveMutation.isPending ? 'Saving...' : 'Save Draft'}
                </button>
                <button
                  type="button"
                  className={`${styles.verifyMainButton} ${styles.saveButton}`}
                  onClick={handleSaveAndVerify}
                  disabled={verifyDisabled}
                  title={verifyDisabledReason}
                >
                  {saveAndVerifyLabel}
                </button>
              </>
            )}
            {allVerified && (
              <div className={styles.allVerifiedMessage}>
                All results have been verified.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default function ResultsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const orderItemIdStr = searchParams.get('orderItemId') || searchParams.get('orderItem');
  const orderItemId = orderItemIdStr ? Number(orderItemIdStr) : null;

  return (
    <div>
      {orderItemId ? (
        <ResultEntry
          key={orderItemId}
          orderItemId={orderItemId}
          onBack={() => setSearchParams((prev) => {
            const newParams = new URLSearchParams(prev);
            newParams.delete('orderItemId');
            newParams.delete('orderItem');
            return newParams;
          })}
        />
      ) : (
        <ResultWorklist
          onSelect={(id) => setSearchParams({ orderItemId: id.toString() })}
        />
      )}
    </div>
  );
}
