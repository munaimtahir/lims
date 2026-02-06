import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { orderApi, patientApi, systemSettingsApi } from '../../api/services';
import type { Order, Patient, SystemSettings } from '../../types';
import { formatCurrency } from '../../utils/currency';
import { formatDateDDMMYY } from '../../utils/dateFormat';
import {
  getStoredReceiptFormat,
  getStoredThermalCopies,
  setStoredReceiptFormat,
  setStoredThermalCopies,
  type ReceiptPrintFormat,
} from '../../utils/printPreferences';
import styles from './PrintReceiptPage.module.css';

const ReceiptContent = ({
  order,
  patient,
  settings,
  isThermal = false,
  copyLabel = '',
}: {
  order: Order;
  patient: Patient;
  settings?: SystemSettings;
  isThermal?: boolean;
  copyLabel?: string;
}) => {
  const currency = settings?.currency || 'PKR';

  return (
    <div className={styles.receiptContent}>
      <div className={styles.header}>
        {settings?.report_header_image ? (
          <img src={settings.report_header_image} alt="Header Banner" className={styles.wrapper} style={{ width: '100%', maxHeight: '70px', objectFit: 'contain' }} />
        ) : (
          <>
            {settings?.lab_logo && <img src={settings.lab_logo} alt="Lab Logo" className={styles.logo} />}
            <h1 className={styles.labName}>{settings?.lab_display_name || settings?.lab_name || 'LIMS Laboratory'}</h1>
            {settings?.lab_address && <div className={styles.labSub}>{settings.lab_address}</div>}
            {settings?.lab_phone && <div className={styles.labSub}>Tel: {settings.lab_phone}</div>}
          </>
        )}

        <div className={styles.receiptTitle}>CASH RECEIPT {copyLabel && `(${copyLabel})`}</div>
      </div>

      <div className={`${styles.patientInfoGrid} ${isThermal ? styles.thermalInfoGrid : ''}`}>
        <div className={styles.infoRow}><span className={styles.label}>MRN:</span><span className={styles.value}>{patient.patient_id}</span></div>
        <div className={styles.infoRow}><span className={styles.label}>Lab No:</span><span className={styles.value}>{order.order_id}</span></div>
        <div className={styles.infoRow}><span className={styles.label}>Name:</span><span className={`${styles.value} ${styles.wrap}`}>{patient.full_name}</span></div>
        <div className={styles.infoRow}><span className={styles.label}>Date:</span><span className={styles.value}>{formatDateDDMMYY(order.created_at)}</span></div>
        <div className={styles.infoRow}><span className={styles.label}>DOB:</span><span className={styles.value}>{formatDateDDMMYY(patient.date_of_birth) || '-'}</span></div>
        <div className={styles.infoRow}><span className={styles.label}>Age/Sex:</span><span className={styles.value}>{patient.age_years ? `${patient.age_years}Y ` : ''}{patient.gender}</span></div>
        <div className={styles.infoRow}><span className={styles.label}>Contact:</span><span className={styles.value}>{patient.phone}</span></div>
        {order.referred_by && <div className={styles.infoRow}><span className={styles.label}>Ref By:</span><span className={`${styles.value} ${styles.wrap}`}>{order.referred_by}</span></div>}
      </div>

      <table className={styles.testsTable}>
        <thead>
          <tr>
            <th>Test / Service</th>
            {!isThermal && <th>Code</th>}
            <th className={styles.money}>Price</th>
          </tr>
        </thead>
        <tbody>
          {order.items.map((item) => (
            <tr key={item.id}>
              <td className={styles.wrap}>{item.test_name || item.panel_name}</td>
              {!isThermal && <td>{item.test_code || item.panel_code}</td>}
              <td className={styles.money}>{formatCurrency(item.price, currency)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className={styles.financialSection}>
        <div className={styles.financialGrid}>
          <div className={styles.finRow}><span className={styles.finLabel}>Total:</span><span className={styles.finValue}>{formatCurrency(order.total_amount, currency)}</span></div>
          {parseFloat(order.discount) > 0 && <div className={styles.finRow}><span className={styles.finLabel}>Discount:</span><span className={styles.finValue}>-{formatCurrency(order.discount, currency)}</span></div>}
          <div className={styles.finRow}><span className={styles.finLabel}>Net Payable:</span><span className={styles.finValue}>{formatCurrency(order.net_amount || (parseFloat(order.total_amount) - parseFloat(order.discount)).toString(), currency)}</span></div>
          <div className={styles.finRow}><span className={styles.finLabel}>Paid:</span><span className={styles.finValue}>{formatCurrency(order.paid_amount, currency)}</span></div>
          <div className={`${styles.finRow} ${styles.highlightDue}`}><span className={styles.finLabel}>Balance Due:</span><span className={styles.finValue}>{formatCurrency(order.due_amount, currency)}</span></div>
        </div>
      </div>

      <div className={styles.footer}>
        {settings?.report_footer_image ? <img src={settings.report_footer_image} alt="Footer Info" /> : <div>{settings?.report_footer || 'Thank you for choosing us.'}</div>}
      </div>
    </div>
  );
};

export default function PrintReceiptPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const [printMode, setPrintMode] = useState<ReceiptPrintFormat>(() => getStoredReceiptFormat());
  const [thermalCopies, setThermalCopies] = useState<number>(() => getStoredThermalCopies());

  const { data: order, isLoading: loadingOrder, error: orderError } = useQuery({
    queryKey: ['order', orderId],
    queryFn: async () => {
      const numericId = Number(orderId);
      if (!Number.isNaN(numericId)) return orderApi.get(numericId);
      const response = await orderApi.list({ search: orderId });
      const match = response.results.find((o) => o.order_id === orderId) || response.results[0];
      if (!match) throw new Error('Order not found');
      return match;
    },
    enabled: !!orderId,
  });

  const { data: patient, isLoading: loadingPatient } = useQuery({
    queryKey: ['patient', order?.patient],
    queryFn: () => patientApi.get(order!.patient),
    enabled: !!order,
  });

  const { data: settings, isLoading: loadingSettings } = useQuery({
    queryKey: ['systemSettings'],
    queryFn: () => systemSettingsApi.get(),
  });

  const settingsData = useMemo(() => (settings && 'data' in settings ? settings.data : (settings as SystemSettings | undefined)), [settings]);

  const onChangeMode = (mode: ReceiptPrintFormat) => {
    setPrintMode(mode);
    setStoredReceiptFormat(mode);
  };

  const onChangeThermalCopies = (value: number) => {
    setThermalCopies(value);
    setStoredThermalCopies(value);
  };

  const handlePrint = () => {
    window.print();
  };

  if (loadingOrder || loadingPatient || loadingSettings) return <div className="p-8 text-center">Loading receipt data...</div>;
  if (orderError || !order || !patient) return <div className="p-8 text-center text-red-500">Error loading receipt. Order ID: {orderId}</div>;

  return (
    <div className={styles.pageContainer}>
      <div className={`${styles.controls} noDisplayPrint`}>
        <div style={{ fontWeight: '600', marginRight: '1rem' }}>Print Format:</div>
        <button className={`${styles.controlButton} ${printMode === 'A4' ? styles.activeButton : ''}`} onClick={() => onChangeMode('A4')}>A4 (Dual Copy)</button>
        <button className={`${styles.controlButton} ${printMode === 'Thermal' ? styles.activeButton : ''}`} onClick={() => onChangeMode('Thermal')}>Thermal (80mm)</button>
        {printMode === 'Thermal' && (
          <label>
            Copies
            <input type="number" min={1} value={thermalCopies} onChange={(e) => onChangeThermalCopies(Number(e.target.value) || 1)} style={{ width: 60, marginLeft: 8 }} />
          </label>
        )}
        <button className={styles.printButton} onClick={handlePrint}>🖨 Print Receipt</button>
      </div>

      <div className={styles.printArea}>
        {printMode === 'A4' ? (
          <div className={styles.a4Container}>
            <div className={styles.a4Top}><ReceiptContent order={order} patient={patient.data} settings={settingsData} copyLabel="Patient Copy" /></div>
            <div className={styles.separator}><div className={styles.cutLine}></div><div className={styles.cutIcon}>✂ Cut Here</div></div>
            <div className={styles.a4Bottom}><ReceiptContent order={order} patient={patient.data} settings={settingsData} copyLabel="Lab/Office Copy" /></div>
          </div>
        ) : (
          <>
            {Array.from({ length: thermalCopies }).map((_, idx) => (
              <div className={styles.thermalContainer} key={idx}>
                <ReceiptContent order={order} patient={patient.data} settings={settingsData} isThermal copyLabel={idx === 0 ? 'Patient Copy' : 'Lab Copy'} />
              </div>
            ))}
          </>
        )}
      </div>

      <style>{`@media print { .noDisplayPrint { display: none !important; } }`}</style>
    </div>
  );
}
