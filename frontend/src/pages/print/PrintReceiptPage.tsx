import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { orderApi, patientApi, systemSettingsApi } from '../../api/services';
import type { Order, Patient, SystemSettings } from '../../types';
import { formatCurrency } from '../../utils/currency';
import styles from './PrintReceiptPage.module.css';
import { formatDobDisplay } from '../../utils/dateFormat';
import { loadLastReceiptFormat, saveLastReceiptFormat, loadThermalCopies, saveThermalCopies } from '../../utils/printPreferences';

// Receipt Content Component
const ReceiptContent = ({
    order,
    patient,
    settings,
    isThermal = false,
    copyLabel,
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
            {/* Header */}
            {/* Header */}
            <div className={styles.header}>
                {settings?.report_header_image ? (
                    <img src={settings.report_header_image} alt="Header Banner" className={styles.wrapper} style={{ width: '100%', maxHeight: '100px', objectFit: 'contain' }} />
                ) : (
                    <>
                        {settings?.lab_logo && (
                            <img src={settings.lab_logo} alt="Lab Logo" className={styles.logo} />
                        )}
                        <h1 className={styles.labName}>{settings?.lab_display_name || settings?.lab_name || 'LIMS Laboratory'}</h1>
                        {settings?.lab_address && <div className={styles.labSub}>{settings.lab_address}</div>}
                        {settings?.lab_phone && <div className={styles.labSub}>Tel: {settings.lab_phone}</div>}
                    </>
                )}

                <div className={styles.receiptTitle}>
                    CASH RECEIPT {copyLabel && `(${copyLabel})`}
                </div>
            </div>

            {/* Patient & Order Info */}
            <div className={styles.patientInfoGrid}>
                <div className={styles.infoRow}>
                    <span className={styles.label}>MRN:</span>
                    <span className={styles.value}>{patient.patient_id}</span>
                </div>
                <div className={styles.infoRow}>
                    <span className={styles.label}>Lab No:</span>
                    <span className={styles.value}>{order.order_id}</span>
                </div>
                <div className={styles.infoRow}>
                    <span className={styles.label}>Name:</span>
                    <span className={styles.value}>{patient.full_name}</span>
                </div>
                <div className={styles.infoRow}>
                    <span className={styles.label}>Date:</span>
                    <span className={styles.value}>{new Date(order.created_at).toLocaleString()}</span>
                </div>
                <div className={styles.infoRow}>
                    <span className={styles.label}>Age/Sex:</span>
                    <span className={styles.value}>
                        {patient.age_years ? `${patient.age_years}Y ` : ''}
                        {patient.gender}
                    </span>
                </div>
                <div className={styles.infoRow}>
                    <span className={styles.label}>DOB:</span>
                    <span className={styles.value}>{formatDobDisplay(patient.date_of_birth) || 'N/A'}</span>
                </div>
                <div className={styles.infoRow}>
                    <span className={styles.label}>Contact:</span>
                    <span className={styles.value}>{patient.phone}</span>
                </div>
                {order.referred_by && (
                    <div className={styles.infoRow}>
                        <span className={styles.label}>Ref By:</span>
                        <span className={styles.value}>{order.referred_by}</span>
                    </div>
                )}
            </div>

            {/* Test Items */}
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
                            <td>
                                <div>{item.test_name || item.panel_name}</div>
                            </td>
                            {!isThermal && <td>{item.test_code || item.panel_code}</td>}
                            <td className={styles.money}>{formatCurrency(item.price, currency)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {/* Financials */}
            <div className={styles.financialSection}>
                <div className={styles.financialGrid}>
                    <div className={styles.finRow}>
                        <span className={styles.finLabel}>Total:</span>
                        <span className={styles.finValue}>{formatCurrency(order.total_amount, currency)}</span>
                    </div>

                    {parseFloat(order.discount) > 0 && (
                        <div className={styles.finRow}>
                            <span className={styles.finLabel}>Discount:</span>
                            <span className={styles.finValue}>-{formatCurrency(order.discount, currency)}</span>
                        </div>
                    )}

                    <div className={styles.finRow}>
                        <span className={styles.finLabel}>Net Payable:</span>
                        <span className={styles.finValue}>{formatCurrency(order.net_amount || (parseFloat(order.total_amount) - parseFloat(order.discount)).toString(), currency)}</span>
                    </div>

                    <div className={styles.finRow}>
                        <span className={styles.finLabel}>Paid:</span>
                        <span className={styles.finValue}>{formatCurrency(order.paid_amount, currency)}</span>
                    </div>

                    <div className={`${styles.finRow} ${styles.highlightDue}`}>
                        <span className={styles.finLabel}>Balance Due:</span>
                        <span className={styles.finValue}>{formatCurrency(order.due_amount, currency)}</span>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className={styles.footer}>
                {settings?.report_footer_image ? (
                    <img src={settings.report_footer_image} alt="Footer Info" />
                ) : (
                    <div>{settings?.report_footer || 'Thank you for choosing us.'}</div>
                )}
                <div style={{ marginTop: '5px', fontSize: '0.7em' }}>
                    Printed by: {settings?.lab_display_name || 'System'} | {new Date().toLocaleString()}
                </div>
            </div>
        </div>
    );
};

export default function PrintReceiptPage() {
    const { orderId } = useParams<{ orderId: string }>();
    const [printMode, setPrintMode] = useState<'A4' | 'Thermal'>(() => loadLastReceiptFormat());
    const [thermalCopies, setThermalCopies] = useState<number>(() => loadThermalCopies());

    // Fetch Order
    const { data: order, isLoading: loadingOrder, error: orderError } = useQuery({
        queryKey: ['order', orderId],
        queryFn: async () => {
            const numericId = Number(orderId);
            if (!isNaN(numericId)) {
                return orderApi.get(numericId);
            }
            // If ID is not numeric (e.g., ORD-2026...), search for it
            const response = await orderApi.list({ search: orderId });
            // Find exact match or use the first result
            const match = response.results.find(o => o.order_id === orderId) || response.results[0];
            if (!match) throw new Error("Order not found");
            return match;
        },
        enabled: !!orderId,
    });

    // Fetch Patient (after order is loaded)
    const { data: patient, isLoading: loadingPatient } = useQuery({
        queryKey: ['patient', order?.patient],
        queryFn: () => patientApi.get(order!.patient),
        enabled: !!order,
    });

    // Fetch Settings
    const { data: settings, isLoading: loadingSettings } = useQuery({
        queryKey: ['systemSettings'],
        queryFn: () => systemSettingsApi.get(),
    });

    // Apply body class for print mode targeting
    useEffect(() => {
        const className = printMode === 'A4' ? 'a4-print' : 'thermal-print';
        document.body.classList.add(className);
        return () => {
            document.body.classList.remove(className);
        };
    }, [printMode]);

    const handlePrint = () => {
        // Ensure body class is set before printing
        const className = printMode === 'A4' ? 'a4-print' : 'thermal-print';
        document.body.classList.add(className);

        // Small delay to ensure styles are applied
        setTimeout(() => {
            window.print();
        }, 100);
    };

    const changePrintMode = (mode: 'A4' | 'Thermal') => {
        // Remove old class, add new class
        document.body.classList.remove('a4-print', 'thermal-print');
        const className = mode === 'A4' ? 'a4-print' : 'thermal-print';
        document.body.classList.add(className);

        setPrintMode(mode);
        saveLastReceiptFormat(mode);
        if (mode === 'Thermal' && (!thermalCopies || thermalCopies < 1)) {
            setThermalCopies(2);
            saveThermalCopies(2);
        }
    };

    const handleThermalCopiesChange = (value: string) => {
        const num = Math.max(1, parseInt(value, 10) || 1);
        setThermalCopies(num);
        saveThermalCopies(num);
    };

    if (loadingOrder || loadingPatient || loadingSettings) {
        return <div className="p-8 text-center">Loading receipt data...</div>;
    }

    if (orderError || !order || !patient) {
        return <div className="p-8 text-center text-red-500">Error loading receipt. Order ID: {orderId}</div>;
    }

    const settingsData = settings && 'data' in settings ? settings.data : settings as SystemSettings | undefined;

    return (
        <div className={styles.pageContainer}>
            {/* Controls - Hidden during print */}
            <div className={`${styles.controls} noDisplayPrint`}>
                <div style={{ fontWeight: '600', marginRight: '1rem' }}>Print Format:</div>
                <button
                    className={`${styles.controlButton} ${printMode === 'A4' ? styles.activeButton : ''}`}
                    onClick={() => changePrintMode('A4')}
                >
                    A4 (Dual Copy)
                </button>
                <button
                    className={`${styles.controlButton} ${printMode === 'Thermal' ? styles.activeButton : ''}`}
                    onClick={() => changePrintMode('Thermal')}
                >
                    Thermal (80mm)
                </button>

                {printMode === 'Thermal' && (
                    <div className={styles.copiesInput}>
                        <label htmlFor="thermal-copies">Copies:</label>
                        <input
                            id="thermal-copies"
                            type="number"
                            min={1}
                            max={10}
                            value={thermalCopies}
                            onChange={(e) => handleThermalCopiesChange(e.target.value)}
                            aria-label="Number of thermal receipt copies"
                        />
                        <span className={styles.copiesHint}>(default 2)</span>
                    </div>
                )}

                <button className={styles.printButton} onClick={handlePrint}>
                    🖨 Print Receipt
                </button>
            </div>

            {/* Print View Area */}
            <div className={styles.printArea}>
                {printMode === 'A4' ? (
                    <div className={styles.a4Container}>
                        <div className={styles.a4Top}>
                            <ReceiptContent
                                order={order}
                                patient={patient.data}
                                settings={settingsData}
                                copyLabel="Patient Copy"
                            />
                        </div>

                        <div className={styles.separator}>
                            <div className={styles.cutLine}></div>
                            <div className={styles.cutIcon}>✂ Cut Here</div>
                        </div>

                        <div className={styles.a4Bottom}>
                            <ReceiptContent
                                order={order}
                                patient={patient.data}
                                settings={settingsData}
                                copyLabel="Lab/Office Copy"
                            />
                        </div>
                    </div>
                ) : (
                    <div className={styles.thermalContainer}>
                        {Array.from({ length: thermalCopies || 1 }).map((_, idx) => (
                            <div key={idx} className={styles.thermalCopy}>
                                <ReceiptContent
                                    order={order}
                                    patient={patient.data}
                                    settings={settingsData}
                                    isThermal={true}
                                    copyLabel={thermalCopies > 1 ? `Copy ${idx + 1}` : undefined}
                                />
                                {idx < (thermalCopies || 1) - 1 && <div className={styles.thermalDivider} />}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Print-visible style helper to hide controls */}
            <style>{`
        @media print {
          .noDisplayPrint { display: none !important; }
        }
      `}</style>
        </div>
    );
}
