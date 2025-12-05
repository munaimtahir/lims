import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../../api/client';
import type { PaginatedResponse } from '../../types';
import styles from './AuditLogsPage.module.css';

interface AuditLog {
  id: number;
  user?: number;
  user_name?: string;
  user_role?: string;
  action: string;
  table_name: string;
  object_id?: string;
  old_value?: Record<string, unknown>;
  new_value?: Record<string, unknown>;
  timestamp: string;
  ip_address?: string;
  notes?: string;
}

export default function AuditLogsPage() {
  const [actionFilter, setActionFilter] = useState<string>('');
  const [tableFilter, setTableFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  const { data: logsData, isLoading, error } = useQuery({
    queryKey: ['audit-logs', actionFilter, tableFilter, searchQuery],
    queryFn: async () => {
      const params: Record<string, unknown> = {};
      if (actionFilter) params.action = actionFilter;
      if (tableFilter) params.table_name = tableFilter;
      if (searchQuery) params.search = searchQuery;
      
      const response = await api.get<PaginatedResponse<AuditLog>>('/audit/logs/', { params });
      return response.data;
    },
  });

  const logs = logsData?.results || [];

  const getActionBadgeClass = (action: string) => {
    switch (action) {
      case 'CREATE':
        return styles.actionCreate;
      case 'UPDATE':
        return styles.actionUpdate;
      case 'DELETE':
        return styles.actionDelete;
      case 'VERIFY':
      case 'APPROVE':
        return styles.actionApprove;
      case 'REJECT':
        return styles.actionReject;
      default:
        return styles.actionDefault;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Audit Logs</h1>
        <p className={styles.subtitle}>System activity and change tracking</p>
      </div>

      <div className={styles.filters}>
        <div className={styles.filterGroup}>
          <label>Action:</label>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className={styles.select}
          >
            <option value="">All Actions</option>
            <option value="CREATE">Create</option>
            <option value="UPDATE">Update</option>
            <option value="DELETE">Delete</option>
            <option value="VERIFY">Verify</option>
            <option value="APPROVE">Approve</option>
            <option value="REJECT">Reject</option>
            <option value="LOGIN">Login</option>
            <option value="LOGOUT">Logout</option>
          </select>
        </div>

        <div className={styles.filterGroup}>
          <label>Table:</label>
          <select
            value={tableFilter}
            onChange={(e) => setTableFilter(e.target.value)}
            className={styles.select}
          >
            <option value="">All Tables</option>
            <option value="patients">Patients</option>
            <option value="orders">Orders</option>
            <option value="samples">Samples</option>
            <option value="results">Results</option>
            <option value="reports">Reports</option>
            <option value="payments">Payments</option>
          </select>
        </div>

        <div className={styles.searchFilter}>
          <input
            type="text"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
        </div>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading audit logs...</div>
      ) : error ? (
        <div className={styles.error}>Failed to load audit logs</div>
      ) : (
        <div className={styles.logsContainer}>
          {logs.map((log) => (
            <div key={log.id} className={styles.logEntry}>
              <div className={styles.logHeader}>
                <div className={styles.logMeta}>
                  <span className={`${styles.actionBadge} ${getActionBadgeClass(log.action)}`}>
                    {log.action}
                  </span>
                  <span className={styles.tableName}>{log.table_name}</span>
                  {log.object_id && (
                    <span className={styles.objectId}>ID: {log.object_id}</span>
                  )}
                </div>
                <span className={styles.timestamp}>
                  {new Date(log.timestamp).toLocaleString()}
                </span>
              </div>
              
              <div className={styles.logDetails}>
                <div className={styles.detailRow}>
                  <span className={styles.label}>User:</span>
                  <span className={styles.value}>
                    {log.user_name || 'System'} ({log.user_role || 'N/A'})
                  </span>
                </div>
                
                {log.ip_address && (
                  <div className={styles.detailRow}>
                    <span className={styles.label}>IP Address:</span>
                    <span className={styles.value}>{log.ip_address}</span>
                  </div>
                )}
                
                {log.notes && (
                  <div className={styles.detailRow}>
                    <span className={styles.label}>Notes:</span>
                    <span className={styles.value}>{log.notes}</span>
                  </div>
                )}
                
                {(log.old_value || log.new_value) && (
                  <div className={styles.changes}>
                    {log.old_value && (
                      <div className={styles.changeSection}>
                        <strong>Old Value:</strong>
                        <pre className={styles.jsonValue}>
                          {JSON.stringify(log.old_value, null, 2)}
                        </pre>
                      </div>
                    )}
                    {log.new_value && (
                      <div className={styles.changeSection}>
                        <strong>New Value:</strong>
                        <pre className={styles.jsonValue}>
                          {JSON.stringify(log.new_value, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {logs.length === 0 && (
            <div className={styles.noData}>No audit logs found</div>
          )}
        </div>
      )}
    </div>
  );
}
