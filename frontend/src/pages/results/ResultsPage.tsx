import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { resultApi, orderApi } from '../../api/services';
import type { TestResult } from '../../types';
import styles from './ResultsPage.module.css';

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
  };
  test?: {
    test_name: string;
    test_code: string;
  };
  panel?: {
    panel_name: string;
    panel_code: string;
  };
  status: string;
}

const ResultWorklist = ({ onSelect }: { onSelect: (id: number) => void }) => {
  const { data: worklistData, isLoading } = useQuery({
    queryKey: ['result-worklist'],
    queryFn: () => resultApi.getWorklist(),
  });

  // Handle potential pagination or list response
  const items: WorklistOrderItem[] = Array.isArray(worklistData)
    ? worklistData
    : worklistData?.results || [];

  if (isLoading) return <div className={styles.loading}>Loading worklist...</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Pending Results Worklist</h1>
        <p className={styles.subtitle}>Select a test to enter results</p>
      </div>

      <div className={styles.tableContainer}>
        {items.length === 0 ? (
          <div className={styles.emptyState}>No pending results found.</div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Patient</th>
                <th>Test / Panel</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className={styles.row}>
                  <td>{item.order?.order_id}</td>
                  <td>
                    <div className={styles.patientInfo}>
                      <span className={styles.patientName}>{item.order?.patient?.full_name}</span>
                      <span className={styles.patientSub}>
                        {item.order?.patient?.age}y / {item.order?.patient?.gender}
                      </span>
                    </div>
                  </td>
                  <td>
                    {item.test?.test_name || item.panel?.panel_name || 'Unknown Test'}
                  </td>
                  <td>
                    <span className={`${styles.badge} ${styles[item.status?.toLowerCase()]}`}>
                      {item.status}
                    </span>
                  </td>
                  <td>
                    <button
                      className={styles.actionButton}
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

const ResultEntry = ({ orderItemId, onBack }: { orderItemId: number; onBack: () => void }) => {
  const queryClient = useQueryClient();
  // State for form inputs
  const [results, setResults] = useState<Record<number, string>>({});
  const [remarks, setRemarks] = useState<Record<number, string>>({});

  // Ensure results exist (create blank rows if needed)
  const ensureMutation = useMutation({
    mutationFn: () => resultApi.ensure(orderItemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['results', orderItemId] });
    },
  });

  useEffect(() => {
    ensureMutation.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderItemId]);

  // Fetch results
  const { data: existingResultsData, isLoading: isLoadingResults } = useQuery({
    queryKey: ['results', orderItemId],
    queryFn: () => resultApi.getByOrderItem(orderItemId),
    enabled: !!orderItemId,
  });

  // Fetch order item details to get patient and test info
  const { data: orderItemDetails, isLoading: isLoadingDetails } = useQuery({
    queryKey: ['order-item-details', orderItemId],
    queryFn: () => orderApi.getOrderItem(orderItemId),
    enabled: !!orderItemId,
  });

  // If orderItemDetails doesn't have nested order, we might need another fetch, 
  // but let's see if we can get it from the worklist data or if it's returning it.
  // Given WorklistOrderItem local interface, we expect it there.
  const orderItem = orderItemDetails as unknown as WorklistOrderItem;
  const orderInfo = orderItem?.order;
  const patientInfo = orderInfo?.patient;
  const testInfo = orderItem?.test || orderItem?.panel;

  // Initialize form state when data loads
  useEffect(() => {
    if (existingResultsData?.results) {
      const initialResults: Record<number, string> = {};
      const initialRemarks: Record<number, string> = {};
      existingResultsData.results.forEach((r: TestResult) => {
        initialResults[r.test_parameter] = r.result_value || '';
        initialRemarks[r.test_parameter] = r.remarks || '';
      });
      setResults(initialResults);
      setRemarks(initialRemarks);
    }
  }, [existingResultsData]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const resultsArray = Object.entries(results).map(([paramId, value]) => ({
        order_item: orderItemId,
        test_parameter: Number(paramId),
        result_value: value,
        remarks: remarks[Number(paramId)] || '',
      }));
      return resultApi.bulkEntry(resultsArray);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['results', orderItemId] });
      queryClient.invalidateQueries({ queryKey: ['result-worklist'] });
    },
  });

  const verifyMutation = useMutation({
    mutationFn: async (resultId: number) => {
      return resultApi.verify(resultId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['results', orderItemId] });
    },
    onError: (error: any) => {
      alert(`Verification failed: ${error?.response?.data?.error || 'Unknown error'}`);
    }
  });

  const handleSave = async (silent = false) => {
    await saveMutation.mutateAsync();
    if (!silent) alert('Results saved successfully!');
  };

  const handleVerify = async (result: TestResult) => {
    await handleSave(true);
    if (result.id) {
      if (confirm('Are you sure you want to verify this result? It will be locked.')) {
        verifyMutation.mutate(result.id);
      }
    } else {
      alert('Please save the result first.');
    }
  };

  const isLoading = isLoadingResults || isLoadingDetails;

  if (isLoading) return <div className={styles.loading}>Loading results...</div>;

  return (
    <div className={styles.container}>
      <button className={styles.backButton} onClick={onBack}>
        &larr; Back to Worklist
      </button>

      <div className={styles.header}>
        <div className={styles.headerTop}>
          <h1>Result Entry</h1>
          <span className={styles.orderId}>#{orderInfo?.order_id || 'ID Loading...'}</span>
        </div>
        {patientInfo && (
          <div className={styles.patientBanner}>
            <div>
              <strong>Patient:</strong> {patientInfo.full_name}
            </div>
            <div>
              <strong>MRN:</strong> {patientInfo.mrn}
            </div>
            <div>
              <strong>Info:</strong> {patientInfo.age}y / {patientInfo.gender}
            </div>
          </div>
        )}
        <p className={styles.subtitle}>
          Test: {
            (testInfo && 'test_name' in testInfo ? testInfo.test_name :
              testInfo && 'panel_name' in testInfo ? testInfo.panel_name :
                'Loading Test Info...')
          }
        </p>
      </div>

      {(!existingResultsData?.results || existingResultsData.results.length === 0) ? (
        <div className={styles.message}>Initializing result form...</div>
      ) : (
        <div className={styles.form}>
          <div className={styles.resultsGrid}>
            {existingResultsData.results.map((result: TestResult) => {
              const isVerified = result.status === 'verified';
              return (
                <div key={result.test_parameter} className={styles.resultField}>
                  <div className={styles.fieldLabelRow}>
                    <label className={styles.label}>
                      {result.parameter_name || `Param ${result.test_parameter}`}
                    </label>
                    <span className={styles.unit}>
                      {result.unit}
                    </span>
                  </div>

                  <div className={styles.inputGroup}>
                    {isVerified ? (
                      <div className={styles.verifiedValue}>
                        {result.result_value}
                        <span className={styles.verifiedBadge}>Verified</span>
                      </div>
                    ) : (
                      <>
                        <input
                          type="text"
                          value={results[result.test_parameter] || ''}
                          onChange={(e) => setResults(prev => ({ ...prev, [result.test_parameter]: e.target.value }))}
                          className={styles.input}
                          placeholder="Value"
                        />
                        <button
                          className={styles.verifyButton}
                          onClick={() => handleVerify(result)}
                          title="Save & Verify"
                        >
                          Verify
                        </button>
                      </>
                    )}
                  </div>
                  <div className={styles.referenceRange}>
                    Status: <span style={{ fontWeight: 600 }}>{result.status}</span>
                    {result.flag && <span className={styles.flag}> [{result.flag}]</span>}
                  </div>
                </div>
              );
            })}
          </div>

          <div className={styles.actions}>
            <button
              className={styles.saveButton}
              onClick={() => handleSave(false)}
              disabled={saveMutation.isPending}
            >
              {saveMutation.isPending ? 'Saving...' : 'Save All Changes'}
            </button>
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


