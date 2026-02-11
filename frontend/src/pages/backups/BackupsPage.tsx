import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { backupApi } from '../../api/services';
import { normalizeListResponse } from '../../utils/apiHelpers';
import type { BackupArtifact } from '../../types';
import styles from './BackupsPage.module.css';

const POLL_MS = 4000;

function formatBytes(size: number): string {
  if (!size) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  const value = size / Math.pow(1024, index);
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

export default function BackupsPage() {
  const queryClient = useQueryClient();
  const [importFile, setImportFile] = useState<File | null>(null);
  const [showRestoreModalFor, setShowRestoreModalFor] = useState<BackupArtifact | null>(null);
  const [restoreConfirmation, setRestoreConfirmation] = useState('');
  const [expandedLogs, setExpandedLogs] = useState<Record<string, boolean>>({});

  const { data, isLoading, error } = useQuery({
    queryKey: ['backups'],
    queryFn: () => backupApi.list(),
    refetchInterval: (query) => {
      const result = query.state.data;
      if (!result) return false;
      const rows = normalizeListResponse<BackupArtifact>(result);
      return rows.some((row) => row.status === 'PENDING' || row.status === 'RUNNING') ? POLL_MS : false;
    },
  });

  const { data: backupSettings } = useQuery({
    queryKey: ['backup-settings'],
    queryFn: () => backupApi.settings(),
  });

  const rows = useMemo(() => normalizeListResponse<BackupArtifact>(data), [data]);

  const createMutation = useMutation({
    mutationFn: (pushOffsite: boolean) => backupApi.create(pushOffsite),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backups'] });
    },
  });

  const importMutation = useMutation({
    mutationFn: (file: File) => backupApi.importBackup(file),
    onSuccess: () => {
      setImportFile(null);
      queryClient.invalidateQueries({ queryKey: ['backups'] });
      alert('Backup imported successfully.');
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Import failed';
      alert(msg);
    },
  });

  const restoreMutation = useMutation({
    mutationFn: ({ id, confirmation }: { id: string; confirmation: string }) => backupApi.restore(id, confirmation),
    onSuccess: () => {
      setShowRestoreModalFor(null);
      setRestoreConfirmation('');
      queryClient.invalidateQueries({ queryKey: ['backups'] });
      alert('Restore job queued. Monitor logs for progress.');
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Restore failed';
      alert(msg);
    },
  });

  const pushMutation = useMutation({
    mutationFn: (id: string) => backupApi.push(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backups'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => backupApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backups'] });
    },
  });

  const offsiteTestMutation = useMutation({
    mutationFn: () => backupApi.testOffsite(),
    onSuccess: (result) => {
      alert(result.message || 'Connection test complete');
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Offsite test failed';
      alert(msg);
    },
  });

  const handleDownload = async (backup: BackupArtifact) => {
    try {
      const blob = await backupApi.download(backup.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = backup.filename?.split('/').pop() || `${backup.id}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Download failed';
      alert(msg);
    }
  };

  if (isLoading) {
    return <div className={styles.state}>Loading backups...</div>;
  }

  if (error) {
    return <div className={styles.stateError}>Failed to load backups.</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Backups</h1>
        <p>Backup and restore database, media, and deployment snapshot artifacts.</p>
      </div>

      <section className={styles.toolbar}>
        <button
          className={styles.primaryBtn}
          onClick={() => createMutation.mutate(false)}
          disabled={createMutation.isPending}
        >
          Create Backup Now
        </button>
        <button
          className={styles.secondaryBtn}
          onClick={() => createMutation.mutate(true)}
          disabled={createMutation.isPending}
        >
          Create + Push Offsite
        </button>
      </section>

      <section className={styles.importPanel}>
        <h2>Import Backup</h2>
        <div className={styles.importRow}>
          <input
            type="file"
            accept=".zip"
            onChange={(e) => setImportFile(e.target.files?.[0] || null)}
          />
          <button
            className={styles.secondaryBtn}
            disabled={!importFile || importMutation.isPending}
            onClick={() => importFile && importMutation.mutate(importFile)}
          >
            Import
          </button>
        </div>
      </section>

      <section className={styles.settingsPanel}>
        <h2>Settings</h2>
        <div className={styles.settingsGrid}>
          <div>Retention Daily: {backupSettings?.retention_daily ?? '-'}</div>
          <div>Retention Weekly: {backupSettings?.retention_weekly ?? '-'}</div>
          <div>Retention Monthly: {backupSettings?.retention_monthly ?? '-'}</div>
          <div>Offsite Provider: {backupSettings?.offsite_provider ?? 'NONE'}</div>
          <div>Offsite Configured: {backupSettings?.offsite_configured ? 'Yes' : 'No'}</div>
        </div>
        <button
          className={styles.secondaryBtn}
          onClick={() => offsiteTestMutation.mutate()}
          disabled={offsiteTestMutation.isPending}
        >
          Test Offsite Connection
        </button>
      </section>

      <section className={styles.tablePanel}>
        <h2>Backup History</h2>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Created</th>
                <th>Type</th>
                <th>Status</th>
                <th>Size</th>
                <th>Offsite</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((backup) => {
                const isRunning = backup.status === 'PENDING' || backup.status === 'RUNNING';
                return (
                  <tr key={backup.id}>
                    <td>{formatDate(backup.created_at)}</td>
                    <td>{backup.type}</td>
                    <td>{backup.status}</td>
                    <td>{formatBytes(backup.size_bytes)}</td>
                    <td>{backup.offsite_status}</td>
                    <td>
                      <div className={styles.actions}>
                        <button className={styles.linkBtn} onClick={() => handleDownload(backup)}>Download</button>
                        <button
                          className={styles.linkBtn}
                          onClick={() => setShowRestoreModalFor(backup)}
                          disabled={isRunning}
                        >
                          Restore
                        </button>
                        <button
                          className={styles.linkBtn}
                          onClick={() => pushMutation.mutate(backup.id)}
                          disabled={pushMutation.isPending || isRunning}
                        >
                          Push
                        </button>
                        <button
                          className={styles.linkBtnDanger}
                          onClick={() => {
                            if (window.confirm(`Delete backup ${backup.id}?`)) {
                              deleteMutation.mutate(backup.id);
                            }
                          }}
                          disabled={deleteMutation.isPending || isRunning}
                        >
                          Delete
                        </button>
                        <button
                          className={styles.linkBtn}
                          onClick={() =>
                            setExpandedLogs((prev) => ({ ...prev, [backup.id]: !prev[backup.id] }))
                          }
                        >
                          {expandedLogs[backup.id] ? 'Hide Logs' : 'Logs'}
                        </button>
                      </div>
                      {expandedLogs[backup.id] && (
                        <pre className={styles.logsBlock}>{backup.logs || '(No logs yet)'}</pre>
                      )}
                      {!!backup.error_message && (
                        <div className={styles.errorInline}>{backup.error_message}</div>
                      )}
                    </td>
                  </tr>
                );
              })}
              {!rows.length && (
                <tr>
                  <td colSpan={6} className={styles.empty}>No backups yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {showRestoreModalFor && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <h3>Confirm Restore</h3>
            <p>
              This will overwrite current database and media. Type exactly:
            </p>
            <code className={styles.code}>RESTORE {showRestoreModalFor.id}</code>
            <input
              className={styles.input}
              value={restoreConfirmation}
              onChange={(e) => setRestoreConfirmation(e.target.value)}
              placeholder={`RESTORE ${showRestoreModalFor.id}`}
            />
            <div className={styles.modalActions}>
              <button className={styles.secondaryBtn} onClick={() => setShowRestoreModalFor(null)}>Cancel</button>
              <button
                className={styles.dangerBtn}
                onClick={() =>
                  restoreMutation.mutate({
                    id: showRestoreModalFor.id,
                    confirmation: restoreConfirmation,
                  })
                }
                disabled={restoreMutation.isPending}
              >
                Restore
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
