import { useState, useEffect, type KeyboardEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { resultApi, orderApi } from '../../api/services/index';
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
  test_name?: string;
  panel_name?: string;
  test_code?: string;
  panel_code?: string;
  status: string;
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
    return (
      item.order?.order_id?.toLowerCase().includes(term) ||
      item.order?.patient?.full_name?.toLowerCase().includes(term) ||
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
                <th style={{ width: '15%' }}>Order ID</th>
                <th style={{ width: '30%' }}>Patient</th>
                <th style={{ width: '30%' }}>Test / Panel</th>
                <th style={{ width: '10%' }}>Status</th>
                <th style={{ width: '15%' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className={styles.resultRow}>
                  <td>
                    <span className={styles.orderId}>{item.order?.order_id}</span>
                  </td>
                  <td>
                    <div className={styles.patientInfo}>
                      <span className={styles.patientName}>{item.order?.patient?.full_name}</span>
                      <span className={styles.patientSub}>
                        {item.order?.patient?.age}y / {item.order?.patient?.gender} • {item.order?.patient?.mrn}
                      </span>
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
                    <span className={`${styles.statusBadge} ${styles['status-' + (item.status?.toLowerCase() || 'pending')]}`}>
                      {item.status}
                    </span>
                  </td>
                  <td>
                    <button
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
  
    const { data: existingResultsData, isLoading: isLoadingResults } = useQuery({
      queryKey: ['results', orderItemId],
      queryFn: () => resultApi.getByOrderItem(orderItemId),
      enabled: !!orderItemId,
    });
  
    useEffect(() => {
      if (existingResultsData?.data.results) {
        const initialResults: Record<number, string> = {};
        const initialRemarks: Record<number, string> = {};
        existingResultsData.data.results.forEach((r: TestResult) => {
          initialResults[r.test_parameter] = r.result_value || '';
          initialRemarks[r.test_parameter] = r.remarks || '';
        });
        setResults(initialResults);
        setRemarks(initialRemarks);
      }
    }, [existingResultsData]);
  
    const saveMutation = useMutation({
        mutationFn: async (resultsToSave: TestResult[]) => {
          const payload = resultsToSave.map(r => ({
            order_item: orderItemId,
            test_parameter: r.test_parameter,
            result_value: results[r.test_parameter] ?? '',
            remarks: remarks[r.test_parameter] ?? '',
          }));
          return resultApi.bulkEntry(payload);
        },
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['results', orderItemId] });
          queryClient.invalidateQueries({ queryKey: ['result-worklist'] });
        },
      });
  
      const verifyMutation = useMutation({
        mutationFn: async (resultIds: number[]) => {
          return resultApi.bulkVerify(resultIds);
        },
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['results', orderItemId] });
          queryClient.invalidateQueries({ queryKey: ['result-worklist'] });
          alert('Results verified successfully!');
        },
        onError: (error: any) => {
          const errorData = error.response?.data;
          if (errorData && errorData.details) {
            alert(`Verification failed:\n- ${errorData.details.join('\n- ')}`);
          } else {
            alert('An unexpected error occurred during verification.');
          }
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
      saveMutation,
      verifyMutation,
      handleKeyDown,
    };
  };

const ResultEntry = ({ orderItemId, onBack }: { orderItemId: number; onBack: () => void }) => {
  const {
    results,
    setResults,
    existingResultsData,
    isLoadingResults,
    saveMutation,
    verifyMutation,
    handleKeyDown,
  } = useResultEntry(orderItemId);

  const { data: orderItemDetails, isLoading: isLoadingDetails } = useQuery({
    queryKey: ['order-item-details', orderItemId],
    queryFn: () => orderApi.getOrderItem(orderItemId),
    enabled: !!orderItemId,
  });

  const handleSaveAndVerify = async () => {
    await saveMutation.mutateAsync(existingResultsData?.data.results || []);
    if (confirm('This will lock all results and prevent edits. Continue?')) {
      const resultIds = existingResultsData?.data.results.map((r: TestResult) => r.id) || [];
      await verifyMutation.mutateAsync(resultIds);
    }
  };
  
  const isLoading = isLoadingResults || isLoadingDetails;

  if (isLoading) return <div className={styles.message}>Loading results...</div>;

  const resultItems = existingResultsData?.data.results || [];
  const orderInfo = (orderItemDetails?.data as any)?.order;
  const patientInfo = orderInfo?.patient;
  const testInfo = (orderItemDetails?.data as any)?.test_name || (orderItemDetails?.data as any)?.panel_name;
  const allVerified = resultItems.every((r: TestResult) => r.status === 'verified');


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

          <div className={styles.footer}>
          {!allVerified && (
            <>
              <button
                className={styles.saveButton}
                onClick={() => saveMutation.mutate(resultItems)}
                disabled={saveMutation.isPending || verifyMutation.isPending}
              >
                {saveMutation.isPending ? 'Saving...' : 'Save Draft'}
              </button>
              <button
                className={`${styles.verifyMainButton} ${styles.saveButton}`}
                onClick={handleSaveAndVerify}
                disabled={saveMutation.isPending || verifyMutation.isPending}
              >
                {verifyMutation.isPending ? 'Verifying...' : 'Save & Verify All'}
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
