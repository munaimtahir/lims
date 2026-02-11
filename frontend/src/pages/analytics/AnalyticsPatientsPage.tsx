import { } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { analyticsApi } from '../../api/services';
import type { PatientRow } from './types';
import { AnalyticsFilterBar } from './AnalyticsFilterBar';
import styles from './AnalyticsPage.module.css';

export default function AnalyticsPatientsPage() {
    const [searchParams] = useSearchParams();

    const queryParams = {
        start_date: searchParams.get('start_date') || new Date().toISOString().split('T')[0],
        end_date: searchParams.get('end_date') || new Date().toISOString().split('T')[0],
        include_cancelled: searchParams.get('include_cancelled') === 'true',
    };

    const { data: reportData, isLoading, error } = useQuery({
        queryKey: ['analytics-patients', queryParams],
        queryFn: () => analyticsApi.patients(queryParams),
    });

    const handleExport = async (format: 'csv' | 'xlsx') => {
        try {
            const blob = await analyticsApi.exportReport('patients', format, queryParams);
            const url = window.URL.createObjectURL(blob as Blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `Patients_${new Date().toISOString()}.${format}`;
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error('Export failed', err);
            alert('Export failed');
        }
    };

    if (isLoading) return <div className={styles.pageContainer}>Loading...</div>;
    if (error) return <div className={styles.pageContainer}>Error loading report</div>;

    const rows = (reportData?.rows || []) as PatientRow[];
    const summary = reportData?.summary || {};

    return (
        <div className={styles.pageContainer}>
            <div className={styles.header}>
                <h1>Patient Analytics</h1>
                <p>Patient activity and contribution analysis</p>
            </div>

            <AnalyticsFilterBar onExport={handleExport}  />

            {/* Summary Cards */}
            <div className={styles.grid} style={{ marginBottom: '24px' }}>
                <div className={styles.card}>
                    <div className={styles.cardTitle}>Total Patients</div>
                    <div className={styles.cardValue}>{summary.total_patients}</div>
                </div>
            </div>

            <div className={styles.tableContainer}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th>Patient ID</th>
                            <th>Name</th>
                            <th>Age/Gender</th>
                            <th>Visits</th>
                            <th>Revenue Contrib.</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.length === 0 ? (
                            <tr><td colSpan={5} style={{ textAlign: 'center' }}>No data found</td></tr>
                        ) : (
                            rows.map((row) => (
                                <tr key={row.patient_id}>
                                    <td>{row.patient_id}</td>
                                    <td>{row.name}</td>
                                    <td>{row.age} / {row.gender}</td>
                                    <td>{row.orders_count}</td>
                                    <td className={styles.currency}>{row.revenue.toLocaleString()}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
