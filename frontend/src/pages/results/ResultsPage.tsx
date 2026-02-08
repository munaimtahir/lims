import { useState, useEffect, useRef, useMemo, type KeyboardEvent } from 'react';
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

  const [expandedPatientId, setExpandedPatientId] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Handle potential pagination or list response
  const rawItems: WorklistOrderItem[] = Array.isArray(worklistData?.data.results)
    ? worklistData?.data.results
    : worklistData?.data.results || [];

  const items = useMemo(() => rawItems.filter(item => {
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
  }), [rawItems, searchTerm]);

  // Group by Patient
  const groupedByPatient = useMemo(() => {
    const groups: Record<number, WorklistOrderItem[]> = {};
    items.forEach(item => {
      const pId = item.order?.patient?.id || 0;
      if (!groups[pId]) groups[pId] = [];
      groups[pId].push(item);
    });
    return groups;
  }, [items]);

  if (isLoading) return <div className={styles.message}>Loading worklist...</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <h1>Result Entry Worklist</h1>
        </div>
        <div className={styles.controls}>
          <input
            type="text"
            placeholder="Search by Patient, Order, or Test..."
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
          <div className={styles.accordion}>
            {Object.entries(groupedByPatient).map(([patientIdStr, patientItems]) => {
              const patientId = Number(patientIdStr);
              const firstItem = patientItems[0];
              const patient = firstItem.order?.patient;
              const isExpanded = expandedPatientId === patientId;

              return (
                <div key={patientId} className={styles.accordionItem} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', marginBottom: '12px', overflow: 'hidden' }}>
                  <div
                    onClick={() => setExpandedPatientId(isExpanded ? null : patientId)}
                    style={{
                      padding: '16px',
                      background: '#f8fafc',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                      <div style={{ fontWeight: 'bold', fontSize: '16px' }}>{patient?.full_name || firstItem.patient_name || 'Unknown Patient'}</div>
                      <div style={{ fontSize: '14px', color: '#64748b' }}>
                        {patient?.age}y / {patient?.gender} • MRN: {patient?.mrn}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ fontSize: '13px', color: '#64748b', fontWeight: 500 }}>
                        {patientItems.length} test{patientItems.length !== 1 ? 's' : ''} pending
                      </span>
                      <span>{isExpanded ? '▼' : '▶'}</span>
                    </div>
                  </div>

                  {isExpanded && (
                    <div style={{ padding: '0', background: 'white' }}>
                      <table className={styles.table} style={{ margin: 0 }}>
                        <thead style={{ background: '#f1f5f9' }}>
                          <tr>
                            <th style={{ width: '20%' }}>Order ID</th>
                            <th style={{ width: '40%' }}>Test / Panel</th>
                            <th style={{ width: '20%' }}>Status</th>
                            <th style={{ width: '20%' }}>Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {patientItems.map(item => (
                            <tr key={item.id} className={styles.resultRow}>
                              <td><span className={styles.orderId}>{item.order?.order_id}</span></td>
                              <td><span className={styles.paramName}>{item.test_name || item.panel_name}</span></td>
                              <td>
                                <span className={`${styles.statusBadge} ${styles['status-' + (item.status?.toLowerCase() || 'pending')]}`}>
                                  {item.status}
                                </span>
                              </td>
                              <td>
                                <button
                                  className={styles.verifyMainButton}
                                  style={{ fontSize: '12px', padding: '6px 12px' }}
                                  onClick={(e) => { e.stopPropagation(); onSelect(item.id); }}
                                >
                                  Enter Result
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
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
  // Reset initialization if orderItemId changes
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
        saveMutation.mutate(existingResultsData?.data.results || []);
        return;
      }
      if (e.shiftKey) {
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

const ResultEntry = ({ orderItemId, onBack, onChangeItem }: { orderItemId: number; onBack: () => void; onChangeItem: (id: number) => void }) => {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Custom Hook Logic
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

  // Fetch sibling items (using worklist cache if available, or fetch fresh)
  // We need to find other items for the SAME patient.
  const { data: worklistData } = useQuery({
    queryKey: ['result-worklist'],
    queryFn: () => resultApi.getWorklist(),
    staleTime: 60000, // Reuse worklist data for 1 minute
  });

  const patientId = (orderItemDetails?.data as any)?.order?.patient?.id;

  const siblingItems = useMemo(() => {
    if (!worklistData?.data.results || !patientId) return [];
    const allItems = worklistData.data.results as WorklistOrderItem[];
    return allItems.filter(item => item.order?.patient?.id === patientId && item.id !== orderItemId);
  }, [worklistData, patientId, orderItemId]);

  // Timeout detection
  useEffect(() => {
    if (isLoadingResults || isLoadingDetails) {
      const timer = setTimeout(() => setLoadingTimeout(true), 15000);
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

  if (loadingTimeout && isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.errorContainer}>
          <h2>Loading Timeout</h2>
          <button className={styles.retryButton} onClick={handleRetry}>Retry</button>
          <button className={styles.backButton} onClick={onBack}>Back</button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Loading results data...</p>
        </div>
      </div>
    );
  }

  if (isError || isDetailsError) {
    return (
      <div className={styles.container}>
        <div className={styles.errorContainer}>
          <p>Error loading results.</p>
          <button className={styles.backButton} onClick={onBack}>Back</button>
        </div>
      </div>
    );
  }

  const resultItems = existingResultsData?.data.results || [];
  const orderDetails = orderItemDetails?.data as any;
  const orderInfo = orderDetails?.order;
  const patientInfo = orderInfo?.patient;
  const testInfo = orderDetails?.test_name || orderDetails?.panel_name;
  const allVerified = resultItems.every((r: TestResult) => r.status === 'verified');
  const rejectedResults = resultItems.filter((r: TestResult) => r.status?.toLowerCase() === 'rejected');
  const verifyDisabled = !canVerify || saveMutation.isPending || verifyMutation.isPending;

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

      {/* Tabs for Sibling Tests */}
      {siblingItems.length > 0 && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
          <div style={{ padding: '8px 16px', background: '#3b82f6', color: 'white', borderRadius: '6px', fontWeight: 'bold' }}>
            Current: {testInfo}
          </div>
          {siblingItems.map(item => (
            <button
              key={item.id}
              onClick={() => onChangeItem(item.id)}
              style={{
                padding: '8px 16px',
                background: '#f1f5f9',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                cursor: 'pointer',
                color: '#475569'
              }}
            >
              {item.test_name || item.panel_name}
            </button>
          ))}
        </div>
      )}

      <div className={styles.header}>
        <div className={styles.headerTop}>
          <h1>Result Entry</h1>
          <span className={styles.orderId}>#{orderInfo?.order_id}</span>
        </div>
        <div className={styles.subtitle}>Test: <strong>{testInfo}</strong></div>
        {patientInfo && (
          <div className={styles.patientBanner}>
            <div className={styles.patientField}><span className={styles.fieldLabel}>Patient</span><span className={styles.fieldValue}>{patientInfo.full_name}</span></div>
            <div className={styles.patientField}><span className={styles.fieldLabel}>MRN</span><span className={styles.fieldValue}>{patientInfo.mrn}</span></div>
            <div className={styles.patientField}><span className={styles.fieldLabel}>Age/Sex</span><span className={styles.fieldValue}>{patientInfo.age}y / {patientInfo.gender}</span></div>
          </div>
        )}
      </div>

      {rejectedResults.length > 0 && (
        <div className={styles.rejectionNotice}>
          <strong>Returned for correction</strong>
          <ul>
            {rejectedResults.map((result) => (
              <li key={result.id}>{result.remarks}</li>
            ))}
          </ul>
        </div>
      )}

      <div className={styles.form}>
        <div className={styles.stickyActionBar}>
          {!allVerified && (
            <>
              <button onClick={() => saveMutation.mutate(resultItems)} disabled={saveMutation.isPending} className={styles.saveButton}>
                {saveMutation.isPending ? 'Saving...' : 'Draft'}
              </button>
              <button onClick={handleSaveAndVerify} disabled={verifyDisabled} className={`${styles.verifyMainButton} ${styles.saveButton}`}>
                {verifyMutation.isPending ? 'Verifying...' : 'Verify Draft'}
              </button>
            </>
          )}
        </div>

        <div className={styles.tableContainer}>
          <table className={styles.resultTable}>
            <thead>
              <tr>
                <th>Test Parameter</th>
                <th>Result Value</th>
                <th>Unit</th>
                <th>Remarks</th>
                <th>Ref. Range</th>
              </tr>
            </thead>
            <tbody>
              {resultItems.map((result: TestResult, index: number) => (
                <tr key={result.test_parameter}>
                  <td>{result.parameter_name}</td>
                  <td>
                    <input
                      type="text"
                      data-index={index}
                      value={results[result.test_parameter] || ''}
                      onChange={(e) => setResults(prev => ({ ...prev, [result.test_parameter]: e.target.value }))}
                      onKeyDown={(e) => handleKeyDown(e, result, index, resultItems.length)}
                      className={styles.resultInput}
                      disabled={result.status === 'verified'}
                    />
                  </td>
                  <td>{result.unit}</td>
                  <td>
                    <textarea
                      className={styles.remarksInput}
                      value={remarks[result.test_parameter] || ''}
                      onChange={(e) => setRemarks(prev => ({ ...prev, [result.test_parameter]: e.target.value }))}
                    />
                  </td>
                  <td>{result.reference_range}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default function ResultsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const orderItemIdStr = searchParams.get('orderItemId') || searchParams.get('orderItem');
  const orderItemId = orderItemIdStr ? Number(orderItemIdStr) : null;

  const handleChangeItem = (id: number) => {
    setSearchParams({ orderItemId: id.toString() });
  };

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
          onChangeItem={handleChangeItem}
        />
      ) : (
        <ResultWorklist
          onSelect={(id) => setSearchParams({ orderItemId: id.toString() })}
        />
      )}
    </div>
  );
}
