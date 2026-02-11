import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { analyticsApi } from '../../api/services';
import type { TestRow } from './types';
import { AnalyticsFilterBar } from './AnalyticsFilterBar';
import styles from './AnalyticsPage.module.css';

export default function AnalyticsTestsPage() {
    const [searchParams] = useSearchParams();

    const queryParams = {
        start_date: searchParams.get('start_date') || new Date().toISOString().split('T')[0],
        end_date: searchParams.get('end_date') || new Date().toISOString().split('T')[0],
        include_cancelled: searchParams.get('include_cancelled') === 'true',
    };

    const { data: reportData, isLoading, error } = useQuery({
        queryKey: ['analytics-tests', queryParams],
        queryFn: () => analyticsApi.tests(queryParams),
    });

    const handleExport = async (format: 'csv' | 'xlsx') => {
        try {
            const blob = await analyticsApi.exportReport('tests', format, queryParams);
            const url = window.URL.createObjectURL(blob as Blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `Tests_${new Date().toISOString()}.${format}`;
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

    const rows = (reportData?.rows || []) as TestRow[];
    const summary = reportData?.summary || {};

    return (
        <div className={styles.pageContainer}>
            <div className={styles.header}>
                <h1>Test Analytics</h1>
                <p>Most ordered tests and revenue share</p>
            </div>

            <AnalyticsFilterBar onExport={handleExport} currentReportKey="tests" />

            <div className={styles.grid} style={{ marginBottom: '24px' }}>
                <div className={styles.card}>
                    <div className={styles.cardTitle}>Total Tests Billed</div>
                    <div className={styles.cardValue}>{summary.total_tests_billed}</div>
                </div>
            </div>

            <div className={styles.tableContainer}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th>Test Name</th>
                            <th>Count</th>
                            <th>Revenue</th>
                            <th>Share (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.length === 0 ? (
                            <tr><td colSpan={4} style={{ textAlign: 'center' }}>No data found</td></tr>
                        ) : (
                            rows.map((row) => (
                                <tr key={row.test_name}>
                                    <td>{row.test_name}</td>
                                    <td>{row.count}</td>
                                    <td className={styles.currency}>{row.revenue.toLocaleString()}</td>
                                    <td>{row.share_percent}%</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
