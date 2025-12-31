import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { laboratoryApi } from '../../api/services';
import api from '../../api/client';
import styles from './TestCatalogPage.module.css';

export default function TestCatalogPage() {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'tests' | 'panels'>('tests');
  const [searchQuery, setSearchQuery] = useState('');
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

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

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Test Catalog</h1>
        <div className={styles.actions}>
           <button onClick={() => setIsImportModalOpen(true)} className={styles.actionButton}>
             Import Excel
           </button>
        </div>
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
                <div key={test.id} className={styles.card}>
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
                    <p><strong>Price:</strong> ${test.price}</p>
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
                    <p><strong>Price:</strong> ${panel.price}</p>
                    <p><strong>Turnaround:</strong> {panel.turnaround_time} hours</p>
                    {panel.tests && panel.tests.length > 0 && (
                      <div className={styles.parameters}>
                        <strong>Tests ({panel.tests.length}):</strong>
                        <ul>
                          {panel.tests.slice(0, 3).map((test) => (
                            <li key={test.id}>{test.test_name}</li>
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

      {isImportModalOpen && (
        <BulkImportModal
          onClose={() => setIsImportModalOpen(false)}
          onSuccess={() => {
              queryClient.invalidateQueries({ queryKey: ['tests'] });
              queryClient.invalidateQueries({ queryKey: ['test-categories'] });
              setIsImportModalOpen(false);
          }}
        />
      )}
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

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await api.post('/laboratory/import/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            setSuccessMessage(response.data.message);
            setTimeout(() => {
                onSuccess();
            }, 1500);
        } catch (err: any) {
            setError(err.response?.data?.error || "Failed to upload file");
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
                    <p>Upload an Excel file (.xlsx) containing "Tests", "Parameters", and "ReferenceRanges" sheets.</p>

                    <div className={styles.dropZone}>
                        <input
                            type="file"
                            accept=".xlsx"
                            onChange={handleFileChange}
                            disabled={uploading}
                        />
                    </div>

                    {file && <p>Selected file: {file.name}</p>}

                    {error && <div className={styles.error}>{error}</div>}
                    {successMessage && <div className={styles.success}>{successMessage}</div>}

                    <div className={styles.modalActions}>
                        <button onClick={onClose} disabled={uploading} className={styles.cancelButton}>
                            Cancel
                        </button>
                        <button
                            onClick={handleUpload}
                            disabled={!file || uploading}
                            className={styles.submitButton}
                        >
                            {uploading ? "Uploading..." : "Import"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
