import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { laboratoryApi } from '../../api/services';

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
  const [activeTab, setActiveTab] = useState<'tests' | 'panels'>('tests');
  const [searchQuery, setSearchQuery] = useState('');
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [auditSummary, setAuditSummary] = useState<CatalogAuditSummary | null>(null);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [auditLoading, setAuditLoading] = useState(false);

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

  const categories = categoriesData?.results || [];
  const tests = testsData?.results || [];
  const panels = panelsData?.results || [];

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

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Test Catalog</h1>
        {(isAdmin || isManager) && (
          <div className={styles.actions}>
            {isAdmin && (
              <>
                <button onClick={handleExport} className={styles.secondaryButton}>
                  Export Catalog
                </button>
                <button onClick={() => setIsImportModalOpen(true)} className={styles.actionButton}>
                  Import Catalog
                </button>
              </>
            )}
            <button onClick={handleAudit} className={styles.secondaryButton}>
              Audit Catalog
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
            placeholder="Search tests or panels..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
        </div>

        <div className={styles.tabButtons}>
          <button
            className={activeTab === 'tests' ? styles.activeTab : styles.tab}
            onClick={() => setActiveTab('tests')}
          >
            Tests
          </button>
          <button
            className={activeTab === 'panels' ? styles.activeTab : styles.tab}
            onClick={() => setActiveTab('panels')}
          >
            Panels
          </button>
        </div>
      </div>

      {activeTab === 'tests' ? (
        <div className={styles.content}>
          {testsLoading ? (
            <div className={styles.loading}>Loading tests...</div>
          ) : (
            <div className={styles.grid}>
              {tests.map((test) => (
                <div key={test.test_id} className={styles.card}>
                  <div className={styles.cardHeader}>
                    <h3>{test.test_name}</h3>
                    <span className={styles.code}>{test.test_code}</span>
                  </div>
                  <div className={styles.cardBody}>
                    <p className={styles.category}>{test.category_name}</p>
                    <p><strong>Sample:</strong> {test.sample_type}</p>
                    {test.sample_volume && (
                      <p><strong>Volume:</strong> {test.sample_volume}</p>
                    )}
                    <p><strong>Price:</strong> {formatCurrency(test.price, currency)}</p>
                    <p><strong>Turnaround:</strong> {test.turnaround_time} hours</p>
                    {test.parameters && test.parameters.length > 0 && (
                      <div className={styles.parameters}>
                        <strong>Parameters ({test.parameters.length}):</strong>
                        <ul>
                          {test.parameters.slice(0, 3).map((param) => (
                            <li key={param.id}>{param.parameter_name}</li>
                          ))}
                          {test.parameters.length > 3 && (
                            <li>+{test.parameters.length - 3} more</li>
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {tests.length === 0 && (
                <div className={styles.noData}>No tests found</div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className={styles.content}>
          {panelsLoading ? (
            <div className={styles.loading}>Loading panels...</div>
          ) : (
            <div className={styles.grid}>
              {panels.map((panel) => (
                <div key={panel.id} className={styles.card}>
                  <div className={styles.cardHeader}>
                    <h3>{panel.panel_name}</h3>
                    <span className={styles.code}>{panel.panel_code}</span>
                  </div>
                  <div className={styles.cardBody}>
                    <p className={styles.category}>{panel.category_name}</p>
                    <p><strong>Sample:</strong> {panel.sample_type}</p>
                    {panel.sample_volume && (
                      <p><strong>Volume:</strong> {panel.sample_volume}</p>
                    )}
                    <p><strong>Price:</strong> {formatCurrency(panel.price, currency)}</p>
                    <p><strong>Turnaround:</strong> {panel.turnaround_time} hours</p>
                    {panel.tests && panel.tests.length > 0 && (
                      <div className={styles.parameters}>
                        <strong>Tests ({panel.tests.length}):</strong>
                        <ul>
                          {panel.tests.slice(0, 3).map((test) => (
                            <li key={test.test_id}>{test.test_name}</li>
                          ))}
                          {panel.tests.length > 3 && (
                            <li>+{panel.tests.length - 3} more</li>
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {panels.length === 0 && (
                <div className={styles.noData}>No panels found</div>
              )}
            </div>
          )}
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
