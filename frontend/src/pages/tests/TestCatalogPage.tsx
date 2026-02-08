import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { laboratoryApi, referenceRangeApi } from '../../api/services';

import { useBranding } from '../../contexts/BrandingContext';
import { useAuth } from '../../contexts/AuthContext';
import { formatCurrency } from '../../utils/currency';
import type { CatalogAuditSummary, CatalogImportSummary } from '../../types';
import styles from './TestCatalogPage.module.css';

export default function TestCatalogPage() {
  const queryClient = useQueryClient();
  const { branding } = useBranding();
  const { user } = useAuth();
  const currency = branding?.currency || 'PKR';
  const isAdmin = user?.role === 'Admin';
  const isManager = user?.role === 'Manager';
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = (searchParams.get('tab') as 'tests' | 'panels' | 'parameters' | 'ranges') || 'tests';
  const setActiveTab = (tab: string) => setSearchParams({ tab });
  const [searchQuery, setSearchQuery] = useState('');
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null); // For edit/delete
  const [modalType, setModalType] = useState<'test' | 'panel' | 'parameter' | 'range' | null>(null);

  const [auditSummary, setAuditSummary] = useState<CatalogAuditSummary | null>(null);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [auditLoading, setAuditLoading] = useState(false);

  // Queries
  const { data: categoriesData } = useQuery({
    queryKey: ['test-categories'],
    queryFn: () => laboratoryApi.getCategories(),
  });

  const { data: testsData, isLoading: testsLoading } = useQuery({
    queryKey: ['tests', selectedCategory, searchQuery],
    queryFn: () => laboratoryApi.getTests({
      ...(selectedCategory && { category: selectedCategory }),
      ...(searchQuery && { search: searchQuery }),
    }),
  });

  const { data: panelsData, isLoading: panelsLoading } = useQuery({
    queryKey: ['panels', selectedCategory, searchQuery],
    queryFn: () => laboratoryApi.getPanels({
      ...(selectedCategory && { category: selectedCategory }),
      ...(searchQuery && { search: searchQuery }),
    }),
  });

  const { data: parametersData, isLoading: parametersLoading } = useQuery({
    queryKey: ['parameters', searchQuery],
    queryFn: () => laboratoryApi.getParameters({
      ...(searchQuery && { search: searchQuery }),
    }),
    enabled: activeTab === 'parameters',
  });

  const { data: rangesData, isLoading: rangesLoading } = useQuery({
    queryKey: ['reference-ranges', searchQuery],
    queryFn: () => referenceRangeApi.list({
      ...(searchQuery && { search: searchQuery }),
    }),
    enabled: activeTab === 'ranges',
  });

  const categories = categoriesData?.results || [];
  const tests = testsData?.results || [];
  const panels = panelsData?.results || [];
  const parameters = parametersData?.results || [];
  const ranges = rangesData?.results || [];

  // Handlers
  const handleExport = async () => {
    try {
      const blob = await laboratoryApi.exportCatalog();
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'LIMS_Catalog_Export.xlsx');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      console.error('Export failed', err);
      alert('Failed to export catalog');
    }
  };

  const handleAudit = async () => {
    setAuditLoading(true);
    setAuditError(null);
    try {
      const summary = await laboratoryApi.auditCatalog();
      setAuditSummary(summary);
    } catch (err) {
      console.error('Audit failed', err);
      setAuditError('Failed to run catalog audit');
    } finally {
      setAuditLoading(false);
    }
  };

  const handleEdit = (item: any, type: 'test' | 'panel' | 'parameter' | 'range') => {
    setSelectedItem(item);
    setModalType(type);
    setIsEditModalOpen(true);
  };

  const handleDelete = async (id: number, type: 'test' | 'panel' | 'parameter' | 'range') => {
    if (!window.confirm('Are you sure you want to delete this item?')) return;
    try {
      if (type === 'test') await laboratoryApi.deleteTest(id);
      if (type === 'panel') await laboratoryApi.deletePanel(id);
      if (type === 'parameter') await laboratoryApi.deleteParameter(id);
      if (type === 'range') await referenceRangeApi.delete(id);

      queryClient.invalidateQueries({ queryKey: [type === 'range' ? 'reference-ranges' : type + 's'] });
    } catch (err) {
      console.error('Delete failed', err);
      alert('Failed to delete item');
    }
  };

  const handleSave = async (data: any) => {
    try {
      const type = modalType!;
      const isEdit = !!selectedItem;
      // Some items use 'test_id' instead of 'id'
      const id = selectedItem?.id ?? selectedItem?.test_id;

      if (type === 'test') {
        if (isEdit) await laboratoryApi.updateTest(id, data);
        else await laboratoryApi.createTest(data);
      } else if (type === 'panel') {
        if (isEdit) await laboratoryApi.updatePanel(id, data);
        else await laboratoryApi.createPanel(data);
      } else if (type === 'parameter') {
        if (isEdit) await laboratoryApi.updateParameter(id, data);
        else await laboratoryApi.createParameter(data);
      } else if (type === 'range') {
        if (isEdit) await referenceRangeApi.update(id, data);
        else await referenceRangeApi.create(data);
      }

      setIsEditModalOpen(false);
      // Invalidate relevant queries
      if (type === 'range') {
        queryClient.invalidateQueries({ queryKey: ['reference-ranges'] });
      } else {
        queryClient.invalidateQueries({ queryKey: [type + 's'] });
      }

    } catch (err) {
      console.error('Save failed', err);
      alert('Failed to save item');
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Test Catalog</h1>
        {(isAdmin || isManager) && (
          <div className={styles.actions}>
            {isAdmin && (
              <>
                <button
                  onClick={() => {
                    setSelectedItem(null);
                    setModalType(activeTab === 'tests' ? 'test' : activeTab === 'panels' ? 'panel' : activeTab === 'parameters' ? 'parameter' : 'range');
                    setIsEditModalOpen(true);
                  }}
                  className={styles.actionButton}
                >
                  + Add {activeTab === 'tests' ? 'Test' : activeTab === 'panels' ? 'Panel' : activeTab === 'parameters' ? 'Parameter' : 'Range'}
                </button>
                <button onClick={handleExport} className={styles.secondaryButton}>
                  Export
                </button>
                <button onClick={() => setIsImportModalOpen(true)} className={styles.secondaryButton}>
                  Import
                </button>
              </>
            )}
            <button onClick={handleAudit} className={styles.secondaryButton}>
              Audit
            </button>
          </div>
        )}
      </div>

      <div className={styles.filters}>
        <div className={styles.categoryFilter}>
          <label>Category:</label>
          <select
            value={selectedCategory || ''}
            onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
            className={styles.select}
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.searchFilter}>
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
        </div>

        <div className={styles.tabButtons}>
          {(['tests', 'panels', 'parameters', 'ranges'] as const).map((tab) => (
            <button
              key={tab}
              className={activeTab === tab ? styles.activeTab : styles.tab}
              onClick={() => setActiveTab(tab)}
              style={{ textTransform: 'capitalize' }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.content}>
        {activeTab === 'tests' && (
          testsLoading ? <div className={styles.loading}>Loading tests...</div> : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Sample</th>
                  <th>Price</th>
                  <th>TAT (hrs)</th>
                  <th>Params</th>
                  <th>Last Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {tests.map((test) => (
                  <tr key={test.test_id}>
                    <td><span className={styles.code}>{test.test_code}</span></td>
                    <td>{test.test_name}</td>
                    <td>{test.category_name}</td>
                    <td>{test.sample_type}</td>
                    <td>{formatCurrency(test.price, currency)}</td>
                    <td>{test.turnaround_time}</td>
                    <td>{test.parameters?.length || 0}</td>
                    <td style={{ fontSize: '12px', color: '#64748b' }}>
                      {new Date().toLocaleDateString()} {/* Placeholder, using current date for now as updated_at might be missing in type */}
                    </td>
                    <td>
                      <div className={styles.rowActions}>
                        <button onClick={() => handleEdit(test, 'test')} className={styles.iconButton}>✎</button>
                        {isAdmin && <button onClick={() => handleDelete(test.test_id, 'test')} className={styles.iconButtonDelete}>🗑</button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )}

        {activeTab === 'panels' && (
          panelsLoading ? <div className={styles.loading}>Loading panels...</div> : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Sample</th>
                  <th>Price</th>
                  <th>TAT (hrs)</th>
                  <th>Tests</th>
                  <th>Last Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {panels.map((panel) => (
                  <tr key={panel.id}>
                    <td><span className={styles.code}>{panel.panel_code}</span></td>
                    <td>{panel.panel_name}</td>
                    <td>{panel.category_name}</td>
                    <td>{panel.sample_type}</td>
                    <td>{formatCurrency(panel.price, currency)}</td>
                    <td>{panel.turnaround_time}</td>
                    <td>{panel.tests?.length || 0}</td>
                    <td style={{ fontSize: '12px', color: '#64748b' }}>
                      {new Date().toLocaleDateString()}
                    </td>
                    <td>
                      <div className={styles.rowActions}>
                        <button onClick={() => handleEdit(panel, 'panel')} className={styles.iconButton}>✎</button>
                        {isAdmin && <button onClick={() => handleDelete(panel.id, 'panel')} className={styles.iconButtonDelete}>🗑</button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )}

        {activeTab === 'parameters' && (
          parametersLoading ? <div className={styles.loading}>Loading parameters...</div> : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Param ID</th>
                  <th>Name</th>
                  <th>Unit</th>
                  <th>Type</th>
                  <th>Last Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {parameters.map((param) => (
                  <tr key={param.id}>
                    <td><span className={styles.code}>{param.parameter}</span></td>
                    <td>{param.parameter_name}</td>
                    <td>{param.unit}</td>
                    <td>numeric</td>
                    <td style={{ fontSize: '12px', color: '#64748b' }}>-</td>
                    <td>
                      <div className={styles.rowActions}>
                        <button onClick={() => handleEdit(param, 'parameter')} className={styles.iconButton}>✎</button>
                        {isAdmin && <button onClick={() => handleDelete(param.id, 'parameter')} className={styles.iconButtonDelete}>🗑</button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )}

        {activeTab === 'ranges' && (
          rangesLoading ? <div className={styles.loading}>Loading ranges...</div> : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Test</th>
                  <th>Parameter</th>
                  <th>Gender</th>
                  <th>Age Range</th>
                  <th>Normal Range</th>
                  <th>Critical Range</th>
                  <th>Last Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {ranges.map((range) => (
                  <tr key={range.id}>
                    <td><span className={styles.code}>{range.test_code}</span> {range.test_name}</td>
                    <td>{range.parameter_name}</td>
                    <td>{range.gender}</td>
                    <td>
                      {range.age_min ?? 0} - {range.age_max ?? '∞'} yrs
                    </td>
                    <td>{range.reference_min} - {range.reference_max}</td>
                    <td>{range.critical_low} - {range.critical_high}</td>
                    <td style={{ fontSize: '12px', color: '#64748b' }}>
                      {new Date(range.effective_date).toLocaleDateString()}
                    </td>
                    <td>
                      <div className={styles.rowActions}>
                        <button onClick={() => handleEdit(range, 'range')} className={styles.iconButton}>✎</button>
                        {isAdmin && <button onClick={() => handleDelete(range.id, 'range')} className={styles.iconButtonDelete}>🗑</button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )}
      </div>

      {isEditModalOpen && modalType && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h2>{selectedItem ? 'Edit' : 'Add'} {modalType}</h2>
              <button onClick={() => setIsEditModalOpen(false)} className={styles.closeButton}>×</button>
            </div>
            <div className={styles.modalBody}>
              <GenericForm
                type={modalType}
                initialData={selectedItem}
                categories={categories}
                onSubmit={handleSave}
                onCancel={() => setIsEditModalOpen(false)}
              />
            </div>
          </div>
        </div>
      )}

      {isAdmin && isImportModalOpen && (
        <BulkImportModal
          onClose={() => setIsImportModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['tests'] });
            queryClient.invalidateQueries({ queryKey: ['test-categories'] });
            queryClient.invalidateQueries({ queryKey: ['panels'] });
            setIsImportModalOpen(false);
          }}
        />
      )}

      {auditSummary && (
        <div className={styles.auditPanel}>
          <h2>Catalog Audit Summary</h2>
          <div className={styles.auditGrid}>
            <div>
              <h4>Duplicates</h4>
              <p>Test Codes: {auditSummary.duplicates.test_code.count}</p>
              <p>Parameter Codes: {auditSummary.duplicates.parameter_code.count}</p>
            </div>
            <div>
              <h4>Missing/Invalid</h4>
              <p>Tests w/ No Params: {auditSummary.tests_without_parameters.count}</p>
              <p>Missing Ranges: {auditSummary.reference_ranges.missing.count}</p>
              <p>Invalid Ranges: {auditSummary.reference_ranges.invalid.count}</p>
            </div>
            <div>
              <h4>Defaults</h4>
              <p>Sample Type Serum: {auditSummary.suspicious_defaults.sample_type_serum.count}</p>
              <p>Price Zero: {auditSummary.suspicious_defaults.price_zero.count}</p>
              <p>TAT 24h: {auditSummary.suspicious_defaults.turnaround_time_24.count}</p>
            </div>
            <div>
              <h4>Panels</h4>
              <p>Panels w/ No Tests: {auditSummary.panels_without_tests.count}</p>
            </div>
          </div>
        </div>
      )}
      {auditLoading && <div className={styles.loading}>Running audit...</div>}
      {auditError && <div className={styles.error}>{auditError}</div>}
    </div>
  );
}

interface GenericFormProps {
  type: 'test' | 'panel' | 'parameter' | 'range';
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  initialData?: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  categories: any[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSubmit: (data: any) => void;
  onCancel: () => void;
}

function GenericForm({ type, initialData, categories, onSubmit, onCancel }: GenericFormProps) {
  const [formData, setFormData] = useState(initialData || {});

  // For ranges, we might need parameters/tests list if it was available.
  // Given we didn't pass it, we'll use simple inputs for now or mocked selects.

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleChange = (field: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
  };

  type FieldConfig = {
    name: string;
    label: string;
    type: string; // 'text' | 'number' | 'select'
    options?: { value: string | number; label: string }[];
    placeholder?: string;
  };

  const fields: Record<string, FieldConfig[]> = {
    test: [
      { name: 'test_code', label: 'Test Code', type: 'text' },
      { name: 'test_name', label: 'Test Name', type: 'text' },
      { name: 'category', label: 'Category', type: 'select', options: categories.map((c: any) => ({ value: c.id, label: c.name })) },
      { name: 'sample_type', label: 'Sample Type', type: 'text' },
      { name: 'price', label: 'Price', type: 'number' },
      { name: 'turnaround_time', label: 'TAT (Hours)', type: 'number' },
    ],
    panel: [
      { name: 'panel_code', label: 'Panel Code', type: 'text' },
      { name: 'panel_name', label: 'Panel Name', type: 'text' },
      { name: 'category', label: 'Category', type: 'select', options: categories.map((c: any) => ({ value: c.id, label: c.name })) },
      { name: 'sample_type', label: 'Sample Type', type: 'text' },
      { name: 'price', label: 'Price', type: 'number' },
      { name: 'turnaround_time', label: 'TAT (Hours)', type: 'number' },
    ],
    parameter: [
      { name: 'parameter', label: 'Parameter ID', type: 'text', placeholder: 'p123' },
      { name: 'parameter_name', label: 'Parameter Name', type: 'text' },
      { name: 'unit', label: 'Unit', type: 'text' },
      { name: 'decimal_places', label: 'Decimal Places', type: 'number' },
    ],
    range: [
      // Needs Test/Parameter ID. For simplicity, we ask for Parameter ID manually if creating new 
      // or assume it's pre-filled if we had better context. 
      // Ideally this needs a searchable select.
      { name: 'parameter', label: 'Parameter ID (Test Parameter ID)', type: 'number' },
      { name: 'gender', label: 'Gender', type: 'select', options: [{ value: 'Male', label: 'Male' }, { value: 'Female', label: 'Female' }, { value: 'Both', label: 'Both' }] },
      { name: 'age_min', label: 'Age Min', type: 'number' },
      { name: 'age_max', label: 'Age Max', type: 'number' },
      { name: 'reference_min', label: 'Normal Min', type: 'number' },
      { name: 'reference_max', label: 'Normal Max', type: 'number' },
      { name: 'critical_low', label: 'Critical Low', type: 'number' },
      { name: 'critical_high', label: 'Critical High', type: 'number' },
    ]
  };

  const currentFields = fields[type];

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(formData); }}>
      {currentFields.map((field) => (
        <div key={field.name} className={styles.formGroup} style={{ marginBottom: '12px' }}>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>{field.label}</label>
          {field.type === 'select' ? (
            <select
              value={formData[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              className={styles.select}
              style={{ width: '100%' }}
            >
              <option value="">Select...</option>
              {field.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              type={field.type}
              value={formData[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              placeholder={field.placeholder}
              className={styles.input}
              style={{ width: '100%', padding: '8px', border: '1px solid #e2e8f0', borderRadius: '4px' }}
            />
          )}
        </div>
      ))}
      <div className={styles.modalActions}>
        <button type="button" onClick={onCancel} className={styles.cancelButton}>
          Cancel
        </button>
        <button type="submit" className={styles.submitButton}>
          Save
        </button>
      </div>
    </form>
  );
}

interface BulkImportModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

function BulkImportModal({ onClose, onSuccess }: BulkImportModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [validationSummary, setValidationSummary] = useState<CatalogImportSummary | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [validationErrors, setValidationErrors] = useState<any[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [validationWarnings, setValidationWarnings] = useState<any[]>([]);
  const [strict, setStrict] = useState(true);
  const [allowDefaults, setAllowDefaults] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
      setValidationErrors([]);
      setValidationWarnings([]);
      setValidationSummary(null);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const blob = await laboratoryApi.downloadImportTemplate();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'LIMS_Import_Template.xlsx');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      console.error("Failed to download template", err);
      setError("Failed to download template");
    }
  };

  const handleValidate = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setValidationErrors([]);
    setValidationWarnings([]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const data = await laboratoryApi.importCatalog(file, {
        strict,
        allow_defaults: allowDefaults,
        mode: 'upsert',
        dry_run: true,
      });
      setValidationSummary(data.summary);
      setValidationErrors(data.summary.errors || []);
      setValidationWarnings(data.summary.warnings || []);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string; error?: string; summary?: { errors?: unknown[]; warnings?: unknown[] } } } };
      const errorData = error.response?.data;
      setError(errorData?.message || errorData?.error || "Failed to upload file");

      if (errorData?.summary?.errors) {
        setValidationErrors(errorData.summary.errors);
        setValidationWarnings(errorData.summary.warnings || []);
        setValidationSummary(errorData.summary as CatalogImportSummary);
      }
    } finally {
      setUploading(false);
    }
  };

  const handleApply = async () => {
    if (!file || !validationSummary) return;
    setUploading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      await laboratoryApi.importCatalog(file, {
        strict,
        allow_defaults: allowDefaults,
        mode: 'upsert',
        dry_run: false,
      });
      setSuccessMessage('Import applied');
      setTimeout(() => onSuccess(), 1200);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string; error?: string; summary?: { errors?: unknown[] } } } };
      const errorData = error.response?.data;
      setError(errorData?.message || errorData?.error || 'Import failed');
      if (errorData?.summary?.errors) {
        setValidationErrors(errorData.summary.errors);
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h2>Bulk Import Tests</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <div className={styles.modalBody}>
          <div className={styles.templateSection}>
            <p>Need a starting point? Download the Excel template.</p>
            <button onClick={handleDownloadTemplate} className={styles.secondaryButton}>
              Download Template
            </button>
          </div>

          <div className={styles.uploadSection}>
            <p>Upload an Excel file (.xlsx) containing "Tests", "Parameters", "Mapping", and "ReferenceRanges" sheets.</p>

            <div className={styles.dropZone}>
              <input
                type="file"
                accept=".xlsx"
                onChange={handleFileChange}
                disabled={uploading}
              />
            </div>

            {file && <p className={styles.fileName}>Selected file: {file.name}</p>}
          </div>

          <div className={styles.optionsRow}>
            <label>
              <input type="checkbox" checked={strict} onChange={(e) => setStrict(e.target.checked)} />
              Strict (required fields enforced)
            </label>
            <label>
              <input type="checkbox" checked={allowDefaults} onChange={(e) => setAllowDefaults(e.target.checked)} />
              Allow defaults
            </label>
          </div>

          {error && <div className={styles.error}>{error}</div>}

          {validationErrors.length > 0 && (
            <div className={styles.validationErrors}>
              <h4>Validation Errors:</h4>
              <ul>
                {validationErrors.slice(0, 10).map((err, idx) => (
                  <li key={idx}>
                    Sheet <strong>{err.sheet}</strong>, Row <strong>{err.row}</strong>, Field <strong>{err.field}</strong>: {err.message}
                  </li>
                ))}
                {validationErrors.length > 10 && <li>...and {validationErrors.length - 10} more errors</li>}
              </ul>
            </div>
          )}

          {validationWarnings.length > 0 && (
            <div className={styles.validationWarnings}>
              <h4>Warnings:</h4>
              <ul>
                {validationWarnings.slice(0, 10).map((warn, idx) => (
                  <li key={idx}>
                    Sheet <strong>{warn.sheet}</strong>, Row <strong>{warn.row}</strong>, Field <strong>{warn.field}</strong>: {warn.message}
                  </li>
                ))}
                {validationWarnings.length > 10 && <li>...and {validationWarnings.length - 10} more warnings</li>}
              </ul>
            </div>
          )}

          {validationSummary && (
            <div className={styles.summaryBox}>
              <h4>Diff Summary</h4>
              <div className={styles.summaryGrid}>
                {Object.entries(validationSummary.counts).map(([key, counts]) => (
                  <div key={key}>
                    <strong>{key}</strong>
                    <div>Created: {counts.created}</div>
                    <div>Updated: {counts.updated}</div>
                    <div>Unchanged: {counts.unchanged}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {successMessage && <div className={styles.success}>{successMessage}</div>}

          <div className={styles.modalActions}>
            <button onClick={onClose} disabled={uploading} className={styles.cancelButton}>
              Cancel
            </button>
            <button
              onClick={handleValidate}
              disabled={!file || uploading}
              className={styles.submitButton}
            >
              {uploading ? "Validating..." : "Validate"}
            </button>
            <button
              onClick={handleApply}
              disabled={!file || uploading || (validationErrors.length > 0) || !validationSummary}
              className={styles.actionButton}
            >
              {uploading ? "Applying..." : "Apply"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
