import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resultApi } from '../../api/services';
import type { TestResult } from '../../types';
import styles from './VerificationQueuePage.module.css';

export default function VerificationQueuePage() {
  const queryClient = useQueryClient();
  const [selectedResult, setSelectedResult] = useState<TestResult | null>(null);

  const { data: queueData, isLoading, error } = useQuery({
    queryKey: ['verification-queue'],
    queryFn: () => resultApi.getVerificationQueue(),
  });

  const verifyMutation = useMutation({
    mutationFn: (resultId: number) => resultApi.verify(resultId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
      queryClient.invalidateQueries({ queryKey: ['results'] });
      setSelectedResult(null);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ resultId, reason }: { resultId: number; reason: string }) =>
      resultApi.reject(resultId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verification-queue'] });
      queryClient.invalidateQueries({ queryKey: ['results'] });
      setSelectedResult(null);
    },
  });

  const results = queueData?.results || [];

  const handleVerify = (resultId: number) => {
    if (confirm('Verify this result?')) {
      verifyMutation.mutate(resultId);
    }
  };

  const handleReject = (resultId: number) => {
    const reason = prompt('Enter rejection reason:');
    if (reason) {
      rejectMutation.mutate({ resultId, reason });
    }
  };

  const getFlagClass = (flag: string) => {
    switch (flag) {
      case 'critical_low':
      case 'critical_high':
        return styles.flagCritical;
      case 'high':
      case 'low':
        return styles.flagAbnormal;
      default:
        return styles.flagNormal;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Verification Queue</h1>
        <p className={styles.subtitle}>Results pending pathologist verification</p>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading queue...</div>
      ) : error ? (
        <div className={styles.error}>Failed to load queue</div>
      ) : (
        <>
          <div className={styles.stats}>
            <div className={styles.statCard}>
              <div className={styles.statValue}>{results.length}</div>
              <div className={styles.statLabel}>Pending Verification</div>
            </div>
          </div>

          {results.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No results pending verification</p>
            </div>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Parameter</th>
                  <th>Result Value</th>
                  <th>Unit</th>
                  <th>Flag</th>
                  <th>Entered By</th>
                  <th>Entered At</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result) => (
                  <tr key={result.id}>
                    <td>{result.parameter_name}</td>
                    <td className={styles.resultValue}>{result.result_value}</td>
                    <td>{result.unit}</td>
                    <td>
                      <span className={`${styles.flagBadge} ${getFlagClass(result.flag)}`}>
                        {result.flag.replace('_', ' ')}
                      </span>
                    </td>
                    <td>{result.entered_by_name || '-'}</td>
                    <td>{new Date(result.entered_at).toLocaleString()}</td>
                    <td>
                      <div className={styles.actions}>
                        <button
                          onClick={() => handleVerify(result.id)}
                          className={styles.verifyButton}
                          disabled={verifyMutation.isPending}
                        >
                          Verify
                        </button>
                        <button
                          onClick={() => handleReject(result.id)}
                          className={styles.rejectButton}
                          disabled={rejectMutation.isPending}
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}
