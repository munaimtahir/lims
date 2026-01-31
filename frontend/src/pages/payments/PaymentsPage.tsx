import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { paymentApi } from '../../api/services';
import type { Payment, PaymentMethod } from '../../types';
import { useBranding } from '../../contexts/BrandingContext';
import { formatCurrency } from '../../utils/currency';
import styles from './PaymentsPage.module.css';

export default function PaymentsPage() {
  const queryClient = useQueryClient();
  const { branding } = useBranding();
  const currency = branding?.currency || 'PKR';
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
  const [amount, setAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('cash');
  const [transactionId, setTransactionId] = useState('');
  const [notes, setNotes] = useState('');

  const { data: paymentsData, isLoading, error } = useQuery({
    queryKey: ['payments'],
    queryFn: () => paymentApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: (data: Partial<Payment>) => paymentApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      setIsModalOpen(false);
      // Reset form
      setSelectedOrderId(null);
      setAmount('');
      setPaymentMethod('cash');
      setTransactionId('');
      setNotes('');
    },
  });

  const downloadReceiptMutation = useMutation({
    mutationFn: async (paymentId: number) => {
      const blob = await paymentApi.getReceipt(paymentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `receipt_${paymentId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });

  const payments = paymentsData?.results || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrderId || !amount) {
      alert('Please fill in all required fields');
      return;
    }
    createMutation.mutate({
      order: selectedOrderId,
      amount: amount,
      payment_method: paymentMethod,
      transaction_id: transactionId || undefined,
      notes: notes || undefined,
    });
  };

  const handleDownloadReceipt = (paymentId: number) => {
    downloadReceiptMutation.mutate(paymentId);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Payments</h1>
        <button onClick={() => setIsModalOpen(true)} className={styles.addButton}>
          + Record Payment
        </button>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading payments...</div>
      ) : error ? (
        <div className={styles.error}>Failed to load payments</div>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Amount</th>
              <th>Payment Method</th>
              <th>Transaction ID</th>
              <th>Date</th>
              <th>Recorded By</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((payment) => (
              <tr key={payment.id}>
                <td>Order #{payment.order}</td>
                <td className={styles.amount}>{formatCurrency(payment.amount, currency)}</td>
                <td>
                  <span className={styles.methodBadge}>
                    {payment.payment_method.replace('_', ' ')}
                  </span>
                </td>
                <td>{payment.transaction_id || '-'}</td>
                <td>{new Date(payment.payment_date).toLocaleString()}</td>
                <td>{payment.recorded_by_name || '-'}</td>
                <td>
                  <button
                    onClick={() => handleDownloadReceipt(payment.id)}
                    className={styles.receiptButton}
                    disabled={downloadReceiptMutation.isPending}
                  >
                    Receipt
                  </button>
                </td>
              </tr>
            ))}
            {payments.length === 0 && (
              <tr>
                <td colSpan={7} className={styles.noData}>
                  No payments found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {isModalOpen && (
        <div className={styles.modalOverlay} onClick={() => setIsModalOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Record Payment</h2>
              <button onClick={() => setIsModalOpen(false)} className={styles.closeButton}>
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit} className={styles.modalForm}>
              <div className={styles.formGroup}>
                <label>Order ID *</label>
                <input
                  type="number"
                  value={selectedOrderId || ''}
                  onChange={(e) => setSelectedOrderId(e.target.value ? Number(e.target.value) : null)}
                  required
                  className={styles.input}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  required
                  className={styles.input}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Payment Method *</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
                  required
                  className={styles.select}
                >
                  <option value="cash">Cash</option>
                  <option value="card">Credit/Debit Card</option>
                  <option value="bank_transfer">Bank Transfer</option>
                  <option value="mobile_money">Mobile Money</option>
                  <option value="insurance">Insurance</option>
                </select>
              </div>
              <div className={styles.formGroup}>
                <label>Transaction ID</label>
                <input
                  type="text"
                  value={transactionId}
                  onChange={(e) => setTransactionId(e.target.value)}
                  className={styles.input}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className={styles.textarea}
                  rows={3}
                />
              </div>
              <div className={styles.modalActions}>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className={styles.cancelButton}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className={styles.submitButton}
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? 'Recording...' : 'Record Payment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
