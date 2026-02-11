import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { reportApi } from '../../api/services';
import apiClient from '../../api/client';
import type { Report } from '../../types';
import styles from './ReportsPage.module.css';

export default function ReportsPage() {
    const [retryCount, setRetryCount] = useState(0);
    const [showTimeoutError, setShowTimeoutError] = useState(false);
    const [activeTab, setActiveTab] = useState<'reports' | 'audit'>('reports');
    const [auditReportId, setAuditReportId] = useState<number | null>(null);

    const {
        data: reportsData,
        isLoading,
        isError,
        error,
        refetch
    } = useQuery({
        queryKey: ['reports', retryCount],
        queryFn: () => reportApi.list(),
        retry: 2,
        retryDelay: 1000,
    });

    // Timeout detection
    useEffect(() => {
        let timer: number;
        if (isLoading) {
            setShowTimeoutError(false);
            timer = window.setTimeout(() => setShowTimeoutError(true), 15000); // 15s timeout
        } else {
            setShowTimeoutError(false);
        }
        return () => clearTimeout(timer);
    }, [isLoading, retryCount]);

    const handleRetry = () => {
        setRetryCount(prev => prev + 1);
        setShowTimeoutError(false);
        // data will be refetched because retryCount changes queryKey
    };

    // Loading state with timeout check
    if (isLoading) {
        if (showTimeoutError) {
            return (
                <div className={styles.container}>
                    <div className={styles.errorContainer}>
                        <div className={styles.errorIcon}>⚠️</div>
                        <h2>Loading Timeout</h2>
                        <p className={styles.errorMessage}>The reports are taking too long to load.</p>
                        <div className={styles.errorActions}>
                            <button className={styles.retryButton} onClick={handleRetry}>
                                Retry
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return (
            <div className={styles.container}>
                <div className={styles.loadingContainer}>
                    <div className={styles.spinner}></div>
                    <p>Loading reports...</p>
                    <p className={styles.loadingHint}>This may take a few moments</p>
                </div>
            </div>
        );
    }

    // Error state with retry
    if (isError) {
        const errorMessage = (error as Error)?.message || 'Failed to load reports';
        return (
            <div className={styles.container}>
                <div className={styles.errorContainer}>
                    <div className={styles.errorIcon}>❌</div>
                    <h2>Failed to Load Reports</h2>
                    <p className={styles.errorMessage}>{errorMessage}</p>
                    <div className={styles.errorActions}>
                        <button className={styles.retryButton} onClick={handleRetry}>
                            Retry
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    const reportResults = reportsData?.results;
    // Safeguard against undefined results
    const reports = Array.isArray(reportResults) ? reportResults : [];

    const { data: auditEvents, isLoading: isAuditLoading } = useQuery({
        queryKey: ['report-audit', auditReportId],
        queryFn: async () => {
            if (!auditReportId) return [];
            const response = await apiClient.get<{ results: Array<{ id: number; created_at?: string; actor_name?: string; action: string; before?: unknown; after?: unknown; }> }>('/audit/', {
                params: { entity_type: 'report', entity_id: auditReportId }
            });
            return response.data.results || [];
        },
        enabled: activeTab === 'audit' && !!auditReportId,
    });

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1>Reports</h1>
                <p className={styles.subtitle}>Generated laboratory reports</p>
                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                    <button className={styles.retryButton} onClick={() => setActiveTab('reports')}>Reports</button>
                    <button className={styles.retryButton} onClick={() => setActiveTab('audit')}>Audit</button>
                </div>
            </div>

            {activeTab === 'audit' ? (
                <div className={styles.reportsList}>
                    {!auditReportId && <p>Select a report to view audit.</p>}
                    {isAuditLoading ? <p>Loading audit...</p> : (
                        (auditEvents || []).map((event) => (
                            <div key={event.id} className={styles.reportCard}>
                                <div className={styles.reportHeader}>
                                    <div className={styles.reportInfo}>
                                        <h3>{event.action}</h3>
                                        <span className={styles.orderId}>
                                            {(event.actor_name || 'System')} • {event.created_at ? new Date(event.created_at).toLocaleString() : ''}
                                        </span>
                                    </div>
                                </div>
                                <div className={styles.reportDetails}>
                                    <pre className={styles.noFile}>{JSON.stringify(event.before || {}, null, 2)}</pre>
                                    <pre className={styles.noFile}>{JSON.stringify(event.after || {}, null, 2)}</pre>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            ) : reports.length === 0 ? (
                <div className={styles.emptyState}>
                    <p>📄 No reports generated yet</p>
                    {/* Add a manual refresh here just in case */}
                    <button className={styles.retryButton} onClick={() => refetch()} style={{ marginTop: '10px', fontSize: '0.9em' }}>
                        Refresh List
                    </button>
                </div>
            ) : (
                <div className={styles.reportsList}>
                    {reports.map((report: Report) => (
                        <div key={report.id || Math.random()} className={styles.reportCard}>
                            <div className={styles.reportHeader}>
                                <div className={styles.reportInfo}>
                                    <h3>Report #{report.id}</h3>
                                    <span className={styles.orderId}>Order: {report.order_id_display || report.order || 'N/A'}</span>
                                </div>
                                <span className={`${styles.statusBadge} ${report.is_final ? styles.final : styles.draft}`}>
                                    {report.is_final ? 'Final' : 'Draft'}
                                </span>
                            </div>

                            <div className={styles.reportDetails}>
                                <div className={styles.detailRow}>
                                    <span className={styles.label}>Generated:</span>
                                    <span className={styles.value}>
                                        {report.generated_at ? new Date(report.generated_at).toLocaleString() : 'Date Unknown'}
                                    </span>
                                </div>
                                {report.generated_by_name && (
                                    <div className={styles.detailRow}>
                                        <span className={styles.label}>Generated by:</span>
                                        <span className={styles.value}>{report.generated_by_name}</span>
                                    </div>
                                )}
                                {report.verified_by_name && (
                                    <div className={styles.detailRow}>
                                        <span className={styles.label}>Verified by:</span>
                                        <span className={styles.value}>{report.verified_by_name}</span>
                                    </div>
                                )}
                            </div>

                            <div className={styles.reportActions}>
                                {report.report_file ? (
                                    <a
                                        href={report.report_file}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className={styles.downloadButton}
                                    >
                                        📥 Download
                                    </a>
                                ) : (
                                    <span className={styles.noFile}>No File</span>
                                )}
                                <button
                                    className={styles.downloadButton}
                                    onClick={() => {
                                        setAuditReportId(report.id || null);
                                        setActiveTab('audit');
                                    }}
                                >
                                    Audit
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
