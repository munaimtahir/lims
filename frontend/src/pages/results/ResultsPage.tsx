import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { resultApi, orderApi } from '../../api/services';
import type { TestResult, OrderItem } from '../../types';
import styles from './ResultsPage.module.css';

export default function ResultsPage() {
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const orderItemId = searchParams.get('orderItem');
  
  const [selectedOrderItem, setSelectedOrderItem] = useState<number | null>(
    orderItemId ? Number(orderItemId) : null
  );
  const [results, setResults] = useState<Record<number, string>>({});
  const [remarks, setRemarks] = useState<Record<number, string>>({});

  const { data: orderItemData } = useQuery({
    queryKey: ['order-item', selectedOrderItem],
    queryFn: () => orderApi.get(selectedOrderItem!),
    enabled: !!selectedOrderItem,
  });

  const { data: existingResults } = useQuery({
    queryKey: ['results', selectedOrderItem],
    queryFn: () => resultApi.getByOrderItem(selectedOrderItem!),
    enabled: !!selectedOrderItem,
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!selectedOrderItem) return;
      
      const resultsArray = Object.entries(results).map(([paramId, value]) => ({
        order_item: selectedOrderItem,
        test_parameter: Number(paramId),
        result_value: value,
        remarks: remarks[Number(paramId)] || '',
      }));

      return resultApi.bulkEntry(resultsArray);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['results'] });
      queryClient.invalidateQueries({ queryKey: ['result-entry-worklist'] });
      alert('Results saved successfully!');
      // Reset form
      setResults({});
      setRemarks({});
    },
  });

  useEffect(() => {
    if (existingResults?.results) {
      const existing = existingResults.results.reduce((acc, result) => {
        acc[result.test_parameter] = result.result_value;
        return acc;
      }, {} as Record<number, string>);
      setResults(existing);
    }
  }, [existingResults]);

  if (!selectedOrderItem) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h1>Result Entry</h1>
          <p>Please select an order item from the worklist to enter results.</p>
        </div>
      </div>
    );
  }

  const order = orderData;
  const test = orderItem?.items?.find((item: OrderItem) => item.id === selectedOrderItem);
  const testParameters = test?.test?.parameters || test?.panel?.tests?.flatMap((t: any) => t.parameters) || [];

  const handleResultChange = (paramId: number, value: string) => {
    setResults((prev) => ({ ...prev, [paramId]: value }));
  };

  const handleRemarksChange = (paramId: number, value: string) => {
    setRemarks((prev) => ({ ...prev, [paramId]: value }));
  };

  const getFlagClass = (value: string, param: any) => {
    try {
      const numValue = parseFloat(value);
      // Simple flag calculation (would be done by backend)
      if (param.critical_low && numValue <= param.critical_low) return styles.flagCritical;
      if (param.critical_high && numValue >= param.critical_high) return styles.flagCritical;
      if (param.reference_min_male && numValue < param.reference_min_male) return styles.flagAbnormal;
      if (param.reference_max_male && numValue > param.reference_max_male) return styles.flagAbnormal;
      return styles.flagNormal;
    } catch {
      return '';
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Result Entry</h1>
        <p className={styles.subtitle}>
          {test?.test_name || test?.panel_name || 'Enter test results'}
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          saveMutation.mutate();
        }}
        className={styles.form}
      >
        <div className={styles.resultsGrid}>
          {testParameters.map((param: any) => (
            <div key={param.id} className={styles.resultField}>
              <label className={styles.label}>
                {param.parameter_name}
                <span className={styles.unit}>({param.unit})</span>
              </label>
              <input
                type="text"
                value={results[param.id] || ''}
                onChange={(e) => handleResultChange(param.id, e.target.value)}
                className={`${styles.input} ${getFlagClass(results[param.id] || '', param)}`}
                placeholder="Enter result value"
              />
              {param.reference_min_male && param.reference_max_male && (
                <div className={styles.referenceRange}>
                  Reference: {param.reference_min_male} - {param.reference_max_male} {param.unit}
                </div>
              )}
              <textarea
                value={remarks[param.id] || ''}
                onChange={(e) => handleRemarksChange(param.id, e.target.value)}
                className={styles.remarks}
                placeholder="Remarks (optional)"
                rows={2}
              />
            </div>
          ))}
        </div>

        <div className={styles.actions}>
          <button
            type="button"
            onClick={() => {
              setSelectedOrderItem(null);
              setResults({});
              setRemarks({});
            }}
            className={styles.cancelButton}
          >
            Cancel
          </button>
          <button
            type="submit"
            className={styles.saveButton}
            disabled={saveMutation.isPending}
          >
            {saveMutation.isPending ? 'Saving...' : 'Save Results'}
          </button>
        </div>
      </form>
    </div>
  );
}
