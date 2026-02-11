import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { patientApi } from '../../api/services';
import styles from './TopHeader.module.css';

export function TopHeader() {
    const { user, currentBranch, setCurrentBranch } = useAuth();
    const navigate = useNavigate();

    const [searchQuery, setSearchQuery] = useState('');
    const [results, setResults] = useState<any[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [showResults, setShowResults] = useState(false);
    const [branchMenuOpen, setBranchMenuOpen] = useState(false);

    const searchRef = useRef<HTMLDivElement>(null);
    const debounceRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
                setShowResults(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleSearch = (query: string) => {
        setSearchQuery(query);
        setShowResults(true);

        if (debounceRef.current) clearTimeout(debounceRef.current);

        if (query.trim().length < 2) {
            setResults([]);
            setIsSearching(false);
            return;
        }

        setIsSearching(true);
        debounceRef.current = setTimeout(async () => {
            try {
                const response = await patientApi.globalSearch(query);
                if (response.success) {
                    setResults(response.data);
                }
            } catch (err) {
                console.error("Search failed", err);
            } finally {
                setIsSearching(false);
            }
        }, 400);
    };

    const handleSelectPatient = (patientId: number) => {
        navigate(`/dashboard/patients/${patientId}`);
        setShowResults(false);
        setSearchQuery('');
    };

    const handleBranchClick = () => {
        if (user?.branch_memberships && user.branch_memberships.length > 1) {
            setBranchMenuOpen(!branchMenuOpen);
        }
    };

    const switchBranch = (branch: any) => {
        setCurrentBranch(branch);
        setBranchMenuOpen(false);
        navigate('/dashboard');
    };

    const branches = user?.branch_memberships?.map(m => m.branch) || [];

    return (
        <header className={styles.header}>
            <div className={styles.left}>
                {/* Branch Switcher */}
                <div style={{ position: 'relative' }}>
                    <div
                        className={`${styles.branchChip} ${branchMenuOpen ? styles.branchChipActive : ''}`}
                        onClick={handleBranchClick}
                        role="button"
                        tabIndex={0}
                    >
                        <span className={styles.branchCode}>{currentBranch?.code || '00'}</span>
                        <span>{currentBranch?.name || 'Loading...'}</span>
                        {currentBranch?.capability_mode === 'COLLECT_ONLY' && (
                            <span style={{ fontSize: '0.7em', color: '#ea580c', background: '#fff7ed', padding: '1px 4px', borderRadius: 4 }}>COLLECT ONLY</span>
                        )}
                        {branches.length > 1 && (
                            <span style={{ fontSize: '0.7em', marginLeft: 4 }}>▼</span>
                        )}
                    </div>

                    {branchMenuOpen && (
                        <div className={styles.branchMenu}>
                            {branches.map(b => (
                                <div
                                    key={b.id}
                                    className={styles.branchMenuItem}
                                    onClick={() => switchBranch(b)}
                                >
                                    <span>
                                        <span className={styles.branchCode} style={{ marginRight: 8 }}>{b.code}</span>
                                        {b.name}
                                    </span>
                                    {b.id === currentBranch?.id && <span>✓</span>}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <div className={styles.right}>
                {/* Global Search */}
                <div className={styles.searchContainer} ref={searchRef}>
                    <input
                        type="text"
                        className={styles.searchInput}
                        placeholder="Search MRN, Name, Mobile..."
                        value={searchQuery}
                        onChange={(e) => handleSearch(e.target.value)}
                        onFocus={() => { if (searchQuery) setShowResults(true); }}
                    />
                    {/* Simple SVG icon since lucide-react might not be there */}
                    <span className={styles.searchIcon}>
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    </span>

                    {showResults && searchQuery.length >= 2 && (
                        <div className={styles.searchResults}>
                            {isSearching ? (
                                <div style={{ padding: 12, color: '#64748b' }}>Searching...</div>
                            ) : results.length === 0 ? (
                                <div style={{ padding: 12, color: '#64748b' }}>No matches found</div>
                            ) : (
                                results.map(r => (
                                    <div
                                        key={r.id}
                                        className={styles.searchResultItem}
                                        onClick={() => handleSelectPatient(r.id)}
                                    >
                                        <div className={styles.patientName}>
                                            <span>{r.name}</span>
                                            <span className={styles.mrn}>{r.mrn}</span>
                                        </div>
                                        <div className={styles.patientDetails}>
                                            <span>{r.age}y / {r.gender}</span>
                                            <span>{r.mobile}</span>
                                            {r.last_visit_branch_code && (
                                                <span style={{ background: '#f1f5f9', padding: '0 4px', borderRadius: 4 }}>Last: {r.last_visit_branch_code}</span>
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
