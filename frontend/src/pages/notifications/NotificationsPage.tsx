import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { notificationApi } from '../../api/services';
import type { Notification } from '../../types';
import styles from './NotificationsPage.module.css';

export default function NotificationsPage() {
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);

  const { data: notificationsData, isLoading } = useQuery({
    queryKey: ['notifications', selectedType, selectedStatus, searchQuery],
    queryFn: () => notificationApi.list({
      ...(selectedType && { notification_type: selectedType }),
      ...(selectedStatus && { status: selectedStatus }),
      ...(searchQuery && { search: searchQuery }),
    }),
  });

  const notifications = notificationsData?.results || [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SENT':
        return styles.sent;
      case 'PENDING':
        return styles.pending;
      case 'FAILED':
        return styles.failed;
      case 'CANCELLED':
        return styles.cancelled;
      default:
        return '';
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Notifications</h1>
        <p className={styles.subtitle}>View system notifications and email history</p>
      </div>

      <div className={styles.filters}>
        <div className={styles.filter}>
          <label>Type:</label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className={styles.select}
          >
            <option value="">All Types</option>
            <option value="ORDER_COMPLETE">Order Complete</option>
            <option value="CRITICAL_VALUE">Critical Value</option>
            <option value="PAYMENT_RECEIPT">Payment Receipt</option>
            <option value="REPORT_READY">Report Ready</option>
            <option value="SYSTEM_ALERT">System Alert</option>
          </select>
        </div>

        <div className={styles.filter}>
          <label>Status:</label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className={styles.select}
          >
            <option value="">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="SENT">Sent</option>
            <option value="FAILED">Failed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>

        <div className={styles.searchFilter}>
          <input
            type="text"
            placeholder="Search by subject, message, or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
        </div>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading notifications...</div>
      ) : notifications.length === 0 ? (
        <div className={styles.noData}>No notifications found</div>
      ) : (
        <div className={styles.list}>
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className={styles.notificationCard}
              onClick={() => setSelectedNotification(notification)}
            >
              <div className={styles.cardHeader}>
                <div className={styles.cardTitle}>
                  <h3>{notification.subject}</h3>
                  <span className={`${styles.status} ${getStatusColor(notification.status)}`}>
                    {notification.status_display}
                  </span>
                </div>
                <div className={styles.cardMeta}>
                  <span className={styles.type}>{notification.notification_type_display}</span>
                  <span className={styles.date}>
                    {new Date(notification.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
              <div className={styles.cardBody}>
                <p className={styles.recipient}>To: {notification.recipient_email}</p>
                <p className={styles.messagePreview}>
                  {notification.message.substring(0, 150)}
                  {notification.message.length > 150 ? '...' : ''}
                </p>
                {notification.sent_at && (
                  <p className={styles.sentAt}>
                    Sent: {new Date(notification.sent_at).toLocaleString()}
                  </p>
                )}
                {notification.error_message && (
                  <p className={styles.error}>Error: {notification.error_message}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedNotification && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <div className={styles.modalHeader}>
              <h2>{selectedNotification.subject}</h2>
              <button
                onClick={() => setSelectedNotification(null)}
                className={styles.closeButton}
              >
                ×
              </button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.detailRow}>
                <strong>Type:</strong>
                <span>{selectedNotification.notification_type_display}</span>
              </div>
              <div className={styles.detailRow}>
                <strong>Status:</strong>
                <span className={getStatusColor(selectedNotification.status)}>
                  {selectedNotification.status_display}
                </span>
              </div>
              <div className={styles.detailRow}>
                <strong>Recipient:</strong>
                <span>{selectedNotification.recipient_email}</span>
              </div>
              {selectedNotification.recipient_user_name && (
                <div className={styles.detailRow}>
                  <strong>User:</strong>
                  <span>{selectedNotification.recipient_user_name}</span>
                </div>
              )}
              <div className={styles.detailRow}>
                <strong>Created:</strong>
                <span>{new Date(selectedNotification.created_at).toLocaleString()}</span>
              </div>
              {selectedNotification.sent_at && (
                <div className={styles.detailRow}>
                  <strong>Sent:</strong>
                  <span>{new Date(selectedNotification.sent_at).toLocaleString()}</span>
                </div>
              )}
              {selectedNotification.error_message && (
                <div className={styles.detailRow}>
                  <strong>Error:</strong>
                  <span className={styles.error}>{selectedNotification.error_message}</span>
                </div>
              )}
              <div className={styles.messageSection}>
                <strong>Message:</strong>
                <div className={styles.messageContent}>{selectedNotification.message}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


