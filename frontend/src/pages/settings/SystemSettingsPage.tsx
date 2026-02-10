import { useEffect, useState, useMemo, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { systemSettingsApi, printTemplateApi, userApi } from '../../api/services';
import { normalizeListResponse, normalizeObjectResponse } from '../../utils/apiHelpers';
import { isSampleBarcodeEnabled, setSampleBarcodeEnabled as setStoredBarcodeEnabled } from '../../utils/featureFlags';
import type { SystemSettings, PrintTemplate, PrintSignatory, PrintTemplateConfig, User, UserRole } from '../../types';
import styles from './SystemSettingsPage.module.css';

export default function SystemSettingsPage() {
  const queryClient = useQueryClient();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState<'ui' | 'lab' | 'reports' | 'email' | 'backup' | 'print' | 'users'>(() => {
    const params = new URLSearchParams(location.search);
    const tab = params.get('tab');
    if (tab === 'ui' || tab === 'reports' || tab === 'lab' || tab === 'email' || tab === 'backup' || tab === 'print' || tab === 'users') {
      return tab;
    }
    return 'lab';
  });
  const [headerFile, setHeaderFile] = useState<File | null>(null);
  const [footerFile, setFooterFile] = useState<File | null>(null);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [barcodeToggle, setBarcodeToggle] = useState<boolean>(() => isSampleBarcodeEnabled());
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);
  const [templateForm, setTemplateForm] = useState<PrintTemplate | null>(null);

  // Replaced duplicate state with just one source of truth where possible, but keeping barcodeToggle for UI binding
  const [isCreatingTemplate, setIsCreatingTemplate] = useState(false);
  const [newTemplateData, setNewTemplateData] = useState<{ name: string; type: 'REPORT' | 'RECEIPT' }>({ name: '', type: 'REPORT' });
  const [userSearch, setUserSearch] = useState('');
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [userNotice, setUserNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const userNoticeTimeoutRef = useRef<number | null>(null);
  const [resetPasswordForm, setResetPasswordForm] = useState({ newPassword: '', confirmPassword: '' });
  const [userForm, setUserForm] = useState({
    username: '',
    email: '',
    full_name: '',
    role: 'Receptionist' as UserRole,
    is_active: true,
    password: '',
    password_confirm: '',
  });

  // Report Preview State
  const [previewKey, setPreviewKey] = useState(0);

  // Template Builder: section selection and undo/redo
  type TemplateSection = 'basic' | 'paper' | 'display' | 'compliance' | 'disclaimer' | 'signatories';
  const [selectedTemplateSection, setSelectedTemplateSection] = useState<TemplateSection>('basic');
  const [templateHistory, setTemplateHistory] = useState<PrintTemplate[]>([]);
  const [templateHistoryIndex, setTemplateHistoryIndex] = useState(-1);
  const HISTORY_MAX = 30;

  const roleOptions: UserRole[] = [
    'Admin',
    'Receptionist',
    'Cashier',
    'Phlebotomist',
    'Lab Technician',
    'Pathologist',
    'Manager',
  ];

  const { data: settingsData, isLoading } = useQuery({
    queryKey: ['system-settings'],
    queryFn: () => systemSettingsApi.get(),
  });

  const { data: templatesData } = useQuery({
    queryKey: ['print-templates'],
    queryFn: () => printTemplateApi.list(),
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
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { error?: string } }; message?: string };
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
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { error?: string } }; message?: string };
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
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { error?: string } }; message?: string };
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
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { error?: string } }; message?: string };
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
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { error?: string } }; message?: string };
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
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { error?: string } }; message?: string };
      const message =
        error?.response?.data?.error ??
        error?.message ??
        'Failed to remove logo. Please try again.';
      alert(message);
    },
  });

  const settings = normalizeObjectResponse<SystemSettings>(settingsData);
  const templates = useMemo(() => (templatesData || []) as PrintTemplate[], [templatesData]);
  const isUserTab = activeTab === 'users';

  const { data: usersData, isLoading: isUsersLoading, error: usersError } = useQuery({
    queryKey: ['users', userSearch],
    queryFn: () => userApi.list(userSearch ? { search: userSearch } : undefined),
    enabled: isUserTab,
  });

  const users = useMemo(() => (usersData ? normalizeListResponse<User>(usersData) : []), [usersData]);

  useEffect(() => {
    if (!templates.length) return;

    // Determine the template to select (preserve current selection if valid, else default to first)
    const targetId = selectedTemplateId && templates.find(t => t.id === selectedTemplateId)
      ? selectedTemplateId
      : templates[0]?.id;

    if (targetId && targetId !== selectedTemplateId) {
      setSelectedTemplateId(targetId);
      return;
    }

    // Sync form with selected template if form is stale; init undo history
    const template = templates.find((t) => t.id === selectedTemplateId);
    if (template && (!templateForm || templateForm.id !== template.id)) {
      const nextForm = { ...template };
      setTemplateForm(nextForm);
      setTemplateHistory([JSON.parse(JSON.stringify(nextForm))]);
      setTemplateHistoryIndex(0);
      setSelectedTemplateSection('basic');
    }
  }, [templates, selectedTemplateId, templateForm]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tab = params.get('tab');
    if ((tab === 'ui' || tab === 'reports' || tab === 'lab' || tab === 'email' || tab === 'backup' || tab === 'print' || tab === 'users') && activeTab !== tab) {
      setActiveTab(tab);
    }
  }, [location.search]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    return () => {
      if (userNoticeTimeoutRef.current) {
        window.clearTimeout(userNoticeTimeoutRef.current);
      }
    };
  }, []);

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
    if (formData.get('lab_whatsapp')) data.lab_whatsapp = formData.get('lab_whatsapp') as string;

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
    if (formData.get('backup_drive')) data.backup_drive = formData.get('backup_drive') as any;
    if (formData.get('backup_path')) data.backup_path = formData.get('backup_path') as string;
    if (formData.get('backup_auto_upload')) data.backup_auto_upload = formData.get('backup_auto_upload') === 'on';

    updateMutation.mutate(data);
  };

  const updateTemplateMutation = useMutation({
    mutationFn: (data: PrintTemplate) => printTemplateApi.update(data.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['print-templates'] });
      alert('Template updated');
    },
    onError: (error: unknown) => {
      alert(`Error updating template: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const createTemplateMutation = useMutation({
    mutationFn: (data: { name: string; type: 'REPORT' | 'RECEIPT' }) => {
      // Generate unique key based on name and timestamp to ensure uniqueness
      const templateKey = `${data.type.toLowerCase()}_${data.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_${Date.now()}`;
      // Define default config as per backend expectations
      const defaultConfig = {
        paper_size: 'A4',
        margins: { top: 1.0, right: 1.0, bottom: 1.0, left: 1.0 },
        font_scale: 1.0,
        show_logo: true,
        show_header_image: true,
        show_footer_image: true,
        show_disclaimer: true,
        show_signatures: true,
        show_qr: false,
        show_barcode: false
      };

      return printTemplateApi.create({
        name: data.name,
        type: data.type,
        template_key: templateKey,
        is_active: false,
        config: defaultConfig as unknown as PrintTemplate['config'], // cast to avoid strict type issues
        signatories: []
      } as Partial<PrintTemplate>);
    },
    onSuccess: (newTemplate) => {
      queryClient.invalidateQueries({ queryKey: ['print-templates'] });
      setIsCreatingTemplate(false);
      setNewTemplateData({ name: '', type: 'REPORT' });
      alert('Template created successfully');
      // Select the new template
      if (newTemplate && newTemplate.id) {
        setSelectedTemplateId(newTemplate.id);
      }
    },
    onError: (error: unknown) => {
      alert(`Error creating template: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const deleteTemplateMutation = useMutation({
    mutationFn: (id: number) => printTemplateApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['print-templates'] });
      setSelectedTemplateId(null);
      setTemplateForm(null);
      alert('Template deleted successfully');
    },
    onError: (error: unknown) => {
      alert(`Error deleting template: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const pushTemplateHistory = (next: PrintTemplate) => {
    setTemplateHistory((prev) => {
      const trimmed = prev.slice(0, templateHistoryIndex + 1);
      const nextArr = [...trimmed, JSON.parse(JSON.stringify(next))];
      return nextArr.slice(-HISTORY_MAX);
    });
    setTemplateHistoryIndex((prev) => Math.min(prev + 1, HISTORY_MAX - 1));
  };

  const canUndo = templateForm && templateHistory.length > 0 && templateHistoryIndex > 0;
  const canRedo = templateForm && templateHistory.length > 0 && templateHistoryIndex < templateHistory.length - 1;
  const handleTemplateUndo = () => {
    if (!canUndo || !templateHistory[templateHistoryIndex - 1]) return;
    setTemplateForm(JSON.parse(JSON.stringify(templateHistory[templateHistoryIndex - 1])));
    setTemplateHistoryIndex((i) => i - 1);
  };
  const handleTemplateRedo = () => {
    if (!canRedo || !templateHistory[templateHistoryIndex + 1]) return;
    setTemplateForm(JSON.parse(JSON.stringify(templateHistory[templateHistoryIndex + 1])));
    setTemplateHistoryIndex((i) => i + 1);
  };

  const updateTemplateField = (field: keyof PrintTemplate, value: string | boolean) => {
    if (!templateForm) return;
    const next = { ...templateForm, [field]: value };
    setTemplateForm(next);
    pushTemplateHistory(next);
  };

  const handleBarcodeToggle = (value: boolean) => {
    setBarcodeToggle(value);
    setStoredBarcodeEnabled(value);
  };

  const updateTemplateConfig = (field: keyof PrintTemplateConfig, value: string | number | boolean) => {
    if (!templateForm) return;
    const config = { ...templateForm.config, [field]: value };
    const next = { ...templateForm, config };
    setTemplateForm(next);
    pushTemplateHistory(next);
  };

  const updateMargin = (field: keyof PrintTemplateConfig['margins'], value: number) => {
    if (!templateForm) return;
    const margins = { ...templateForm.config.margins, [field]: value };
    const next = { ...templateForm, config: { ...templateForm.config, margins } };
    setTemplateForm(next);
    pushTemplateHistory(next);
  };

  const addSignatory = () => {
    if (!templateForm) return;
    const signatories = [...(templateForm.signatories || []), { name: '', title: '' }];
    const next = { ...templateForm, signatories };
    setTemplateForm(next);
    pushTemplateHistory(next);
  };

  const updateSignatory = (idx: number, field: keyof PrintSignatory, value: string) => {
    if (!templateForm) return;
    const signatories = [...(templateForm.signatories || [])];
    signatories[idx] = { ...signatories[idx], [field]: value };
    const next = { ...templateForm, signatories };
    setTemplateForm(next);
    pushTemplateHistory(next);
  };

  const removeSignatory = (idx: number) => {
    if (!templateForm) return;
    const signatories = [...(templateForm.signatories || [])];
    signatories.splice(idx, 1);
    const next = { ...templateForm, signatories };
    setTemplateForm(next);
    pushTemplateHistory(next);
  };

  const handleTemplateSaveDraft = () => {
    if (!templateForm) return;
    updateTemplateMutation.mutate({ ...templateForm, is_active: templateForm.is_active });
  };

  const handleTemplatePublish = () => {
    if (!templateForm) return;
    updateTemplateMutation.mutate({ ...templateForm, is_active: true });
  };

  const showUserNotice = (type: 'success' | 'error', message: string) => {
    setUserNotice({ type, message });
    if (userNoticeTimeoutRef.current) {
      window.clearTimeout(userNoticeTimeoutRef.current);
    }
    userNoticeTimeoutRef.current = window.setTimeout(() => {
      setUserNotice(null);
    }, 4000);
  };

  const resetUserForm = () => {
    setSelectedUserId(null);
    setUserForm({
      username: '',
      email: '',
      full_name: '',
      role: 'Receptionist' as UserRole,
      is_active: true,
      password: '',
      password_confirm: '',
    });
    setResetPasswordForm({ newPassword: '', confirmPassword: '' });
  };

  const createUserMutation = useMutation({
    mutationFn: (data: {
      username: string;
      email: string;
      full_name: string;
      role: UserRole;
      password: string;
      password_confirm: string;
    }) => userApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      showUserNotice('success', 'User created successfully.');
      resetUserForm();
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to create user.';
      showUserNotice('error', message);
    },
  });

  const updateUserMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<User> }) => userApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      showUserNotice('success', 'User updated successfully.');
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to update user.';
      showUserNotice('error', message);
    },
  });

  const deleteUserMutation = useMutation({
    mutationFn: (id: number) => userApi.remove(id),
    onSuccess: (_, removedId) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      showUserNotice('success', 'User removed successfully.');
      if (selectedUserId === removedId) {
        resetUserForm();
      }
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to remove user.';
      showUserNotice('error', message);
    },
  });

  const resetPasswordMutation = useMutation({
    mutationFn: ({ id, newPassword, confirmPassword }: { id: number; newPassword: string; confirmPassword: string }) =>
      userApi.resetPassword(id, newPassword, confirmPassword),
    onSuccess: () => {
      showUserNotice('success', 'Password reset successfully.');
      setResetPasswordForm({ newPassword: '', confirmPassword: '' });
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to reset password.';
      showUserNotice('error', message);
    },
  });

  const handleUserSave = () => {
    if (!userForm.username.trim() || !userForm.email.trim() || !userForm.full_name.trim()) {
      showUserNotice('error', 'Username, email, and full name are required.');
      return;
    }

    if (!selectedUserId) {
      if (!userForm.password || !userForm.password_confirm) {
        showUserNotice('error', 'Password and confirmation are required for new users.');
        return;
      }
      if (userForm.password !== userForm.password_confirm) {
        showUserNotice('error', 'Passwords do not match.');
        return;
      }
      createUserMutation.mutate({
        username: userForm.username.trim(),
        email: userForm.email.trim(),
        full_name: userForm.full_name.trim(),
        role: userForm.role,
        password: userForm.password,
        password_confirm: userForm.password_confirm,
      });
      return;
    }

    updateUserMutation.mutate({
      id: selectedUserId,
      data: {
        username: userForm.username.trim(),
        email: userForm.email.trim(),
        full_name: userForm.full_name.trim(),
        role: userForm.role,
        is_active: userForm.is_active,
      },
    });
  };

  const handleEditUser = (user: User) => {
    setSelectedUserId(user.id);
    setUserForm({
      username: user.username,
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      is_active: user.is_active,
      password: '',
      password_confirm: '',
    });
    setResetPasswordForm({ newPassword: '', confirmPassword: '' });
  };

  const handleDeleteUser = (user: User) => {
    if (!confirm(`Remove user ${user.full_name}? This cannot be undone.`)) return;
    deleteUserMutation.mutate(user.id);
  };

  const handleResetPassword = () => {
    if (!selectedUserId) return;
    if (!resetPasswordForm.newPassword || !resetPasswordForm.confirmPassword) {
      showUserNotice('error', 'Enter a new password and confirm it.');
      return;
    }
    if (resetPasswordForm.newPassword !== resetPasswordForm.confirmPassword) {
      showUserNotice('error', 'Passwords do not match.');
      return;
    }
    resetPasswordMutation.mutate({
      id: selectedUserId,
      newPassword: resetPasswordForm.newPassword,
      confirmPassword: resetPasswordForm.confirmPassword,
    });
  };

  const isEditingUser = Boolean(selectedUserId);

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
        <button
          className={activeTab === 'users' ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab('users')}
        >
          User Management
        </button>
        <button
          className={activeTab === 'print' ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab('print')}
        >
          Print Templates
        </button>
      </div>

      {activeTab === 'users' ? (
        <div className={styles.tabContent}>
          <h2>User Management</h2>
          <p className={styles.description}>
            Create, update, and deactivate users. Managers and admins can also reset passwords.
          </p>

          {userNotice && (
            <div className={`${styles.notice} ${userNotice.type === 'success' ? styles.noticeSuccess : styles.noticeError}`}>
              {userNotice.message}
            </div>
          )}

          <div className={styles.userGrid}>
            <div className={styles.userCard}>
              <div className={styles.cardHeader}>
                <div>
                  <h3>{isEditingUser ? 'Edit User' : 'Create User'}</h3>
                  <p className={styles.hint}>
                    {isEditingUser ? 'Update user details or reset the password below.' : 'Fill in the details to create a new user.'}
                  </p>
                </div>
                {isEditingUser && (
                  <button type="button" className={styles.secondaryButton} onClick={resetUserForm}>
                    Clear
                  </button>
                )}
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label>Username *</label>
                  <input
                    className={styles.input}
                    type="text"
                    value={userForm.username}
                    onChange={(e) => setUserForm((prev) => ({ ...prev, username: e.target.value }))}
                  />
                </div>
                <div className={styles.formGroup}>
                  <label>Email *</label>
                  <input
                    className={styles.input}
                    type="email"
                    value={userForm.email}
                    onChange={(e) => setUserForm((prev) => ({ ...prev, email: e.target.value }))}
                  />
                </div>
              </div>

              <div className={styles.formGroup}>
                <label>Full Name *</label>
                <input
                  className={styles.input}
                  type="text"
                  value={userForm.full_name}
                  onChange={(e) => setUserForm((prev) => ({ ...prev, full_name: e.target.value }))}
                />
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label>Role</label>
                  <select
                    className={styles.select}
                    value={userForm.role}
                    onChange={(e) => setUserForm((prev) => ({ ...prev, role: e.target.value as UserRole }))}
                  >
                    {roleOptions.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                </div>
                <div className={styles.formGroup}>
                  <label className={styles.checkboxLabel}>
                    <input
                      type="checkbox"
                      checked={userForm.is_active}
                      onChange={(e) => setUserForm((prev) => ({ ...prev, is_active: e.target.checked }))}
                      className={styles.checkbox}
                    />
                    Active
                  </label>
                </div>
              </div>

              {!isEditingUser && (
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Password *</label>
                    <input
                      className={styles.input}
                      type="password"
                      value={userForm.password}
                      onChange={(e) => setUserForm((prev) => ({ ...prev, password: e.target.value }))}
                    />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Confirm Password *</label>
                    <input
                      className={styles.input}
                      type="password"
                      value={userForm.password_confirm}
                      onChange={(e) => setUserForm((prev) => ({ ...prev, password_confirm: e.target.value }))}
                    />
                  </div>
                </div>
              )}

              <div className={styles.userFormActions}>
                <button
                  type="button"
                  className={styles.submitButton}
                  onClick={handleUserSave}
                  disabled={createUserMutation.isPending || updateUserMutation.isPending}
                >
                  {isEditingUser
                    ? (updateUserMutation.isPending ? 'Updating...' : 'Update User')
                    : (createUserMutation.isPending ? 'Creating...' : 'Create User')}
                </button>
              </div>

              {isEditingUser && (
                <div className={styles.resetPanel}>
                  <h4>Reset Password</h4>
                  <div className={styles.formRow}>
                    <div className={styles.formGroup}>
                      <label>New Password</label>
                      <input
                        className={styles.input}
                        type="password"
                        value={resetPasswordForm.newPassword}
                        onChange={(e) => setResetPasswordForm((prev) => ({ ...prev, newPassword: e.target.value }))}
                      />
                    </div>
                    <div className={styles.formGroup}>
                      <label>Confirm Password</label>
                      <input
                        className={styles.input}
                        type="password"
                        value={resetPasswordForm.confirmPassword}
                        onChange={(e) => setResetPasswordForm((prev) => ({ ...prev, confirmPassword: e.target.value }))}
                      />
                    </div>
                  </div>
                  <button
                    type="button"
                    className={styles.resetButton}
                    onClick={handleResetPassword}
                    disabled={resetPasswordMutation.isPending}
                  >
                    {resetPasswordMutation.isPending ? 'Resetting...' : 'Reset Password'}
                  </button>
                </div>
              )}
            </div>

            <div className={styles.userListCard}>
              <div className={styles.listHeader}>
                <div>
                  <h3>Users</h3>
                  <p className={styles.hint}>Search by name, username, or email.</p>
                </div>
                <input
                  className={styles.searchInput}
                  type="text"
                  placeholder="Search users..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                />
              </div>

              {isUsersLoading ? (
                <div className={styles.loading}>Loading users...</div>
              ) : usersError ? (
                <div className={styles.error}>Failed to load users.</div>
              ) : users.length === 0 ? (
                <div className={styles.emptyState}>No users found.</div>
              ) : (
                <div className={styles.tableWrapper}>
                  <table className={styles.userTable}>
                    <thead>
                      <tr>
                        <th>User</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Last Login</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => (
                        <tr key={user.id} className={selectedUserId === user.id ? styles.activeRow : undefined}>
                          <td>
                            <div className={styles.userIdentity}>
                              <span className={styles.userName}>{user.full_name}</span>
                              <span className={styles.userMeta}>@{user.username}</span>
                            </div>
                          </td>
                          <td>{user.email}</td>
                          <td>{user.role}</td>
                          <td>
                            <span
                              className={`${styles.statusBadge} ${user.is_active ? styles.statusActive : styles.statusInactive}`}
                            >
                              {user.is_active ? 'Active' : 'Disabled'}
                            </span>
                          </td>
                          <td>{user.last_login ? new Date(user.last_login).toLocaleString() : '—'}</td>
                          <td>
                            <div className={styles.userActions}>
                              <button
                                type="button"
                                className={`${styles.actionButton} ${styles.actionPrimary}`}
                                onClick={() => handleEditUser(user)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className={`${styles.actionButton} ${styles.actionDanger}`}
                                onClick={() => handleDeleteUser(user)}
                                disabled={deleteUserMutation.isPending}
                              >
                                Remove
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
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

              <div className={styles.formGroup}>
                <label>Enable sample barcode collection</label>
                <div className={styles.toggleRow}>
                  <input
                    type="checkbox"
                    checked={barcodeToggle}
                    onChange={(e) => handleBarcodeToggle(e.target.checked)}
                    style={{ width: '18px', height: '18px', marginRight: '10px', verticalAlign: 'bottom' }}
                  />
                  <span className={styles.hint} style={{ display: 'inline-block' }}>
                    When off, barcode entry prompts are hidden in Collection/Samples. Default: OFF.
                  </span>
                </div>
              </div>
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
                  <label>Lab Whatsapp Number</label>
                  <input
                    type="text"
                    name="lab_whatsapp"
                    defaultValue={settings.lab_whatsapp || ''}
                    placeholder="+1234567890"
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
              <div className={styles.twoColumn}>
                <div className={styles.column}>
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
                <div className={styles.column}>
                  <div className={styles.previewRefresher}>
                    <button type="button" className={styles.refreshButton} onClick={() => setPreviewKey(k => k + 1)}>
                      Refresh Preview
                    </button>
                  </div>
                  <div className={styles.reportPreviewPage} key={previewKey}>
                    {/* Mock Report Preview */}
                    <div className={styles.previewHeader}>
                      {settings.report_header_image ? (
                        <img src={settings.report_header_image} alt="Header" style={{ maxWidth: '100%', maxHeight: '50px' }} />
                      ) : (
                        <h3>{settings.lab_name}</h3>
                      )}
                      <p>{settings.report_header || "Lab Address & Contact Info"}</p>
                    </div>
                    <div style={{ flex: 1, padding: '20px', background: '#f8fafc', border: '1px dashed #cbd5e1', borderRadius: '4px' }}>
                      <h4>Patient Report</h4>
                      <p><strong>Patient:</strong> John Doe</p>
                      <p><strong>Test:</strong> Complete Blood Count</p>
                      <br />
                      <table style={{ width: '100%', fontSize: '11px', textAlign: 'left' }}>
                        <thead><tr><th>Parameter</th><th>Result</th><th>Ref Range</th></tr></thead>
                        <tbody>
                          <tr><td>Hemoglobin</td><td>14.5 g/dL</td><td>13.0 - 17.0</td></tr>
                          <tr><td>WBC</td><td>7.2 x10^9/L</td><td>4.0 - 11.0</td></tr>
                          <tr><td>Platelets</td><td>250 x10^9/L</td><td>150 - 450</td></tr>
                        </tbody>
                      </table>
                    </div>
                    <div className={styles.previewFooter}>
                      <p>{settings.report_footer || "End of Report"}</p>
                      {settings.report_footer_image && (
                        <img src={settings.report_footer_image} alt="Footer" style={{ maxWidth: '100%', maxHeight: '40px', marginTop: '5px' }} />
                      )}
                    </div>
                  </div>
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

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label>Backup Location</label>
                  <select
                    name="backup_drive"
                    defaultValue={settings.backup_drive || 'local'}
                    className={styles.select}
                  >
                    <option value="local">Local Storage</option>
                    <option value="google_drive">Google Drive</option>
                    <option value="dropbox">Dropbox</option>
                    <option value="onedrive">OneDrive</option>
                  </select>
                </div>

                <div className={styles.formGroup}>
                  <label>Backup Path / Folder</label>
                  <input
                    type="text"
                    name="backup_path"
                    defaultValue={settings.backup_path || '/var/backups/lims'}
                    className={styles.input}
                    placeholder="/path/to/backup/folder"
                  />
                </div>
              </div>

              <div className={styles.formGroup}>
                <label>
                  <input
                    type="checkbox"
                    name="backup_auto_upload"
                    defaultChecked={settings.backup_auto_upload}
                    className={styles.checkbox}
                  />
                  Auto-upload to Cloud
                </label>
              </div>

              <div className={styles.formGroup}>
                <button type="button" className={styles.secondaryButton} onClick={() => alert('Connect Logic Placeholder')}>
                  Login / Connect Account
                </button>
              </div>

              <hr style={{ margin: '20px 0', border: 0, borderTop: '1px solid #eee' }} />

              <div className={styles.formGroup}>
                <label>
                  <input
                    type="checkbox"
                    name="backup_enabled"
                    defaultChecked={settings.backup_enabled}
                    className={styles.checkbox}
                  />
                  Enable Automated Backups Schedule
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

          {activeTab === 'print' && (
            <div className={styles.tabContent}>
              <h2>Print Templates</h2>
              <p className={styles.description}>
                Configure report and receipt layouts. Edit one section at a time; preview updates as you change settings.
              </p>

              <div className={styles.formGroup}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <label style={{ margin: 0 }}>Template</label>
                  <button
                    type="button"
                    className={styles.secondaryButton}
                    onClick={() => { setIsCreatingTemplate(true); setNewTemplateData({ name: '', type: 'REPORT' }); }}
                    style={{ fontSize: '12px', padding: '4px 8px' }}
                  >
                    + Create New
                  </button>
                </div>

                {isCreatingTemplate ? (
                  <div className={styles.card} style={{ padding: '15px', border: '1px solid #e2e8f0', background: '#f8fafc', borderRadius: '4px', marginBottom: '15px' }}>
                    <h4 style={{ marginTop: 0, marginBottom: '10px' }}>Create New Template</h4>
                    <div className={styles.formGroup}>
                      <label>Name</label>
                      <input
                        className={styles.input}
                        value={newTemplateData.name}
                        onChange={e => setNewTemplateData({ ...newTemplateData, name: e.target.value })}
                        placeholder="e.g. CBC Report V2"
                      />
                    </div>
                    <div className={styles.formGroup}>
                      <label>Type</label>
                      <select
                        className={styles.select}
                        value={newTemplateData.type}
                        onChange={e => setNewTemplateData({ ...newTemplateData, type: e.target.value as 'REPORT' | 'RECEIPT' })}
                      >
                        <option value="REPORT">Report</option>
                        <option value="RECEIPT">Receipt</option>
                      </select>
                    </div>
                    <div className={styles.formActions} style={{ justifyContent: 'flex-start', gap: '10px', marginTop: '10px' }}>
                      <button
                        type="button"
                        className={styles.submitButton}
                        disabled={!newTemplateData.name || createTemplateMutation.isPending}
                        onClick={() => createTemplateMutation.mutate(newTemplateData)}
                      >
                        {createTemplateMutation.isPending ? 'Creating...' : 'Create'}
                      </button>
                      <button
                        type="button"
                        className={styles.secondaryButton}
                        onClick={() => setIsCreatingTemplate(false)}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  templates.length > 0 ? (
                    <select
                      className={styles.select}
                      value={selectedTemplateId || ''}
                      onChange={(e) => setSelectedTemplateId(Number(e.target.value))}
                    >
                      {templates.map((template) => (
                        <option key={template.id} value={template.id}>
                          {template.type} — {template.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <div className={styles.notice}>No templates found. Create one to get started.</div>
                  )
                )}
              </div>

              {templateForm && (
                <>
                  <div className={styles.templateToolbar}>
                    <button type="button" className={styles.secondaryButton} onClick={handleTemplateUndo} disabled={!canUndo} title="Undo last change">Undo</button>
                    <button type="button" className={styles.secondaryButton} onClick={handleTemplateRedo} disabled={!canRedo} title="Redo">Redo</button>
                  </div>

                  <div className={styles.templateThreePane}>
                    <nav className={styles.templateSectionList} aria-label="Template sections">
                      {(['basic', 'paper', 'display', 'compliance', 'disclaimer', 'signatories'] as const).map((section) => (
                        <button
                          key={section}
                          type="button"
                          className={selectedTemplateSection === section ? styles.templateSectionActive : styles.templateSectionBtn}
                          onClick={() => setSelectedTemplateSection(section)}
                        >
                          {section === 'basic' && 'Basic info'}
                          {section === 'paper' && 'Paper & margins'}
                          {section === 'display' && 'Display options'}
                          {section === 'compliance' && 'Compliance & flags'}
                          {section === 'disclaimer' && 'Disclaimer'}
                          {section === 'signatories' && 'Signatories'}
                        </button>
                      ))}
                    </nav>

                    <div className={styles.templatePreview} aria-label="Live preview">
                      <h3 className={styles.templatePreviewTitle}>Preview</h3>
                      <div className={styles.templatePreviewCard}>
                        <p><strong>{templateForm.name}</strong> ({templateForm.type})</p>
                        <p>Paper: {templateForm.config.paper_size} · Margins: {templateForm.config.margins.top}&quot; top, {templateForm.config.margins.bottom}&quot; bottom</p>
                        <p>Font scale: {templateForm.config.font_scale}</p>
                        <p>Logo: {templateForm.config.show_logo ? 'Yes' : 'No'} · Header image: {templateForm.config.show_header_image ? 'Yes' : 'No'} · Footer: {templateForm.config.show_footer_image ? 'Yes' : 'No'}</p>
                        <p>Disclaimer: {templateForm.config.show_disclaimer ? 'Yes' : 'No'} · Signatures: {templateForm.config.show_signatures ? 'Yes' : 'No'}</p>
                        <p>Compliance: IDs on pages {templateForm.config.repeat_patient_id_on_pages ? 'Yes' : 'No'} · Specimen details {templateForm.config.show_specimen_details ? 'Yes' : 'No'} · Critical flags {templateForm.config.show_critical_annotations ? 'Yes' : 'No'}</p>
                        <p>Active: {templateForm.is_active ? 'Yes' : 'No'}</p>
                      </div>
                    </div>

                    <div className={styles.templateEditor} role="form" aria-label="Edit selected section">
                      <h3 className={styles.templateEditorTitle}>
                        {selectedTemplateSection === 'basic' && 'Basic info'}
                        {selectedTemplateSection === 'paper' && 'Paper & margins'}
                        {selectedTemplateSection === 'display' && 'Display options'}
                        {selectedTemplateSection === 'disclaimer' && 'Disclaimer'}
                        {selectedTemplateSection === 'signatories' && 'Signatories'}
                      </h3>

                      {selectedTemplateSection === 'basic' && (
                        <>
                          <div className={styles.formGroup}>
                            <label title="Display name for this template">Template name</label>
                            <input className={styles.input} type="text" value={templateForm.name} onChange={(e) => updateTemplateField('name', e.target.value)} />
                          </div>
                          <div className={styles.formGroup}>
                            <label title="Optional description">Description</label>
                            <textarea className={styles.textarea} value={templateForm.description || ''} onChange={(e) => updateTemplateField('description', e.target.value)} rows={3} />
                          </div>
                          <div className={styles.formGroup}>
                            <label title="Use this template for printed reports">Set as active template</label>
                            <label className={styles.checkboxLabel}>
                              <input type="checkbox" checked={templateForm.is_active} onChange={(e) => updateTemplateField('is_active', e.target.checked)} />
                              Active
                            </label>
                          </div>
                        </>
                      )}

                      {selectedTemplateSection === 'paper' && (
                        <>
                          <div className={styles.formGroup}>
                            <label title="Page size for printing">Paper size</label>
                            <select className={styles.select} value={templateForm.config.paper_size} onChange={(e) => updateTemplateConfig('paper_size', e.target.value)}>
                              <option value="A4">A4</option>
                              <option value="Letter">Letter</option>
                            </select>
                          </div>
                          <div className={styles.formGroup}>
                            <label title="Text size multiplier">Font scale</label>
                            <input className={styles.input} type="number" step="0.1" min="0.5" max="2" value={templateForm.config.font_scale} onChange={(e) => updateTemplateConfig('font_scale', Number(e.target.value))} />
                          </div>
                          <p className={styles.templateHelp}>Margins in inches</p>
                          <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                              <label>Top</label>
                              <input className={styles.input} type="number" step="0.1" value={templateForm.config.margins.top} onChange={(e) => updateMargin('top', Number(e.target.value))} />
                            </div>
                            <div className={styles.formGroup}>
                              <label>Right</label>
                              <input className={styles.input} type="number" step="0.1" value={templateForm.config.margins.right} onChange={(e) => updateMargin('right', Number(e.target.value))} />
                            </div>
                            <div className={styles.formGroup}>
                              <label>Bottom</label>
                              <input className={styles.input} type="number" step="0.1" value={templateForm.config.margins.bottom} onChange={(e) => updateMargin('bottom', Number(e.target.value))} />
                            </div>
                            <div className={styles.formGroup}>
                              <label>Left</label>
                              <input className={styles.input} type="number" step="0.1" value={templateForm.config.margins.left} onChange={(e) => updateMargin('left', Number(e.target.value))} />
                            </div>
                          </div>
                        </>
                      )}

                      {selectedTemplateSection === 'display' && (
                        <div className={styles.formRow}>
                          <label className={styles.checkboxLabel} title="Show lab logo on report">
                            <input type="checkbox" checked={templateForm.config.show_logo} onChange={(e) => updateTemplateConfig('show_logo', e.target.checked)} />
                            Show logo
                          </label>
                          <label className={styles.checkboxLabel} title="Show header image">
                            <input type="checkbox" checked={templateForm.config.show_header_image} onChange={(e) => updateTemplateConfig('show_header_image', e.target.checked)} />
                            Show header image
                          </label>
                          <label className={styles.checkboxLabel} title="Show footer image">
                            <input type="checkbox" checked={templateForm.config.show_footer_image} onChange={(e) => updateTemplateConfig('show_footer_image', e.target.checked)} />
                            Show footer image
                          </label>
                          <label className={styles.checkboxLabel} title="Show disclaimer text">
                            <input type="checkbox" checked={templateForm.config.show_disclaimer} onChange={(e) => updateTemplateConfig('show_disclaimer', e.target.checked)} />
                            Show disclaimer
                          </label>
                          <label className={styles.checkboxLabel} title="Show signature block">
                            <input type="checkbox" checked={templateForm.config.show_signatures} onChange={(e) => updateTemplateConfig('show_signatures', e.target.checked)} />
                            Show signatures
                          </label>
                        </div>
                      )}

                      {selectedTemplateSection === 'compliance' && (
                        <div className={styles.formGroup}>
                          <p className={styles.templateHelp}>Enable/disable international-reporting fields.</p>
                          <div className={styles.formRow}>
                            <label className={styles.checkboxLabel} title="Add DOB to patient identity and header repeat">
                              <input type="checkbox" checked={templateForm.config.show_patient_dob ?? false} onChange={(e) => updateTemplateConfig('show_patient_dob', e.target.checked)} />
                              Show patient DOB with Age/Gender
                            </label>
                            <label className={styles.checkboxLabel} title="Repeat patient IDs in header of every page">
                              <input type="checkbox" checked={templateForm.config.repeat_patient_id_on_pages ?? false} onChange={(e) => updateTemplateConfig('repeat_patient_id_on_pages', e.target.checked)} />
                              Repeat patient IDs on every page
                            </label>
                          </div>
                          <div className={styles.formRow}>
                            <label className={styles.checkboxLabel} title="Show specimen type and collection time under each test">
                              <input type="checkbox" checked={templateForm.config.show_specimen_details ?? false} onChange={(e) => updateTemplateConfig('show_specimen_details', e.target.checked)} />
                              Show specimen details per result
                            </label>
                            <label className={styles.checkboxLabel} title="Show ordering provider line in patient block">
                              <input type="checkbox" checked={templateForm.config.show_ordering_provider ?? true} onChange={(e) => updateTemplateConfig('show_ordering_provider', e.target.checked)} />
                              Show ordering provider
                            </label>
                            <label className={styles.checkboxLabel} title="Show verified by line under demographics">
                              <input type="checkbox" checked={templateForm.config.show_verified_by_line ?? true} onChange={(e) => updateTemplateConfig('show_verified_by_line', e.target.checked)} />
                              Show verified-by line
                            </label>
                          </div>
                          <div className={styles.formRow}>
                            <label className={styles.checkboxLabel} title="Show method info (when available)">
                              <input type="checkbox" checked={templateForm.config.show_method_info ?? false} onChange={(e) => updateTemplateConfig('show_method_info', e.target.checked)} />
                              Show method info
                            </label>
                            <label className={styles.checkboxLabel} title="Show decision limits / critical limits">
                              <input type="checkbox" checked={templateForm.config.show_decision_limits ?? false} onChange={(e) => updateTemplateConfig('show_decision_limits', e.target.checked)} />
                              Show decision limits
                            </label>
                            <label className={styles.checkboxLabel} title="Highlight critical values">
                              <input type="checkbox" checked={templateForm.config.show_critical_annotations ?? false} onChange={(e) => updateTemplateConfig('show_critical_annotations', e.target.checked)} />
                              Show critical annotations
                            </label>
                          </div>
                          <div className={styles.formRow}>
                            <label className={styles.checkboxLabel} title="Show QC/quality statement in footer">
                              <input type="checkbox" checked={templateForm.config.show_qc_statement ?? false} onChange={(e) => updateTemplateConfig('show_qc_statement', e.target.checked)} />
                              Show QC statement
                            </label>
                            <label className={styles.checkboxLabel} title="Show confidentiality notice in footer">
                              <input type="checkbox" checked={templateForm.config.show_confidentiality_statement ?? false} onChange={(e) => updateTemplateConfig('show_confidentiality_statement', e.target.checked)} />
                              Show confidentiality notice
                            </label>
                            <label className={styles.checkboxLabel} title="Show banner when this is a revised report">
                              <input type="checkbox" checked={templateForm.config.show_revision_banner ?? false} onChange={(e) => updateTemplateConfig('show_revision_banner', e.target.checked)} />
                              Show revision banner
                            </label>
                          </div>
                        </div>
                      )}

                      {selectedTemplateSection === 'disclaimer' && (
                        <div className={styles.formGroup}>
                          <label title="Text shown as disclaimer on the report">Disclaimer text</label>
                          <textarea className={styles.textarea} rows={3} value={templateForm.disclaimer_text || ''} onChange={(e) => updateTemplateField('disclaimer_text', e.target.value)} />
                        </div>
                      )}

                      {selectedTemplateSection === 'signatories' && (
                        <div className={styles.formGroup}>
                          <label>Signatories (names and titles)</label>
                          {templateForm.signatories?.map((signatory, idx) => (
                            <div key={idx} className={styles.signatoryRow}>
                              <input className={styles.input} placeholder="Name" value={signatory.name} onChange={(e) => updateSignatory(idx, 'name', e.target.value)} />
                              <input className={styles.input} placeholder="Title" value={signatory.title} onChange={(e) => updateSignatory(idx, 'title', e.target.value)} />
                              <input className={styles.input} placeholder="Reg No" value={signatory.reg_no || ''} onChange={(e) => updateSignatory(idx, 'reg_no', e.target.value)} />
                              <button type="button" className={styles.removeButton} onClick={() => removeSignatory(idx)}>Remove</button>
                            </div>
                          ))}
                          <button type="button" className={styles.secondaryButton} onClick={addSignatory}>+ Add signatory</button>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className={styles.formActions}>
                    <button
                      type="button"
                      className={styles.secondaryButton}
                      onClick={() => { if (confirm('Are you sure you want to delete this template? This cannot be undone.')) deleteTemplateMutation.mutate(templateForm.id); }}
                      disabled={deleteTemplateMutation.isPending}
                      style={{ marginRight: 'auto', backgroundColor: '#fee2e2', color: '#b91c1c', border: '1px solid #fecaca' }}
                    >
                      {deleteTemplateMutation.isPending ? 'Deleting...' : 'Delete template'}
                    </button>
                    <button type="button" className={styles.secondaryButton} onClick={handleTemplateSaveDraft} disabled={updateTemplateMutation.isPending}>
                      Save draft
                    </button>
                    <button type="button" className={styles.submitButton} onClick={handleTemplatePublish} disabled={updateTemplateMutation.isPending}>
                      Publish
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab !== 'print' && (
            <div className={styles.formActions}>
              <button type="submit" className={styles.submitButton} disabled={updateMutation.isPending}>
                {updateMutation.isPending ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          )}
        </form>
      )}
    </div>
  );
}
