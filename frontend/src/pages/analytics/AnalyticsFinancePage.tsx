import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { analyticsApi } from '../../api/services';
import type { CollectionRow } from './types';
import { AnalyticsFilterBar } from './AnalyticsFilterBar';
import styles from './AnalyticsPage.module.css';

export default function AnalyticsFinancePage() {
    const [searchParams] = useSearchParams();

    const queryParams = {
        start_date: searchParams.get('start_date') || new Date().toISOString().split('T')[0],
        end_date: searchParams.get('end_date') || new Date().toISOString().split('T')[0],
        include_cancelled: searchParams.get('include_cancelled') === 'true',
    };

    const { data: reportData, isLoading, error } = useQuery({
        queryKey: ['analytics-finance', queryParams],
        queryFn: () => analyticsApi.finance(queryParams),
    });

    const handleExport = async (format: 'csv' | 'xlsx') => {
        try {
            const blob = await analyticsApi.exportReport('finance', format, queryParams);
            const url = window.URL.createObjectURL(blob as Blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `Finance_${new Date().toISOString()}.${format}`;
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

    const rows = (reportData?.collections_by_method || []) as CollectionRow[];
    const summary = reportData?.summary || {};

    return (
        <div className={styles.pageContainer}>
            <div className={styles.header}>
                <h1>Financial Analytics</h1>
                <p>Sales, discounts, and collections breakdown</p>
            </div>

            <AnalyticsFilterBar onExport={handleExport} currentReportKey="finance" />

            <div className={styles.grid}>
                <div className={`${styles.card} ${styles.highlight}`}>
                    <div className={styles.cardTitle}>Gross Sales</div>
                    <div className={styles.cardValue}>
                        {(summary.gross_sales || 0).toLocaleString('en-PK', { style: 'currency', currency: 'PKR' })}
                    </div>
                </div>
                <div className={styles.card}>
                    <div className={styles.cardTitle}>Total Discounts</div>
                    <div className={styles.cardValue}>
                        {(summary.discount || 0).toLocaleString('en-PK', { style: 'currency', currency: 'PKR' })}
                    </div>
                </div>
                <div className={`${styles.card} ${styles.success}`}>
                    <div className={styles.cardTitle}>Net Sales</div>
                    <div className={styles.cardValue}>
                        {(summary.net_sales || 0).toLocaleString('en-PK', { style: 'currency', currency: 'PKR' })}
                    </div>
                </div>
                <div className={styles.card}>
                    <div className={styles.cardTitle}>Total Collected</div>
                    <div className={styles.cardValue}>
                        {(summary.total_collected || 0).toLocaleString('en-PK', { style: 'currency', currency: 'PKR' })}
                    </div>
                </div>
            </div>

            <h2 className={styles.sectionTitle}>Collections by Payment Method</h2>
            <div className={styles.tableContainer}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th>Payment Method</th>
                            <th>Amount Collected</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.length === 0 ? (
                            <tr><td colSpan={2} style={{ textAlign: 'center' }}>No data found</td></tr>
                        ) : (
                            rows.map((row) => (
                                <tr key={row.method}>
                                    <td style={{ textTransform: 'capitalize' }}>{row.method.replace('_', ' ')}</td>
                                    <td className={styles.currency}>{row.amount.toLocaleString()}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
