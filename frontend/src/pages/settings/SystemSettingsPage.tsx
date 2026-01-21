import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { systemSettingsApi } from '../../api/services';
import { normalizeObjectResponse } from '../../utils/apiHelpers';
import type { SystemSettings } from '../../types';
import styles from './SystemSettingsPage.module.css';

export default function SystemSettingsPage() {
  const queryClient = useQueryClient();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState<'ui' | 'lab' | 'reports' | 'email' | 'backup'>('lab');
  const [headerFile, setHeaderFile] = useState<File | null>(null);
  const [footerFile, setFooterFile] = useState<File | null>(null);
  const [logoFile, setLogoFile] = useState<File | null>(null);

  const { data: settingsData, isLoading } = useQuery({
    queryKey: ['system-settings'],
    queryFn: () => systemSettingsApi.get(),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<SystemSettings>) => systemSettingsApi.patch(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
      alert('Settings updated successfully');
    },
    onError: (error: unknown) => {
      alert(`Error updating settings: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const uploadHeaderMutation = useMutation({
    mutationFn: (file: File) => systemSettingsApi.uploadReportHeaderImage(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
      setHeaderFile(null);
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.error ??
        error?.message ??
        'Failed to upload header image. Please try again.';
      alert(message);
    },
  });

  const uploadFooterMutation = useMutation({
    mutationFn: (file: File) => systemSettingsApi.uploadReportFooterImage(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
      setFooterFile(null);
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.error ??
        error?.message ??
        'Failed to upload footer image. Please try again.';
      alert(message);
    },
  });

  const removeHeaderMutation = useMutation({
    mutationFn: () => systemSettingsApi.removeReportHeaderImage(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.error ??
        error?.message ??
        'Failed to remove header image. Please try again.';
      alert(message);
    },
  });

  const removeFooterMutation = useMutation({
    mutationFn: () => systemSettingsApi.removeReportFooterImage(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.error ??
        error?.message ??
        'Failed to remove footer image. Please try again.';
      alert(message);
    },
  });

  const uploadLogoMutation = useMutation({
    mutationFn: (file: File) => systemSettingsApi.uploadLabLogo(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
      queryClient.invalidateQueries({ queryKey: ['branding'] });
      setLogoFile(null);
      alert('Logo updated successfully');
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.error ??
        error?.message ??
        'Failed to upload logo. Please try again.';
      alert(message);
    },
  });

  const removeLogoMutation = useMutation({
    mutationFn: () => systemSettingsApi.removeLabLogo(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
      queryClient.invalidateQueries({ queryKey: ['branding'] });
      alert('Logo removed successfully');
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.error ??
        error?.message ??
        'Failed to remove logo. Please try again.';
      alert(message);
    },
  });

  // Use normalizer to handle both wrapped {data: {...}} and plain object responses
  const settings = normalizeObjectResponse<SystemSettings>(settingsData);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tab = params.get('tab');
    if (tab === 'ui' || tab === 'reports' || tab === 'lab' || tab === 'email' || tab === 'backup') {
      setActiveTab(tab);
    }
  }, [location.search]);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data: Partial<SystemSettings> = {};

    // Lab Information
    if (formData.get('lab_name')) data.lab_name = formData.get('lab_name') as string;
    if (formData.get('lab_display_name')) data.lab_display_name = formData.get('lab_display_name') as string;
    if (formData.get('lab_address')) data.lab_address = formData.get('lab_address') as string;
    if (formData.get('lab_phone')) data.lab_phone = formData.get('lab_phone') as string;
    if (formData.get('lab_email')) data.lab_email = formData.get('lab_email') as string;

    // Report Customization
    if (formData.get('report_header')) data.report_header = formData.get('report_header') as string;
    if (formData.get('report_footer')) data.report_footer = formData.get('report_footer') as string;

    // Financial Settings
    if (formData.get('currency')) data.currency = formData.get('currency') as string;
    if (formData.get('tax_rate')) data.tax_rate = formData.get('tax_rate') as string;

    // Email Configuration
    if (formData.get('email_host')) data.email_host = formData.get('email_host') as string;
    if (formData.get('email_port')) data.email_port = Number(formData.get('email_port'));
    if (formData.get('email_use_tls')) data.email_use_tls = formData.get('email_use_tls') === 'on';
    if (formData.get('email_use_ssl')) data.email_use_ssl = formData.get('email_use_ssl') === 'on';
    if (formData.get('email_host_user')) data.email_host_user = formData.get('email_host_user') as string;
    if (formData.get('email_host_password')) data.email_host_password = formData.get('email_host_password') as string;
    if (formData.get('email_from')) data.email_from = formData.get('email_from') as string;

    // Backup Settings
    if (formData.get('backup_enabled')) data.backup_enabled = formData.get('backup_enabled') === 'on';
    if (formData.get('backup_frequency')) data.backup_frequency = formData.get('backup_frequency') as 'daily' | 'weekly' | 'monthly';

    updateMutation.mutate(data);
  };

  if (isLoading) {
    return <div className={styles.loading}>Loading settings...</div>;
  }

  if (!settings) {
    return <div className={styles.error}>Failed to load settings</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>System Settings</h1>
        <p className={styles.subtitle}>Configure system-wide settings</p>
      </div>

      <div className={styles.tabs}>
        <button
          className={activeTab === 'ui' ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab('ui')}
        >
          UI Update
        </button>
        <button
          className={activeTab === 'lab' ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab('lab')}
        >
          Lab Information
        </button>
        <button
          className={activeTab === 'reports' ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab('reports')}
        >
          Report Customization
        </button>
        <button
          className={activeTab === 'email' ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab('email')}
        >
          Email Settings
        </button>
        <button
          className={activeTab === 'backup' ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab('backup')}
        >
          Backup Settings
        </button>
      </div>

      <form onSubmit={handleSubmit} className={styles.form}>
        {activeTab === 'ui' && (
          <div className={styles.tabContent}>
            <h2>UI Update</h2>
            <p className={styles.description}>
              Customize the branding that appears in your application header and login page.
            </p>
            
            <div className={styles.formGroup}>
              <label>Laboratory Display Name</label>
              <input
                type="text"
                name="lab_display_name"
                defaultValue={settings.lab_display_name || ''}
                placeholder="Enter display name for UI (optional, defaults to Lab Name)"
                className={styles.input}
              />
              <small className={styles.hint}>
                This name will appear in the header and login page. If not set, the Lab Name will be used.
              </small>
            </div>

            <div className={styles.formGroup}>
              <label>Laboratory Logo</label>
              {settings.lab_logo && (
                <div className={styles.brandingPreview}>
                  <div className={styles.previewCard}>
                    <img src={settings.lab_logo} alt="Lab logo" />
                    <div className={styles.previewInfo}>
                      <strong>{settings.lab_display_name || settings.lab_name}</strong>
                      <span>Current logo</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeLogoMutation.mutate()}
                    className={styles.removeButton}
                    disabled={removeLogoMutation.isPending}
                  >
                    {removeLogoMutation.isPending ? 'Removing...' : 'Remove Logo'}
                  </button>
                </div>
              )}
              <div className={styles.uploadRow}>
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/jpg,image/webp"
                  onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
                />
                <button
                  type="button"
                  className={styles.uploadButton}
                  disabled={!logoFile || uploadLogoMutation.isPending}
                  onClick={() => logoFile && uploadLogoMutation.mutate(logoFile)}
                >
                  {uploadLogoMutation.isPending ? 'Uploading...' : 'Upload Logo'}
                </button>
              </div>
              <small className={styles.hint}>
                Accepted formats: PNG, JPG, JPEG, WEBP (max 5MB). Logo will appear in header and login page.
              </small>
            </div>

            {(settings.lab_logo || settings.lab_display_name) && (
              <div className={styles.previewSection}>
                <h3>Preview</h3>
                <div className={styles.headerPreview}>
                  {settings.lab_logo && (
                    <img src={settings.lab_logo} alt="Logo preview" className={styles.previewLogo} />
                  )}
                  <span className={styles.previewName}>
                    {settings.lab_display_name || settings.lab_name}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'lab' && (
          <div className={styles.tabContent}>
            <h2>Laboratory Information</h2>
            <div className={styles.formGroup}>
              <label>Lab Name *</label>
              <input
                type="text"
                name="lab_name"
                defaultValue={settings.lab_name}
                required
                className={styles.input}
              />
            </div>
            <div className={styles.formGroup}>
              <label>Lab Address</label>
              <textarea
                name="lab_address"
                defaultValue={settings.lab_address || ''}
                className={styles.textarea}
                rows={3}
              />
            </div>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>Lab Phone</label>
                <input
                  type="text"
                  name="lab_phone"
                  defaultValue={settings.lab_phone || ''}
                  className={styles.input}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Lab Email</label>
                <input
                  type="email"
                  name="lab_email"
                  defaultValue={settings.lab_email || ''}
                  className={styles.input}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className={styles.tabContent}>
            <h2>Report Customization</h2>
            <div className={styles.formGroup}>
              <label>Header Image</label>
              {settings.report_header_image && (
                <div className={styles.imagePreview}>
                  <img src={settings.report_header_image} alt="Report header" />
                  <button
                    type="button"
                    onClick={() => removeHeaderMutation.mutate()}
                    className={styles.removeButton}
                  >
                    Remove
                  </button>
                </div>
              )}
              <div className={styles.uploadRow}>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setHeaderFile(e.target.files?.[0] || null)}
                />
                <button
                  type="button"
                  className={styles.uploadButton}
                  disabled={!headerFile || uploadHeaderMutation.isPending}
                  onClick={() => headerFile && uploadHeaderMutation.mutate(headerFile)}
                >
                  {uploadHeaderMutation.isPending ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </div>
            <div className={styles.formGroup}>
              <label>Report Header</label>
              <textarea
                name="report_header"
                defaultValue={settings.report_header || ''}
                className={styles.textarea}
                rows={4}
                placeholder="Custom header text for reports"
              />
            </div>
            <div className={styles.formGroup}>
              <label>Report Footer</label>
              <textarea
                name="report_footer"
                defaultValue={settings.report_footer || ''}
                className={styles.textarea}
                rows={4}
                placeholder="Custom footer text for reports"
              />
            </div>
            <div className={styles.formGroup}>
              <label>Footer Image</label>
              {settings.report_footer_image && (
                <div className={styles.imagePreview}>
                  <img src={settings.report_footer_image} alt="Report footer" />
                  <button
                    type="button"
                    onClick={() => removeFooterMutation.mutate()}
                    className={styles.removeButton}
                  >
                    Remove
                  </button>
                </div>
              )}
              <div className={styles.uploadRow}>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setFooterFile(e.target.files?.[0] || null)}
                />
                <button
                  type="button"
                  className={styles.uploadButton}
                  disabled={!footerFile || uploadFooterMutation.isPending}
                  onClick={() => footerFile && uploadFooterMutation.mutate(footerFile)}
                >
                  {uploadFooterMutation.isPending ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>Currency</label>
                <input
                  type="text"
                  name="currency"
                  defaultValue={settings.currency}
                  className={styles.input}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Tax Rate (%)</label>
                <input
                  type="number"
                  step="0.01"
                  name="tax_rate"
                  defaultValue={settings.tax_rate}
                  className={styles.input}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'email' && (
          <div className={styles.tabContent}>
            <h2>Email Configuration</h2>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>SMTP Host</label>
                <input
                  type="text"
                  name="email_host"
                  defaultValue={settings.email_host || ''}
                  className={styles.input}
                />
              </div>
              <div className={styles.formGroup}>
                <label>SMTP Port</label>
                <input
                  type="number"
                  name="email_port"
                  defaultValue={settings.email_port}
                  className={styles.input}
                />
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>
                  <input
                    type="checkbox"
                    name="email_use_tls"
                    defaultChecked={settings.email_use_tls}
                    className={styles.checkbox}
                  />
                  Use TLS
                </label>
              </div>
              <div className={styles.formGroup}>
                <label>
                  <input
                    type="checkbox"
                    name="email_use_ssl"
                    defaultChecked={settings.email_use_ssl}
                    className={styles.checkbox}
                  />
                  Use SSL
                </label>
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>SMTP Username</label>
                <input
                  type="text"
                  name="email_host_user"
                  defaultValue={settings.email_host_user || ''}
                  className={styles.input}
                />
              </div>
              <div className={styles.formGroup}>
                <label>SMTP Password</label>
                <input
                  type="password"
                  name="email_host_password"
                  defaultValue={settings.email_host_password || ''}
                  className={styles.input}
                />
              </div>
            </div>
            <div className={styles.formGroup}>
              <label>From Email Address</label>
              <input
                type="email"
                name="email_from"
                defaultValue={settings.email_from || ''}
                className={styles.input}
              />
            </div>
          </div>
        )}

        {activeTab === 'backup' && (
          <div className={styles.tabContent}>
            <h2>Backup Settings</h2>
            <div className={styles.formGroup}>
              <label>
                <input
                  type="checkbox"
                  name="backup_enabled"
                  defaultChecked={settings.backup_enabled}
                  className={styles.checkbox}
                />
                Enable Automated Backups
              </label>
            </div>
            <div className={styles.formGroup}>
              <label>Backup Frequency</label>
              <select
                name="backup_frequency"
                defaultValue={settings.backup_frequency}
                className={styles.select}
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>
        )}

        <div className={styles.formActions}>
          <button type="submit" className={styles.submitButton} disabled={updateMutation.isPending}>
            {updateMutation.isPending ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </form>
    </div>
  );
}

