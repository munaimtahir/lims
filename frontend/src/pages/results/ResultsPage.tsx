import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { resultApi, orderApi } from '../../api/services';
import type { OrderItem } from '../../types';
import styles from './ResultsPage.module.css';

interface TestParameter {
  id: number;
  parameter_name: string;
  unit: string;
  reference_range: string;
  reference_min_male?: number;
  reference_max_male?: number;
  critical_low?: number;
  critical_high?: number;
}

interface ExistingResult {
  test_parameter: number;
  result_value: string;
}

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

  useQuery<{ results: ExistingResult[] }>({
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

  const test = orderItemData?.items?.find((item: OrderItem) => item.id === selectedOrderItem);
  const testParameters: TestParameter[] = (test as { test?: { parameters?: TestParameter[] }; panel?: { tests?: { parameters: TestParameter[] }[] } })?.test?.parameters || (test as { panel?: { tests?: { parameters: TestParameter[] }[] } })?.panel?.tests?.flatMap((t) => t.parameters) || [];

  const handleResultChange = (paramId: number, value: string) => {
    setResults((prev) => ({ ...prev, [paramId]: value }));
  };

  const handleRemarksChange = (paramId: number, value: string) => {
    setRemarks((prev) => ({ ...prev, [paramId]: value }));
  };

  const getFlagClass = (value: string, param: TestParameter) => {
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
          {testParameters.map((param) => (
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
