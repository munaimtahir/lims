import { useState, useEffect, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { orderApi, patientApi, laboratoryApi } from '../../api/services';
import type { Patient, OrderCreateRequest, TestSearchResult } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { useBranding } from '../../contexts/BrandingContext';
import { formatCurrency } from '../../utils/currency';
import styles from './CreateOrderPage.module.css';

export default function CreateOrderPage() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const patientId = searchParams.get('patient_id');

    const { currentBranch } = useAuth();
    const { branding } = useBranding();
    const currency = branding?.currency || 'PKR';

    const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
    const [loadingPatient, setLoadingPatient] = useState(false);

    // Test Selection State
    const [testQuery, setTestQuery] = useState('');
    const [testSuggestions, setTestSuggestions] = useState<TestSearchResult[]>([]);
    const [showTestSuggestions, setShowTestSuggestions] = useState(false);
    const [selectedTestIndex, setSelectedTestIndex] = useState(-1);
    const [addedTests, setAddedTests] = useState<TestSearchResult[]>([]);

    // Payment State
    const [discountAmount, setDiscountAmount] = useState('0');
    const [paidAmount, setPaidAmount] = useState('0');
    const [referredBy, setReferredBy] = useState('');

    const testSearchRef = useRef<HTMLInputElement>(null);

    // Load patient if ID provided
    useEffect(() => {
        if (patientId) {
            setLoadingPatient(true);
            patientApi.get(parseInt(patientId))
                .then(response => {
                    setSelectedPatient(response.data);
                    setReferredBy(response.data.default_referred_by || '');
                })
                .catch(err => {
                    console.error("Failed to load patient", err);
                    alert("Failed to load patient details");
                })
                .finally(() => setLoadingPatient(false));
        }
    }, [patientId]);

    // Focus test search on load if patient is selected
    useEffect(() => {
        if (selectedPatient && testSearchRef.current) {
            testSearchRef.current.focus();
        }
    }, [selectedPatient]);

    // Search Tests
    useEffect(() => {
        if (testQuery.length >= 2) {
            const timer = setTimeout(async () => {
                try {
                    const response = await laboratoryApi.searchTests(testQuery);
                    setTestSuggestions(response.data);
                    setShowTestSuggestions(response.data.length > 0);
                    setSelectedTestIndex(0);
                } catch {
                    setTestSuggestions([]);
                }
            }, 200);
            return () => clearTimeout(timer);
        } else {
            setTestSuggestions([]);
            setShowTestSuggestions(false);
        }
    }, [testQuery]);

    // Calculations
    const totalAmount = addedTests.reduce((sum, test) => sum + parseFloat(test.price), 0);

    // Update paid amount when total changes (lab workflow usually collects full amount or specific logic)
    useEffect(() => {
        const net = totalAmount - parseFloat(discountAmount || '0');
        setPaidAmount(Math.max(net, 0).toFixed(2));
    }, [totalAmount, discountAmount]);


    const createOrderMutation = useMutation({
        mutationFn: (data: OrderCreateRequest) => orderApi.create(data),
        onSuccess: (response) => {
            // Navigate to order details or show receipt
            // For now, let's redirect to orders list or show a success message
            // The prompt says "Order screen must open in ready state" and "Redirect logic into Order Creation"
            // Maybe we stay here and show receipt?
            // Let's redirect to print receipt for now or back to dashboard
            const orderId = response.order_id;
            // Assuming we want to show receipt immediately
            navigate(`/dashboard/orders`); // Or print route
            // In a real app we might show a modal here similar to RegistrationPage.
            // For this refactor, I'll stick to basic navigation or reused modal if I could, but I'll keeping it simple.
            alert(`Order Created! ID: ${response.lab_number || orderId}`);
        },
        onError: (err: any) => {
            console.error(err);
            alert('Failed to create order');
        }
    });

    const handleCreateOrder = (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedPatient) return alert('No patient selected');
        if (addedTests.length === 0) return alert('No tests added');

        const tests = addedTests.filter(t => t.type === 'test');
        const panels = addedTests.filter(t => t.type === 'panel');

        const orderData: OrderCreateRequest = {
            patient: selectedPatient.id,
            test_ids: tests.map((t) => t.test_id ?? t.id),
            panel_ids: panels.map((p) => p.id),
            discount: discountAmount,
            paid_amount: paidAmount,
            referred_by: referredBy,
        };
        if (currentBranch?.id) {
            orderData.collection_branch = currentBranch.id;
        }

        createOrderMutation.mutate(orderData);
    };

    const handleTestKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (showTestSuggestions && testSuggestions.length > 0 && selectedTestIndex >= 0) {
                addTest(testSuggestions[selectedTestIndex]);
            }
        } else if (e.key === 'ArrowDown') {
            if (showTestSuggestions) {
                e.preventDefault();
                setSelectedTestIndex(prev => prev < testSuggestions.length - 1 ? prev + 1 : prev);
            }
        } else if (e.key === 'ArrowUp') {
            if (showTestSuggestions) {
                e.preventDefault();
                setSelectedTestIndex(prev => prev > 0 ? prev - 1 : 0);
            }
        } else if (e.key === 'Escape') {
            setShowTestSuggestions(false);
        }
    };

    const addTest = (test: TestSearchResult) => {
        const testId = test.test_id ?? test.id;
        const isDuplicate = addedTests.find((t) => {
            if (test.type === 'panel') {
                return t.type === 'panel' && (t.id === testId);
            } else {
                return t.type === 'test' && ((t.test_id ?? t.id) === testId);
            }
        });

        if (!isDuplicate) {
            setAddedTests([...addedTests, { ...test, id: testId }]);
        }
        setTestQuery('');
        setShowTestSuggestions(false);
        setSelectedTestIndex(-1);
        testSearchRef.current?.focus();
    };

    const removeTest = (testId: number) => {
        setAddedTests(addedTests.filter((t) => (t.test_id ?? t.id) !== testId));
    };

    if (loadingPatient) {
        return <div className={styles.loading}>Loading Patient...</div>;
    }

    if (!selectedPatient && !loadingPatient) {
        return <div className={styles.error}>No patient selected. Please register a patient first.</div>;
    }

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1>Create Order</h1>
                {selectedPatient && (
                    <div className={styles.patientBanner}>
                        <h2>{selectedPatient.full_name}</h2>
                        <div className={styles.patientMeta}>
                            <span>{selectedPatient.phone}</span>
                            <span>{selectedPatient.gender}</span>
                            <span>{selectedPatient.age_years}Y / {selectedPatient.date_of_birth}</span>
                        </div>
                    </div>
                )}
            </header>

            <div className={styles.mainContent}>
                <div className={styles.testSelection}>
                    <h3>Select Tests</h3>
                    <div className={styles.searchWrapper}>
                        <input
                            ref={testSearchRef}
                            type="text"
                            placeholder="Search tests..."
                            value={testQuery}
                            onChange={(e) => setTestQuery(e.target.value)}
                            onKeyDown={handleTestKeyDown}
                            className={styles.searchInput}
                        />
                        {showTestSuggestions && (
                            <div className={styles.suggestions}>
                                {testSuggestions.map((test, index) => (
                                    <div
                                        key={test.id}
                                        className={`${styles.suggestionItem} ${index === selectedTestIndex ? styles.active : ''}`}
                                        onClick={() => addTest(test)}
                                    >
                                        {test.test_name} - {formatCurrency(test.price, currency)}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className={styles.addedTests}>
                        {addedTests.map(test => (
                            <div key={test.test_id ?? test.id} className={styles.testItem}>
                                <span>{test.test_name}</span>
                                <span>{formatCurrency(test.price, currency)}</span>
                                <button onClick={() => removeTest(test.test_id ?? test.id)}>×</button>
                            </div>
                        ))}
                        {addedTests.length === 0 && <p className={styles.emptyText}>No tests added</p>}
                    </div>
                </div>

                <div className={styles.summary}>
                    <h3>Order Summary</h3>
                    <div className={styles.summaryRow}>
                        <span>Total</span>
                        <span>{formatCurrency(totalAmount.toFixed(2), currency)}</span>
                    </div>
                    <div className={styles.formGroup}>
                        <label>Discount</label>
                        <input
                            type="number"
                            value={discountAmount}
                            onChange={e => setDiscountAmount(e.target.value)}
                        />
                    </div>
                    <div className={styles.formGroup}>
                        <label>Paid Amount</label>
                        <input
                            type="number"
                            value={paidAmount}
                            onChange={e => setPaidAmount(e.target.value)}
                        />
                    </div>
                    <div className={styles.summaryRow}>
                        <span>Balance</span>
                        <span>{formatCurrency((totalAmount - parseFloat(discountAmount) - parseFloat(paidAmount)).toFixed(2), currency)}</span>
                    </div>

                    <button
                        className={styles.createButton}
                        onClick={handleCreateOrder}
                        disabled={createOrderMutation.isPending || addedTests.length === 0}
                    >
                        {createOrderMutation.isPending ? 'Creating Only...' : 'Create Order'}
                    </button>
                </div>
            </div>
        </div>
    );
}
