import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { worklistApi } from '../../api/services';
import type { WorklistPatient } from '../../types';
import styles from './PatientsWorklistPage.module.css';

export default function PatientsWorklistPage() {
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [status, setStatus] = useState('');

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

  const handlePrintReceipt = (orderNumber?: string, fallbackUrl?: string) => {
    if (orderNumber) {
      window.open(`/print/receipt/${orderNumber}`, '_blank', 'noopener,noreferrer');
      return;
    }
    if (fallbackUrl) {
      window.open(fallbackUrl, '_blank', 'noopener,noreferrer');
    }
  };

  const handlePrintReport = (url?: string) => {
    if (!url) return;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className={styles.container}>
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
              <th>Order</th>
              <th>Status</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((item: WorklistPatient) => (
              <tr key={item.latest_order_id}>
                <td>
                  <div className={styles.patientCell}>
                    <span className={styles.patientName}>{item.patient_name}</span>
                    <span className={styles.patientMeta}>{item.gender}</span>
                  </div>
                </td>
                <td>{item.mobile}</td>
                <td>{item.latest_order_number}</td>
                <td>
                  <span className={styles.statusBadge}>{item.current_status}</span>
                </td>
                <td>{new Date(item.latest_order_created_at).toLocaleDateString()}</td>
                <td>
                  <div className={styles.actionButtons}>
                    <button
                      type="button"
                      className={styles.actionButton}
                      disabled={!item.can_reprint_receipt}
                      onClick={() => handlePrintReceipt(item.latest_order_number || String(item.latest_order_id), item.receipt_pdf_url)}
                    >
                      Print Receipt
                    </button>
                    <button
                      type="button"
                      className={styles.actionButton}
                      disabled={!item.can_reprint_report}
                      onClick={() => handlePrintReport(item.report_pdf_url)}
                    >
                      Print Report
                    </button>
                  </div>
                </td>
              </tr>
            ))}
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
