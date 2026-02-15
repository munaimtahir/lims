import { useState, useEffect, useRef } from 'react';
import type { KeyboardEvent } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { patientApi, laboratoryApi, tenantSettingsApi } from '../../api/services';
import type { PatientLookupResult } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { normalizeDobInput, formatDobDisplay } from '../../utils/dateFormat';
import styles from './RegistrationPage.module.css';

interface FormErrors {
    [key: string]: string;
}

export default function RegistrationPage() {
    const navigate = useNavigate();
    const { currentBranch, user } = useAuth();

    // Refs for focus management
    const firstNameRef = useRef<HTMLInputElement>(null);
    const mobileRef = useRef<HTMLInputElement>(null);

    // High Volume Lab Optimization Toggle
    const [quickMode, setQuickMode] = useState(false);

    // Form State
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        gender: 'Male',
        phone: '', // Mobile
        whatsapp_number: '', // Alternate Mobile
        email: '',
        address: '',
        referred_by: '',
        consultant: '',
        category: '',
        mr_number: '',
        registration_center: currentBranch?.id || '',
    });

    // Age/DOB State
    const [dobInput, setDobInput] = useState('');
    const [ageYears, setAgeYears] = useState<number>(0);
    const [ageMonths, setAgeMonths] = useState<number>(0);
    const [ageDays, setAgeDays] = useState<number>(0);
    const [ageInput, setAgeInput] = useState('');

    const [errors, setErrors] = useState<FormErrors>({});

    // Patient Lookup State
    const [patientSuggestions, setPatientSuggestions] = useState<PatientLookupResult[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [suggestionIndex, setSuggestionIndex] = useState(-1);
    const [isSearching, setIsSearching] = useState(false);

    // Fetch Categories for Section 3
    const { data: categoriesData } = useQuery({
        queryKey: ['test-categories'],
        queryFn: () => laboratoryApi.getCategories(),
    });

    // Tenant settings: when enable_collection_centers is OFF, do not send registration_center/branch
    const { data: tenantSettings } = useQuery({
        queryKey: ['tenant-settings'],
        queryFn: () => tenantSettingsApi.get(),
        staleTime: 60_000,
    });
    const enableCollectionCenters = tenantSettings?.enable_collection_centers ?? false;

    // Focus First Name on Load
    useEffect(() => {
        firstNameRef.current?.focus();
    }, []);

    // Update branch if it changes (only used when enable_collection_centers is true)
    useEffect(() => {
        if (enableCollectionCenters && currentBranch) {
            setFormData(prev => ({ ...prev, registration_center: currentBranch.id }));
        }
    }, [enableCollectionCenters, currentBranch]);

    // --- AGE / DOB SYNC ---
    const handleDobChange = (value: string) => {
        const normalized = normalizeDobInput(value);
        const display = normalized.display || value;
        const date = normalized.date;

        setDobInput(display);

        if (date) {
            const today = new Date();
            let years = today.getFullYear() - date.getFullYear();
            let months = today.getMonth() - date.getMonth();
            let days = today.getDate() - date.getDate();

            if (days < 0) {
                months--;
                const prevMonth = new Date(today.getFullYear(), today.getMonth(), 0);
                days += prevMonth.getDate();
            }
            if (months < 0) {
                years--;
                months += 12;
            }

            const y = Math.max(0, years);
            const m = Math.max(0, months);
            const d = Math.max(0, days);

            setAgeYears(y);
            setAgeMonths(m);
            setAgeDays(d);

            let ageStr = '';
            if (y > 0) ageStr += `${y}y `;
            if (m > 0) ageStr += `${m}m `;
            if (d > 0) ageStr += `${d}d`;
            setAgeInput(ageStr.trim() || '0d');
        }
    };

    const parseAge = (str: string) => {
        let y = 0, m = 0, d = 0;
        const lower = str.toLowerCase().trim();
        if (!lower) return { y: 0, m: 0, d: 0 };

        if (/^\d+$/.test(lower)) {
            y = parseInt(lower);
        } else {
            const yMatch = lower.match(/(\d+)\s*y/);
            const mMatch = lower.match(/(\d+)\s*m/);
            const dMatch = lower.match(/(\d+)\s*d/);
            if (yMatch) y = parseInt(yMatch[1]);
            if (mMatch) m = parseInt(mMatch[1]);
            if (dMatch) d = parseInt(dMatch[1]);
        }
        return { y, m, d };
    };

    const handleAgeBlur = () => {
        const { y, m, d } = parseAge(ageInput);
        setAgeYears(y);
        setAgeMonths(m);
        setAgeDays(d);

        const date = new Date();
        date.setFullYear(date.getFullYear() - y);
        date.setMonth(date.getMonth() - m);
        date.setDate(date.getDate() - d);

        const yyyy = date.getFullYear();
        const mm = String(date.getMonth() + 1).padStart(2, '0');
        const dd = String(date.getDate()).padStart(2, '0');
        setDobInput(formatDobDisplay(`${yyyy}-${mm}-${dd}`));

        let ageStr = '';
        if (y > 0) ageStr += `${y}y `;
        if (m > 0) ageStr += `${m}m `;
        if (d > 0) ageStr += `${d}d`;
        setAgeInput(ageStr.trim() || (y === 0 && m === 0 && d === 0 ? '' : ageInput));
    };

    // --- SEARCH ---
    useEffect(() => {
        if (formData.phone.length >= 3) {
            setIsSearching(true);
            const timer = setTimeout(async () => {
                try {
                    const res = await patientApi.lookup(formData.phone);
                    setPatientSuggestions(res.data);
                    setShowSuggestions(res.data.length > 0);
                    setSuggestionIndex(res.data.length > 0 ? 0 : -1);
                } catch (e) {
                    // ignore
                } finally {
                    setIsSearching(false);
                }
            }, 300);
            return () => clearTimeout(timer);
        } else {
            setPatientSuggestions([]);
            setShowSuggestions(false);
            setSuggestionIndex(-1);
        }
    }, [formData.phone]);

    const selectPatient = (patient: any) => {
        navigate(`/dashboard/orders/create?patient_id=${patient.id}`);
    };

    // --- SUBMISSION ---
    const saveMutation = useMutation({
        mutationFn: (data: any) => patientApi.create(data),
        onSuccess: (res) => {
            navigate(`/dashboard/orders/create?patient_id=${res.data.id}`);
        },
        onError: (err: any) => {
            const data = err?.response?.data;
            const newErrors: FormErrors = {};
            if (data) {
                Object.keys(data).forEach(key => {
                    newErrors[key] = Array.isArray(data[key]) ? data[key].join(' ') : String(data[key]);
                });
            }
            if (Object.keys(newErrors).length === 0) {
                newErrors['global'] = "System error occurred. Please try again.";
            }
            setErrors(newErrors);

            const firstField = Object.keys(newErrors)[0];
            if (firstField) {
                const el = document.getElementById(`field-${firstField}`);
                if (el) el.focus();
            }
        }
    });

    const handleSubmit = (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        const newErrors: FormErrors = {};
        if (!formData.first_name) newErrors['first_name'] = 'Required';
        if (!formData.phone) newErrors['phone'] = 'Required';

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            return;
        }

        const payload: Record<string, unknown> = {
            ...formData,
            full_name: `${formData.first_name} ${formData.last_name || ''}`.trim(),
            date_of_birth: normalizeDobInput(dobInput).iso,
            age_years: ageYears,
            age_months: ageMonths,
            age_days: ageDays,
            default_referred_by: formData.referred_by || formData.consultant, // mapping
        };
        // When collection centers OFF: do not send registration_center or branch (backend ignores invalid values)
        if (!enableCollectionCenters) {
            delete payload.registration_center;
            delete payload.branch;
        } else {
            // When ON: send branch (Branch id); do NOT send Branch id as registration_center
            if (formData.registration_center) {
                payload.branch = Number(formData.registration_center);
            }
            delete payload.registration_center;
        }

        saveMutation.mutate(payload as any);
    };

    // --- KEYBOARD NAV ---
    const handleKeyDown = (e: KeyboardEvent, nextId?: string) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (nextId) {
                const el = document.getElementById(nextId);
                if (el) el.focus();
            } else {
                handleSubmit();
            }
        }
    };

    const handleMobileKeyDown = (e: KeyboardEvent) => {
        if (showSuggestions) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSuggestionIndex(prev => Math.min(prev + 1, patientSuggestions.length - 1));
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSuggestionIndex(prev => Math.max(prev - 1, 0));
            } else if (e.key === 'Enter' && suggestionIndex >= 0) {
                e.preventDefault();
                selectPatient(patientSuggestions[suggestionIndex]);
                return;
            }
        }

        if (e.key === 'Enter') {
            e.preventDefault();
            // In Quick Mode, after mobile we might skip to save or go to next visible field
            const nextId = quickMode ? 'field-submit' : 'field-whatsapp';
            const el = document.getElementById(nextId);
            if (el) el.focus();
        }
    };

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div>
                    <h1>Patient Registration</h1>
                    <p className={styles.subtitle}>Keyboard-friendly laboratory workflow</p>
                </div>
                <div className={styles.modeToggle}>
                    <label className={styles.switch}>
                        <input
                            type="checkbox"
                            checked={quickMode}
                            onChange={() => setQuickMode(!quickMode)}
                        />
                        <span className={styles.slider}></span>
                    </label>
                    <span className={styles.modeLabel}>Quick Mode</span>
                </div>
            </header>

            {errors['global'] && <div className={styles.errorBanner}>{errors['global']}</div>}

            <div className={styles.formContainer}>
                {/* SECTION 1: IDENTITY */}
                <section className={styles.section}>
                    <h3 className={styles.sectionTitle}>1. Patient Identity</h3>
                    <div className={styles.row}>
                        <div className={styles.fieldGroup}>
                            <label>First Name <span className={styles.required}>*</span></label>
                            <input
                                id="field-first_name"
                                ref={firstNameRef}
                                type="text"
                                value={formData.first_name}
                                onChange={e => setFormData({ ...formData, first_name: e.target.value })}
                                onKeyDown={e => handleKeyDown(e, quickMode ? 'field-gender' : 'field-last_name')}
                                className={errors['first_name'] ? styles.errorInput : ''}
                                autoComplete="off"
                            />
                            {errors['first_name'] && <span className={styles.errorMsg}>{errors['first_name']}</span>}
                        </div>
                        {!quickMode && (
                            <div className={styles.fieldGroup}>
                                <label>Last Name</label>
                                <input
                                    id="field-last_name"
                                    type="text"
                                    value={formData.last_name}
                                    onChange={e => setFormData({ ...formData, last_name: e.target.value })}
                                    onKeyDown={e => handleKeyDown(e, 'field-gender')}
                                    autoComplete="off"
                                />
                            </div>
                        )}
                        <div className={styles.fieldGroup}>
                            <label>Gender</label>
                            <select
                                id="field-gender"
                                value={formData.gender}
                                onChange={e => setFormData({ ...formData, gender: e.target.value as any })}
                                onKeyDown={e => handleKeyDown(e, 'field-age')}
                            >
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                    </div>

                    <div className={styles.row}>
                        <div className={styles.fieldGroup} style={{ flex: 1.5 }}>
                            <label>Age (e.g. 25, 25y, 2m)</label>
                            <input
                                id="field-age"
                                type="text"
                                autoComplete="off"
                                value={ageInput}
                                onChange={e => setAgeInput(e.target.value)}
                                onBlur={handleAgeBlur}
                                onKeyDown={e => handleKeyDown(e, 'field-dob')}
                                placeholder="Years, Months, Days"
                            />
                        </div>
                        <div className={styles.fieldGroup}>
                            <label>Date of Birth</label>
                            <input
                                id="field-dob"
                                type="text"
                                placeholder="DD/MM/YYYY"
                                value={dobInput}
                                onChange={e => handleDobChange(e.target.value)}
                                onKeyDown={e => handleKeyDown(e, 'field-phone')}
                                autoComplete="off"
                            />
                        </div>
                    </div>
                </section>

                {/* SECTION 2: CONTACT */}
                <section className={styles.section}>
                    <h3 className={styles.sectionTitle}>2. Contact</h3>
                    <div className={styles.row}>
                        <div className={styles.fieldGroup} style={{ position: 'relative' }}>
                            <label>Mobile <span className={styles.required}>*</span></label>
                            <input
                                id="field-phone"
                                ref={mobileRef}
                                type="text"
                                value={formData.phone}
                                onChange={e => setFormData({ ...formData, phone: e.target.value })}
                                onKeyDown={handleMobileKeyDown}
                                className={errors['phone'] ? styles.errorInput : ''}
                                autoComplete="off"
                            />
                            {isSearching && <div className={styles.loadingSpinner}></div>}
                            {showSuggestions && (
                                <div className={styles.suggestions}>
                                    {patientSuggestions.map((p, idx) => (
                                        <div
                                            key={p.id}
                                            className={`${styles.suggestionItem} ${idx === suggestionIndex ? styles.active : ''}`}
                                            onClick={() => selectPatient(p)}
                                        >
                                            <div className={styles.suggestionMain}>
                                                <strong>{p.full_name}</strong>
                                                <span>{p.phone}</span>
                                            </div>
                                            <div className={styles.suggestionMeta}>
                                                {p.gender} • {p.age}Y • Reg: {p.registration_number || p.patient_id}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {errors['phone'] && <span className={styles.errorMsg}>{errors['phone']}</span>}
                        </div>
                        {!quickMode && (
                            <div className={styles.fieldGroup}>
                                <label>Alternate Mobile</label>
                                <input
                                    id="field-whatsapp"
                                    type="text"
                                    value={formData.whatsapp_number}
                                    onChange={e => setFormData({ ...formData, whatsapp_number: e.target.value })}
                                    onKeyDown={e => handleKeyDown(e, 'field-address')}
                                    autoComplete="off"
                                />
                            </div>
                        )}
                    </div>
                    {!quickMode && (
                        <div className={styles.row}>
                            <div className={styles.fieldGroupFull}>
                                <label>Address</label>
                                <textarea
                                    id="field-address"
                                    value={formData.address}
                                    onChange={e => setFormData({ ...formData, address: e.target.value })}
                                    onKeyDown={e => handleKeyDown(e, 'field-referred_by')}
                                    className={styles.expandableTextarea}
                                    rows={1}
                                />
                            </div>
                        </div>
                    )}
                </section>

                {/* SECTION 3: ADMINISTRATIVE */}
                {!quickMode && (
                    <section className={styles.section}>
                        <h3 className={styles.sectionTitle}>3. Lab Administrative</h3>
                        <div className={styles.row}>
                            {enableCollectionCenters && (
                                <div className={styles.fieldGroup}>
                                    <label>Collection center (branch)</label>
                                    <select
                                        id="field-branch"
                                        value={formData.registration_center}
                                        onChange={e => setFormData({ ...formData, registration_center: e.target.value })}
                                        onKeyDown={e => handleKeyDown(e, 'field-referred_by')}
                                    >
                                        {user?.branch_memberships?.map(m => (
                                            <option key={m.branch.id} value={m.branch.id}>
                                                {m.branch.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            )}
                            <div className={styles.fieldGroup}>
                                <label>Referred By</label>
                                <input
                                    id="field-referred_by"
                                    type="text"
                                    value={formData.referred_by}
                                    onChange={e => setFormData({ ...formData, referred_by: e.target.value })}
                                    onKeyDown={e => handleKeyDown(e, 'field-consultant')}
                                    autoComplete="off"
                                />
                            </div>
                        </div>
                        <div className={styles.row}>
                            <div className={styles.fieldGroup}>
                                <label>Consultant</label>
                                <input
                                    id="field-consultant"
                                    type="text"
                                    value={formData.consultant}
                                    onChange={e => setFormData({ ...formData, consultant: e.target.value })}
                                    onKeyDown={e => handleKeyDown(e, 'field-category')}
                                    autoComplete="off"
                                />
                            </div>
                            <div className={styles.fieldGroup}>
                                <label>Category</label>
                                <select
                                    id="field-category"
                                    value={formData.category}
                                    onChange={e => setFormData({ ...formData, category: e.target.value })}
                                    onKeyDown={e => handleKeyDown(e, 'field-mr_number')}
                                >
                                    <option value="">Standard</option>
                                    {categoriesData?.results.map(c => (
                                        <option key={c.id} value={c.id}>{c.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className={styles.fieldGroup}>
                                <label>MR Number</label>
                                <input
                                    id="field-mr_number"
                                    type="text"
                                    value={formData.mr_number}
                                    onChange={e => setFormData({ ...formData, mr_number: e.target.value })}
                                    onKeyDown={e => handleKeyDown(e, 'field-submit')}
                                    placeholder="Legacy / Auto-gen"
                                    autoComplete="off"
                                />
                            </div>
                        </div>
                    </section>
                )}

                <div className={styles.actions}>
                    <button
                        id="field-submit"
                        onClick={() => handleSubmit()}
                        disabled={saveMutation.isPending}
                        className={styles.submitButton}
                    >
                        {saveMutation.isPending ? (
                            <>
                                <span className={styles.btnSpinner}></span> Saving...
                            </>
                        ) : 'Complete Registration & Create Order (Enter)'}
                    </button>
                </div>
            </div>
        </div>
    );
}
