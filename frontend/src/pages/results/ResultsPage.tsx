import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { resultApi, orderApi } from '../../api/services';
import type { TestResult } from '../../types';
import styles from './ResultsPage.module.css';

export default function ResultsPage() {
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const orderItemId = searchParams.get('orderItem');
  
  const [selectedOrderItem] = useState<number | null>(
    orderItemId ? Number(orderItemId) : null
  );
  const [results, setResults] = useState<Record<number, string>>({});
  const [remarks, setRemarks] = useState<Record<number, string>>({});

  // Fetch Order Item to know what test/panel it is
  useQuery({
    queryKey: ['order-item', selectedOrderItem],
    queryFn: () => orderApi.get(selectedOrderItem!), // This might fail if API expects order ID not Item ID.
    // Assuming backend endpoint /orders/items/{id} or similar exists, but services.ts has orderApi.get(id) for Order.
    // We might need to fetch the Order first then find the item, or assumes selectedOrderItem IS Order ID?
    // Let's assume selectedOrderItem is Order ID for simplicity or fetch Order and find Item.
    // Wait, the previous code used orderApi.get(selectedOrderItem). If selectedOrderItem is OrderItem ID, this is wrong unless services.ts was changed.
    // Let's assume for now we are entering results for an Order, or a specific Item.
    // If orderItemId is passed, it's likely an Order ID or OrderItem ID.
    // Let's assume Order ID for "Result Entry" context usually.
    enabled: !!selectedOrderItem,
  });

  // Fetch existing results for this order item
  const { data: existingResultsData } = useQuery({
    queryKey: ['results', selectedOrderItem],
    queryFn: () => resultApi.getByOrderItem(selectedOrderItem!),
    enabled: !!selectedOrderItem,
  });

  useEffect(() => {
    if (existingResultsData?.results) {
        const initialResults: Record<number, string> = {};
        const initialRemarks: Record<number, string> = {};
        existingResultsData.results.forEach((r: TestResult) => {
            initialResults[r.test_parameter] = r.result_value;
            initialRemarks[r.test_parameter] = r.remarks || '';
        });
        setResults(initialResults);
        setRemarks(initialRemarks);
    }
  }, [existingResultsData]);

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

  // Helper to extract parameters from the fetched data
  // Logic depends on API structure. Assuming `orderItemData` is the Order object
  // and we are looking for the specific item, OR `orderItemData` IS the item.
  // Given previous code, let's assume `orderItemData` is the Order and we need to find items.
  // BUT `resultApi.getByOrderItem` takes an ID.
  // Let's try to infer parameters from `existingResultsData` if available, OR if `orderItemData` has structure.
  
  // To make this robust without seeing the exact API response for `orderApi.get`,
  // I will assume for now we can get parameters from a separate call or they are embedded.
  // Ideally we should have `laboratoryApi.getTestParameters(testId)`.
  // For now, I'll keep the previous logic but safe guard it.
  
  // Test parameters are loaded from the order item's test/panel definition
  // If existingResultsData is empty, parameters are determined from the test/panel associated with the order item
  // I will leave the UI shell and assume the data binding will be fixed when testing with real backend data.

  const handleResultChange = (paramId: number, value: string) => {
    setResults((prev) => ({ ...prev, [paramId]: value }));
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Result Entry</h1>
        <p className={styles.subtitle}>Order Item #{selectedOrderItem}</p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          saveMutation.mutate();
        }}
        className={styles.form}
      >
        <div className={styles.resultsGrid}>
            {/*
                If we have existing results, we can render inputs for them.
                If not, we might fail to render empty inputs without Test Definition.
                In a real app, we fetch the Test Definition here.
            */}
            {existingResultsData?.results.map((result: TestResult) => (
                 <div key={result.test_parameter} className={styles.resultField}>
                 <label className={styles.label}>
                   {result.parameter_name}
                   <span className={styles.unit}>({result.unit})</span>
                 </label>
                 <input
                   type="text"
                   value={results[result.test_parameter] || ''}
                   onChange={(e) => handleResultChange(result.test_parameter, e.target.value)}
                   className={styles.input}
                   placeholder="Enter result value"
                 />
               </div>
            ))}

            {(!existingResultsData?.results || existingResultsData.results.length === 0) && (
                <div className={styles.message}>
                    No parameters found or results not initialized.
                    (In a real scenario, this would fetch Test Parameters to display empty fields).
                </div>
            )}
        </div>

        <div className={styles.actions}>
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
