import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { analyticsApi } from '../../api/services';
import type { OverviewData } from './types';
import { AnalyticsFilterBar } from './AnalyticsFilterBar';
import styles from './AnalyticsPage.module.css';

export default function AnalyticsOverviewPage() {
    const [searchParams] = useSearchParams();

    // Default to 'today' if not present
    const defaultStart = new Date().toISOString().split('T')[0];
    const defaultEnd = defaultStart;

    const queryParams = {
        start_date: searchParams.get('start_date') || defaultStart,
        end_date: searchParams.get('end_date') || defaultEnd,
        include_cancelled: searchParams.get('include_cancelled') === 'true',
    };

    const { data, isLoading, error } = useQuery<OverviewData>({
        queryKey: ['analytics-overview', queryParams],
        queryFn: () => analyticsApi.overview(queryParams),
    });

    const handleExport = async (format: 'csv' | 'xlsx') => {
        try {
            const blob = await analyticsApi.exportReport('overview', format, queryParams);
            const url = window.URL.createObjectURL(blob as Blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `Overview_${new Date().toISOString()}.${format}`;
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error('Export failed', err);
            alert('Export failed');
        }
    };

    if (isLoading) return <div className={styles.pageContainer}>Loading analytics...</div>;
    if (error) return <div className={styles.pageContainer}>Error loading analytics.</div>;

    const summary = data?.summary;

    return (
        <div className={styles.pageContainer}>
            <div className={styles.header}>
                <h1>Analytics Overview</h1>
                <p>Operational and financial snapshot for {queryParams.start_date} to {queryParams.end_date}</p>
            </div>

            <AnalyticsFilterBar onExport={handleExport} currentReportKey="overview" />

            {summary && (
                <div className={styles.grid}>
                    {/* Operational Cards */}
                    <div className={styles.card}>
                        <div className={styles.cardTitle}>Patients Seen</div>
                        <div className={styles.cardValue}>{summary.patients_seen}</div>
                        <div className={styles.cardSub}>Unique patients</div>
                    </div>
                    <div className={styles.card}>
                        <div className={styles.cardTitle}>Total Orders</div>
                        <div className={styles.cardValue}>{summary.total_orders}</div>
                        <div className={styles.cardSub}>Visits</div>
                    </div>
                    <div className={styles.card}>
                        <div className={styles.cardTitle}>Tests Billed</div>
                        <div className={styles.cardValue}>{summary.total_tests}</div>
                        <div className={styles.cardSub}>Individual line items</div>
                    </div>

                    {/* Financial Cards */}
                    <div className={`${styles.card} ${styles.highlight}`}>
                        <div className={styles.cardTitle}>Net Sales</div>
                        <div className={styles.cardValue}>
                            {summary.net_sales.toLocaleString('en-PK', { style: 'currency', currency: 'PKR' })}
                        </div>
                        <div className={styles.cardSub}>
                            Gross: {summary.gross_sales.toLocaleString()} | Disc: {summary.total_discount.toLocaleString()}
                        </div>
                    </div>

                    <div className={`${styles.card} ${styles.success}`}>
                        <div className={styles.cardTitle}>Cash Collected</div>
                        <div className={styles.cardValue}>
                            {summary.total_collections.toLocaleString('en-PK', { style: 'currency', currency: 'PKR' })}
                        </div>
                        <div className={styles.cardSub}>
                            Cash Only: {summary.cash_collections.toLocaleString()}
                        </div>
                    </div>

                    <div className={styles.card}>
                        <div className={styles.cardTitle}>Total Outstanding</div>
                        <div className={styles.cardValue}>
                            {/* Using the "outstanding for selected orders" logic which is safer for context */}
                            {summary.outstanding_for_orders.toLocaleString('en-PK', { style: 'currency', currency: 'PKR' })}
                        </div>
                        <div className={styles.cardSub}>
                            For orders in this period
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
