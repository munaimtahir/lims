import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { analyticsApi } from '../../api/services';
import type { ReferralRows } from './types';
import { AnalyticsFilterBar } from './AnalyticsFilterBar';
import styles from './AnalyticsPage.module.css';

export default function AnalyticsReferralsPage() {
    const [searchParams] = useSearchParams();
    const [tab, setTab] = useState<'volume' | 'revenue'>('volume');

    const queryParams = {
        start_date: searchParams.get('start_date') || new Date().toISOString().split('T')[0],
        end_date: searchParams.get('end_date') || new Date().toISOString().split('T')[0],
        include_cancelled: searchParams.get('include_cancelled') === 'true',
    };

    const { data: reportData, isLoading, error } = useQuery({
        queryKey: ['analytics-referrals', queryParams],
        queryFn: () => analyticsApi.referrals(queryParams),
    });

    const handleExport = async (format: 'csv' | 'xlsx') => {
        try {
            const blob = await analyticsApi.exportReport('referrals', format, queryParams);
            const url = window.URL.createObjectURL(blob as Blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `Referrals_${new Date().toISOString()}.${format}`;
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

    const rowsByTab = (reportData?.rows || { volume: [], revenue: [] }) as ReferralRows;
    const rows = tab === 'volume' ? rowsByTab.volume : rowsByTab.revenue;
    const summary = reportData?.summary || {};

    return (
        <div className={styles.pageContainer}>
            <div className={styles.header}>
                <h1>Referral Analytics</h1>
                <p>Referral sources by volume and revenue</p>
            </div>

            <AnalyticsFilterBar onExport={handleExport} currentReportKey="referrals" />

            <div className={styles.grid} style={{ marginBottom: '24px' }}>
                <div className={styles.card}>
                    <div className={styles.cardTitle}>Total Sources</div>
                    <div className={styles.cardValue}>{summary.total_referrers}</div>
                </div>
            </div>

            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <button
                    className={styles.applyButton}
                    onClick={() => setTab('volume')}
                    disabled={tab === 'volume'}
                >
                    Volume
                </button>
                <button
                    className={styles.applyButton}
                    onClick={() => setTab('revenue')}
                    disabled={tab === 'revenue'}
                >
                    Revenue
                </button>
            </div>

            <div className={styles.tableContainer}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th>Referrer</th>
                            <th>Patients Referred</th>
                            <th>Revenue Generated</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.length === 0 ? (
                            <tr><td colSpan={3} style={{ textAlign: 'center' }}>No data found</td></tr>
                        ) : (
                            rows.map((row) => (
                                <tr key={row.referrer}>
                                    <td>{row.referrer}</td>
                                    <td>{row.count}</td>
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
