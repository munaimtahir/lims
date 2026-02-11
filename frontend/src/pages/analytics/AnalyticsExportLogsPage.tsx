import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../../api/services';
import type { ExportLogRow } from './types';
import styles from './AnalyticsPage.module.css';

export default function AnalyticsExportLogsPage() {
    const { data, isLoading, error } = useQuery({
        queryKey: ['analytics-export-logs'],
        queryFn: () => analyticsApi.exportLogs({ limit: 100 }),
    });

    if (isLoading) return <div className={styles.pageContainer}>Loading...</div>;
    if (error) return <div className={styles.pageContainer}>Error loading export logs</div>;

    const rows = (data?.rows || []) as ExportLogRow[];

    return (
        <div className={styles.pageContainer}>
            <div className={styles.header}>
                <h1>Export Logs</h1>
                <p>Audit trail of analytics exports</p>
            </div>

            <div className={styles.tableContainer}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th>Generated At</th>
                            <th>User</th>
                            <th>Report</th>
                            <th>Format</th>
                            <th>Rows</th>
                            <th>Filters</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.length === 0 ? (
                            <tr><td colSpan={6} style={{ textAlign: 'center' }}>No export logs</td></tr>
                        ) : (
                            rows.map((row) => (
                                <tr key={row.id}>
                                    <td>{new Date(row.generated_at).toLocaleString()}</td>
                                    <td>{row.user || 'Unknown'}</td>
                                    <td>{row.report_key}</td>
                                    <td>{row.format.toUpperCase()}</td>
                                    <td>{row.row_count}</td>
                                    <td>
                                        <code style={{ fontSize: '0.8em' }}>
                                            {JSON.stringify(row.filters_json)}
                                        </code>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
