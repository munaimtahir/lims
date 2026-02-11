import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import styles from './AnalyticsFilterBar.module.css';

interface AnalyticsFilterBarProps {
    onExport: (format: 'csv' | 'xlsx') => void;
    currentReportKey: string;
}

export function AnalyticsFilterBar({ onExport, currentReportKey }: AnalyticsFilterBarProps) {
    const [searchParams, setSearchParams] = useSearchParams();

    // Default to 'today' if not present
    const defaultStart = new Date().toISOString().split('T')[0];
    const defaultEnd = defaultStart;

    const [start, setStart] = useState(searchParams.get('start_date') || defaultStart);
    const [end, setEnd] = useState(searchParams.get('end_date') || defaultEnd);
    const [cancelled, setCancelled] = useState(searchParams.get('include_cancelled') === 'true');

    useEffect(() => {
        // Only update state if params changed externally
        const s = searchParams.get('start_date');
        const e = searchParams.get('end_date');
        const c = searchParams.get('include_cancelled') === 'true';
        if (s && s !== start) setStart(s);
        if (e && e !== end) setEnd(e);
        if (c !== cancelled) setCancelled(c);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchParams]);

    const handleApply = () => {
        const params: Record<string, string> = {
            start_date: start,
            end_date: end,
        };
        if (cancelled) {
            params.include_cancelled = 'true';
        }
        setSearchParams(params);
    };

    const handleKeyExport = (format: 'csv' | 'xlsx') => {
        onExport(format);
    };

    const handleReset = () => {
        const resetDate = new Date().toISOString().split('T')[0];
        setStart(resetDate);
        setEnd(resetDate);
        setCancelled(false);
        setSearchParams({
            start_date: resetDate,
            end_date: resetDate,
        });
    };

    return (
        <div className={`${styles.filterBar} ${styles.glass}`}>
            <div className={styles.fieldGroup}>
                <label className={styles.label}>Start Date</label>
                <input
                    type="date"
                    className={styles.input}
                    value={start}
                    onChange={e => setStart(e.target.value)}
                />
            </div>
            <div className={styles.fieldGroup}>
                <label className={styles.label}>End Date</label>
                <input
                    type="date"
                    className={styles.input}
                    value={end}
                    onChange={e => setEnd(e.target.value)}
                />
            </div>
            <div className={styles.fieldGroup}>
                <label className={styles.toggleLabel}>
                    <input
                        type="checkbox"
                        className={styles.checkbox}
                        checked={cancelled}
                        onChange={e => setCancelled(e.target.checked)}
                    />
                    <span>Include Cancelled</span>
                </label>
            </div>

            <div className={styles.actionParams}>
                <button className={styles.applyButton} onClick={handleApply}>
                    Update Report
                </button>
                <button className={styles.applyButton} onClick={handleReset}>
                    Reset
                </button>
                <div style={{ padding: '0 8px', borderLeft: '1px solid #e2e8f0', height: '32px' }}></div>
                <button className={styles.exportButton} onClick={() => handleKeyExport('csv')}>
                    CSV
                </button>
                <button className={styles.exportButton} onClick={() => handleKeyExport('xlsx')}>
                    Excel
                </button>
            </div>
        </div>
    );
}
