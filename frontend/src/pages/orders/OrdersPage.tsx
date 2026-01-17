import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { orderApi, patientApi, laboratoryApi, paymentApi } from '../../api/services';
import type { Order, Patient, OrderCreateRequest } from '../../types';
import styles from './OrdersPage.module.css';

export default function OrdersPage() {
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data: ordersData, isLoading } = useQuery({
    queryKey: ['orders', statusFilter],
    queryFn: () => orderApi.list({ status: statusFilter || undefined }),
  });

  const orders = ordersData?.results || [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NEW':
        return styles.statusPending;
      case 'COLLECTED':
      case 'IN_PROCESS':
        return styles.statusInProgress;
      case 'VERIFIED':
      case 'PUBLISHED':
        return styles.statusCompleted;
      case 'CANCELLED':
        return styles.statusCancelled;
      default:
        return '';
    }
  };

  const handleCancelOrder = (orderId: number) => {
      if (confirm('Are you sure you want to cancel this order?')) {
          orderApi.cancel(orderId).then(() => {
              queryClient.invalidateQueries({ queryKey: ['orders'] });
          });
      }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Orders</h1>
        <button onClick={() => setIsCreateModalOpen(true)} className={styles.addButton}>
          + Create Order
        </button>
      </div>

      <div className={styles.filters}>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={styles.filterSelect}
        >
          <option value="">All Statuses</option>
          <option value="NEW">New</option>
          <option value="COLLECTED">Collected</option>
          <option value="IN_PROCESS">In Process</option>
          <option value="VERIFIED">Verified</option>
          <option value="PUBLISHED">Published</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading orders...</div>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Patient</th>
              <th>Tests</th>
              <th>Total</th>
              <th>Status</th>
              <th>Payment</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.id}>
                <td>{order.order_id}</td>
                <td>{order.patient_name}</td>
                <td>{order.items.length} items</td>
                <td>PKR {order.net_amount}</td>
                <td>
                  <span className={`${styles.statusBadge} ${getStatusColor(order.status)}`}>
                    {order.status.replace('_', ' ')}
                  </span>
                </td>
                <td>
                  <span className={order.is_paid ? styles.paidBadge : styles.unpaidBadge}>
                    {order.is_paid ? 'Paid' : 'Unpaid'}
                  </span>
                </td>
                <td>{new Date(order.created_at).toLocaleDateString()}</td>
                <td>
                  <div className={styles.actionButtons}>
                    <button onClick={() => setSelectedOrder(order)} className={styles.viewButton}>
                      View
                    </button>
                    {!order.is_paid && order.status !== 'CANCELLED' as any && (
                      <button
                        onClick={() => {
                          setSelectedOrder(order);
                          setIsPaymentModalOpen(true);
                        }}
                        className={styles.payButton}
                      >
                        Pay
                      </button>
                    )}
                    {order.status !== 'CANCELLED' as any && order.status !== 'PUBLISHED' as any && (
                        <button onClick={() => handleCancelOrder(order.id)} className={styles.cancelButton}>
                            Cancel
                        </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {orders.length === 0 && (
              <tr>
                <td colSpan={8} className={styles.noData}>
                  No orders found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {isCreateModalOpen && (
        <CreateOrderModal
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['orders'] });
            setIsCreateModalOpen(false);
          }}
        />
      )}

      {selectedOrder && !isPaymentModalOpen && (
        <OrderDetailModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
        />
      )}

      {isPaymentModalOpen && selectedOrder && (
        <PaymentModal
          order={selectedOrder}
          onClose={() => {
            setIsPaymentModalOpen(false);
            setSelectedOrder(null);
          }}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['orders'] });
            setIsPaymentModalOpen(false);
            setSelectedOrder(null);
          }}
        />
      )}
    </div>
  );
}

function CreateOrderModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientSearch, setPatientSearch] = useState('');
  const [selectedTests, setSelectedTests] = useState<number[]>([]);
  const [selectedPanels, setSelectedPanels] = useState<number[]>([]);
  const [discount, setDiscount] = useState('0');

  const { data: patientsData } = useQuery({
    queryKey: ['patients', patientSearch],
    queryFn: () => patientApi.search(patientSearch),
    enabled: patientSearch.length >= 2,
  });

  const { data: testsData } = useQuery({
    queryKey: ['tests'],
    queryFn: () => laboratoryApi.getTests({ is_active: true }),
  });

  const { data: panelsData } = useQuery({
    queryKey: ['panels'],
    queryFn: () => laboratoryApi.getPanels({ is_active: true }),
  });

  const createMutation = useMutation({
    mutationFn: (data: OrderCreateRequest) => orderApi.create(data),
    onSuccess,
  });

  const tests = testsData?.results || [];
  const panels = panelsData?.results || [];
  const patients = patientsData?.results || [];

  const calculateTotal = () => {
    let total = 0;
    selectedTests.forEach((id) => {
      const test = tests.find((t) => t.id === id);
      if (test) total += parseFloat(test.price);
    });
    selectedPanels.forEach((id) => {
      const panel = panels.find((p) => p.id === id);
      if (panel) total += parseFloat(panel.price);
    });
    return total - parseFloat(discount || '0');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatient) return;
    
    createMutation.mutate({
      patient: selectedPatient.id,
      test_ids: selectedTests,
      panel_ids: selectedPanels,
      discount: discount || '0',
    });
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h2>Create New Order</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <form onSubmit={handleSubmit} className={styles.form}>
          {/* Patient Selection */}
          <div className={styles.formGroup}>
            <label>Patient *</label>
            {selectedPatient ? (
              <div className={styles.selectedPatient}>
                <span>{selectedPatient.full_name} ({selectedPatient.patient_id})</span>
                <button type="button" onClick={() => setSelectedPatient(null)}>Change</button>
              </div>
            ) : (
              <div>
                <input
                  type="text"
                  placeholder="Search patient by name or phone..."
                  value={patientSearch}
                  onChange={(e) => setPatientSearch(e.target.value)}
                />
                {patients.length > 0 && (
                  <div className={styles.patientDropdown}>
                    {patients.map((p) => (
                      <div
                        key={p.id}
                        onClick={() => {
                          setSelectedPatient(p);
                          setPatientSearch('');
                        }}
                        className={styles.patientOption}
                      >
                        {p.full_name} - {p.patient_id}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Tests Selection */}
          <div className={styles.formGroup}>
            <label>Tests</label>
            <div className={styles.checkboxGrid}>
              {tests.map((test) => (
                <label key={test.id} className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={selectedTests.includes(test.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTests([...selectedTests, test.id]);
                      } else {
                        setSelectedTests(selectedTests.filter((id) => id !== test.id));
                      }
                    }}
                  />
                  <span>{test.test_name} - PKR {test.price}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Panels Selection */}
          <div className={styles.formGroup}>
            <label>Panels</label>
            <div className={styles.checkboxGrid}>
              {panels.map((panel) => (
                <label key={panel.id} className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={selectedPanels.includes(panel.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedPanels([...selectedPanels, panel.id]);
                      } else {
                        setSelectedPanels(selectedPanels.filter((id) => id !== panel.id));
                      }
                    }}
                  />
                  <span>{panel.panel_name} - PKR {panel.price}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Discount */}
          <div className={styles.formGroup}>
            <label>Discount (PKR)</label>
            <input
              type="number"
              value={discount}
              onChange={(e) => setDiscount(e.target.value)}
              min="0"
            />
          </div>

          {/* Total */}
          <div className={styles.totalSection}>
            <span>Total Amount:</span>
            <span className={styles.totalAmount}>PKR {calculateTotal().toFixed(2)}</span>
          </div>

          <div className={styles.formActions}>
            <button type="button" onClick={onClose} className={styles.cancelButton}>
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedPatient || (selectedTests.length === 0 && selectedPanels.length === 0) || createMutation.isPending}
              className={styles.submitButton}
            >
              {createMutation.isPending ? 'Creating...' : 'Create Order'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function OrderDetailModal({ order, onClose }: { order: Order; onClose: () => void }) {
  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h2>Order Details</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <div className={styles.orderDetails}>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Order ID:</span>
            <span className={styles.detailValue}>{order.order_id}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Patient:</span>
            <span className={styles.detailValue}>{order.patient_name}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Status:</span>
            <span className={styles.detailValue}>{order.status}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Total:</span>
            <span className={styles.detailValue}>PKR {order.total_amount}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Discount:</span>
            <span className={styles.detailValue}>PKR {order.discount}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Net Amount:</span>
            <span className={styles.detailValue}>PKR {order.net_amount}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Payment Status:</span>
            <span className={styles.detailValue}>{order.is_paid ? 'Paid' : 'Unpaid'}</span>
          </div>

          <h3 className={styles.itemsHeader}>Order Items</h3>
          <div className={styles.itemsList}>
            {order.items.map((item) => (
              <div key={item.id} className={styles.orderItem}>
                <span>{item.test_name || item.panel_name}</span>
                <span>PKR {item.price}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function PaymentModal({ order, onClose, onSuccess }: { order: Order; onClose: () => void; onSuccess: () => void }) {
  const [amount, setAmount] = useState(order.net_amount);
  const [paymentMethod, setPaymentMethod] = useState('cash');

  const createPayment = useMutation({
    mutationFn: () =>
      paymentApi.create({
        order: order.id,
        amount: amount,
        payment_method: paymentMethod as 'cash' | 'card' | 'bank_transfer' | 'mobile_money' | 'insurance',
      }),
    onSuccess,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createPayment.mutate();
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h2>Record Payment</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Order:</span>
            <span className={styles.detailValue}>{order.order_id}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Amount Due:</span>
            <span className={styles.detailValue}>PKR {order.net_amount}</span>
          </div>

          <div className={styles.formGroup}>
            <label>Payment Amount</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
              min="0"
              step="0.01"
            />
          </div>

          <div className={styles.formGroup}>
            <label>Payment Method</label>
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
            >
              <option value="cash">Cash</option>
              <option value="card">Card</option>
              <option value="bank_transfer">Bank Transfer</option>
              <option value="mobile_money">Mobile Money</option>
              <option value="insurance">Insurance</option>
            </select>
          </div>

          <div className={styles.formActions}>
            <button type="button" onClick={onClose} className={styles.cancelButton}>
              Cancel
            </button>
            <button type="submit" disabled={createPayment.isPending} className={styles.submitButton}>
              {createPayment.isPending ? 'Processing...' : 'Record Payment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
