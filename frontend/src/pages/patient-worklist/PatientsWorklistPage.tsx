import { useMemo, useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { worklistApi } from '../../api/services';
import type { WorklistPatient } from '../../types';
import styles from './PatientsWorklistPage.module.css';
import { formatDateDDMMYY } from '../../utils/dateFormat';
import { useAuth } from '../../contexts';

export default function PatientsWorklistPage() {
  const { user } = useAuth();
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [status, setStatus] = useState('');
  const [printState, setPrintState] = useState<{ type: 'receipt' | 'report'; orderId: number } | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const toastTimer = useRef<number | null>(null);

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    if (toastTimer.current) {
      window.clearTimeout(toastTimer.current);
    }
    toastTimer.current = window.setTimeout(() => setToast(null), 3000);
  };

  const params = useMemo(() => ({
    search: search || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    status: status || undefined,
  }), [search, dateFrom, dateTo, status]);

  const { data, isLoading } = useQuery({
    queryKey: ['patients-worklist', params],
    queryFn: () => worklistApi.listPatients(params),
  });

  const patients = data?.results || [];

  const applyQuickFilter = (days: number) => {
    const today = new Date();
    const fromDate = new Date(today);
    fromDate.setDate(today.getDate() - days + 1);
    setDateFrom(fromDate.toISOString().slice(0, 10));
    setDateTo(today.toISOString().slice(0, 10));
  };

  const openNewTab = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const canPrintByRole = user?.role === 'Admin'
    || user?.role === 'Receptionist'
    || user?.role === 'Cashier'
    || user?.role === 'Manager';

  const resolvePrintUrl = (target: string, fallbackPath: string) => {
    if (target.startsWith('http') || target.startsWith('/')) {
      return target;
    }
    return `${fallbackPath}/${target}`;
  };

  const handlePrintReceipt = (patient: WorklistPatient) => {
    const orderId = patient.latest_order_id;
    const target =
      patient.receipt_pdf_url ||
      patient.receipt_url ||
      String(orderId || '') ||
      patient.latest_order_number ||
      '';
    const canPrint = canPrintByRole && (patient.can_reprint_receipt ?? true) && Boolean(target);

    if (!canPrint || !target) {
      showToast('error', canPrintByRole ? 'Receipt not available for this order.' : 'You do not have permission to print receipts.');
      return;
    }

    setPrintState({ type: 'receipt', orderId: patient.latest_order_id });
    const url = orderId ? `/print/receipt/${orderId}` : resolvePrintUrl(target, '/print/receipt');

    openNewTab(url);
    showToast('success', 'Opening receipt...');
    setTimeout(() => setPrintState(null), 300);
  };

  const handlePrintReport = (patient: WorklistPatient) => {
    const target =
      patient.report_pdf_url ||
      patient.report_url ||
      '';
    const canPrint = canPrintByRole && (patient.can_reprint_report ?? true) && Boolean(target);

    if (!canPrint || !target) {
      showToast('error', canPrintByRole ? 'Report not available or not yet published.' : 'You do not have permission to print reports.');
      return;
    }

    setPrintState({ type: 'report', orderId: patient.latest_order_id });
    const url = resolvePrintUrl(target, '/print/report');
    openNewTab(url);
    showToast('success', 'Opening report...');
    setTimeout(() => setPrintState(null), 300);
  };

  return (
    <div className={styles.container}>
      {toast && (
        <div className={`${styles.toast} ${toast.type === 'success' ? styles.toastSuccess : styles.toastError}`}>
          {toast.message}
        </div>
      )}
      <div className={styles.header}>
        <div>
          <h1>Patients Worklist</h1>
          <p>Track current workflow status and reprint receipts/reports.</p>
        </div>
      </div>

      <div className={styles.filters}>
        <input
          type="text"
          placeholder="Search by name, mobile, or order number"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={styles.searchInput}
        />
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="registered">Registered / Order Created</option>
          <option value="paid">Paid</option>
          <option value="COLLECTED">Sample Collected</option>
          <option value="IN_PROCESS">In Testing / Result Pending</option>
          <option value="VERIFIED">Report Ready / Verified</option>
          <option value="PUBLISHED">Report Published</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
        <button type="button" onClick={() => applyQuickFilter(1)} className={styles.quickButton}>
          Today
        </button>
        <button type="button" onClick={() => applyQuickFilter(7)} className={styles.quickButton}>
          Last 7 Days
        </button>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading worklist...</div>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Patient</th>
              <th>Mobile</th>
              <th>Lab No</th>
              <th>Status</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((item: WorklistPatient) => {
              const receiptTarget =
                item.receipt_pdf_url ||
                item.receipt_url ||
                String(item.latest_order_id || '') ||
                item.latest_order_number ||
                '';
              const reportTarget = item.report_pdf_url || item.report_url || '';
              const canPrintReceipt = canPrintByRole && (item.can_reprint_receipt ?? true) && Boolean(receiptTarget);
              const canPrintReport = canPrintByRole && (item.can_reprint_report ?? true) && Boolean(reportTarget);
              return (
                <tr key={item.latest_order_id}>
                  <td>
                    <div className={styles.patientCell}>
                      <span className={styles.patientName}>{item.patient_name}</span>
                      <span className={styles.patientMeta}>{item.gender} {item.patient_mrn ? `| MRN: ${item.patient_mrn}` : ''}</span>
                    </div>
                  </td>
                  <td>{item.mobile}</td>
                  <td>
                    <div className={styles.labNoCell}>
                      <span className={styles.labNo}>{item.lab_number || item.latest_order_number}</span>
                    </div>
                  </td>
                  <td>
                    <span className={styles.statusBadge}>{item.current_status}</span>
                  </td>
                  <td>{formatDateDDMMYY(item.latest_order_created_at)}</td>
                  <td>
                    <div className={styles.actionButtons}>
                      <button
                        type="button"
                        className={`${styles.actionButton} ${!canPrintReceipt ? styles.actionButtonDisabled : ''}`}
                        disabled={!canPrintByRole || (printState?.type === 'receipt' && printState.orderId === item.latest_order_id)}
                        aria-disabled={!canPrintReceipt}
                        data-testid="print-receipt"
                        data-available={canPrintReceipt ? 'true' : 'false'}
                        onClick={() => handlePrintReceipt(item)}
                      >
                        {(printState?.type === 'receipt' && printState.orderId === item.latest_order_id) ? 'Opening...' : 'Print Receipt'}
                      </button>
                      <button
                        type="button"
                        className={`${styles.actionButton} ${!canPrintReport ? styles.actionButtonDisabled : ''}`}
                        disabled={!canPrintByRole || (printState?.type === 'report' && printState.orderId === item.latest_order_id)}
                        aria-disabled={!canPrintReport}
                        data-testid="print-report"
                        data-available={canPrintReport ? 'true' : 'false'}
                        onClick={() => handlePrintReport(item)}
                      >
                        {(printState?.type === 'report' && printState.orderId === item.latest_order_id) ? 'Opening...' : 'Print Report'}
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {patients.length === 0 && (
              <tr>
                <td colSpan={6} className={styles.noData}>No patients found</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
