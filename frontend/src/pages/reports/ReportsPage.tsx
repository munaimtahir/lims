import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportApi } from '../../api/services';
import styles from './ReportsPage.module.css';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportApi, systemSettingsApi } from '../../api/services';
import type { Report } from '../../types';
import styles from './ReportsPage.module.css';

export default function ReportsPage() {
  const queryClient = useQueryClient();
  const [expandedPatientId, setExpandedPatientId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const { data: reportsData, isLoading } = useQuery({
    queryKey: ['reports', searchQuery],
    queryFn: () => reportApi.list({ ...(searchQuery && { search: searchQuery }) }),
  });

  const { data: settingsData } = useQuery({
    queryKey: ['system-settings'],
    queryFn: () => systemSettingsApi.get(),
  });

  const downloadMutation = useMutation({
    mutationFn: async (reportId: number) => {
      const blob = await reportApi.download(reportId);
      return blob;
    },
  });

  const handlePrint = async (reportId: number) => {
    try {
      const blob = await downloadMutation.mutateAsync(reportId);
      const url = window.URL.createObjectURL(blob);

      // For immediate printing, we use an iframe
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.src = url;
      document.body.appendChild(iframe);

      iframe.onload = () => {
        iframe.contentWindow?.print();
        setTimeout(() => {
          document.body.removeChild(iframe);
          window.URL.revokeObjectURL(url);
        }, 1000);
      };
    } catch (error) {
      console.error('Print failed:', error);
      alert('Failed to print report.');
    }
  };

  const reports = reportsData?.results || [];

  // Grouping reports by patient (simplified for this view)
  const groupedReports = reports.reduce((acc: any, report: any) => {
    const pId = report.patient_id || report.order; // Fallback if patient_id not directly in report
    if (!acc[pId]) {
      acc[pId] = {
        patient_name: report.patient_name || report.order_id_display || 'Unknown Patient',
        reports: []
      };
    }
    acc[pId].reports.push(report);
    return acc;
  }, {});

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Published Reports</h1>
        <p className={styles.subtitle}>Verified results ready for printing</p>
      </div>

      <div className={styles.filters}>
        <input
          type="text"
          placeholder="Search by patient name or Order ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className={styles.searchInput}
        />
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading reports...</div>
      ) : (
        <div className={styles.accordionList}>
          {Object.entries(groupedReports).map(([pId, group]: [string, any]) => (
            <div key={pId} className={`${styles.accordionItem} ${expandedPatientId === Number(pId) ? styles.active : ''}`}>
              <div
                className={styles.accordionHeader}
                onClick={() => setExpandedPatientId(expandedPatientId === Number(pId) ? null : Number(pId))}
              >
                <div className={styles.patientInfo}>
                  <span className={styles.patientName}>{group.patient_name}</span>
                  <span className={styles.reportCount}>{group.reports.length} report(s)</span>
                </div>
                <span className={styles.chevron}>{expandedPatientId === Number(pId) ? '▼' : '▶'}</span>
              </div>

              {expandedPatientId === Number(pId) && (
                <div className={styles.accordionContent}>
                  <table className={styles.reportsTable}>
                    <thead>
                      <tr>
                        <th>Order ID</th>
                        <th>Tests</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {group.reports.map((report: any) => (
                        <tr key={report.id}>
                          <td>{report.order_id_display || `#${report.order}`}</td>
                          <td>{report.test_names || 'General Report'}</td>
                          <td>
                            <span className={styles.verifiedBadge}>Verified</span>
                          </td>
                          <td>
                            <button
                              className={styles.printBtn}
                              onClick={() => handlePrint(report.id)}
                            >
                              Print (A5)
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}

          {Object.keys(groupedReports).length === 0 && (
            <div className={styles.emptyState}>No reports found.</div>
          )}
        </div>
      )}

      {/* Styles for A5 printing can be injected or handled via global CSS */}
      <style dangerouslySetInnerHTML={{
        __html: `
        @media print {
          @page {
            size: A5;
            margin: 0;
          }
          body {
            background: white;
          }
          /* Custom styles for the report content if it was rendered here */
        }
      `}} />
    </div>
  );
}
