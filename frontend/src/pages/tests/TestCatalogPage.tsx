import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { laboratoryApi } from '../../api/services';
import styles from './TestCatalogPage.module.css';

export default function TestCatalogPage() {
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'tests' | 'panels'>('tests');
  const [searchQuery, setSearchQuery] = useState('');

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
    </div>
  );
}
