/**
 * Test Data Fixtures for Receipt Printing
 * 
 * This file contains test data with edge cases for verifying receipt layout:
 * - Long patient names
 * - Long consultant names
 * - Multiple test items
 * - Long test names
 * - Various financial scenarios
 */

import type { Order, Patient, SystemSettings } from '../../types';

export const TEST_PATIENT_LONG_NAME: Patient = {
    id: 1,
    patient_id: 'MRN-2026-00001',
    full_name: 'Muhammad Abdullah Al-Rahman Khan bin Yusuf Al-Hashimi',
    date_of_birth: '1985-03-15',
    age_years: 39,
    age_months: 0,
    age_days: 0,
    gender: 'M',
    phone: '+92-300-1234567',
    email: 'patient@example.com',
    address: 'House No. 123, Street 45, Sector F-10/3, Islamabad Capital Territory, Pakistan',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
};

export const TEST_ORDER_MULTIPLE_ITEMS: Order = {
    id: 1,
    order_id: 'ORD-20260206-0001',
    patient: 1,
    status: 'paid',
    total_amount: '15500.00',
    discount: '1500.00',
    net_amount: '14000.00',
    paid_amount: '14000.00',
    due_amount: '0.00',
    payment_method: 'cash',
    referred_by: 'Dr. Professor Muhammad Shahid Ahmed Al-Qureshi, MBBS, FCPS, FRCP',
    created_at: '2026-02-06T10:30:00Z',
    updated_at: '2026-02-06T10:30:00Z',
    items: [
        {
            id: 1,
            order: 1,
            test: 1,
            test_name: 'Complete Blood Count with Differential and Platelet Count',
            test_code: 'CBC-DIFF',
            price: '1200.00',
            panel: null,
            panel_name: null,
            panel_code: null,
        },
        {
            id: 2,
            order: 1,
            test: 2,
            test_name: 'Liver Function Test (Complete Panel)',
            test_code: 'LFT-COMP',
            price: '2500.00',
            panel: null,
            panel_name: null,
            panel_code: null,
        },
        {
            id: 3,
            order: 1,
            test: 3,
            test_name: 'Kidney Function Test with Electrolytes',
            test_code: 'KFT-ELEC',
            price: '2800.00',
            panel: null,
            panel_name: null,
            panel_code: null,
        },
        {
            id: 4,
            order: 1,
            test: 4,
            test_name: 'Lipid Profile (Total Cholesterol, HDL, LDL, Triglycerides)',
            test_code: 'LIPID-PRO',
            price: '2000.00',
            panel: null,
            panel_name: null,
            panel_code: null,
        },
        {
            id: 5,
            order: 1,
            test: 5,
            test_name: 'Thyroid Stimulating Hormone (TSH) - Ultra Sensitive',
            test_code: 'TSH-US',
            price: '1500.00',
            panel: null,
            panel_name: null,
            panel_code: null,
        },
        {
            id: 6,
            order: 1,
            test: 6,
            test_name: 'Hemoglobin A1c (HbA1c) - Glycated Hemoglobin',
            test_code: 'HBA1C',
            price: '1800.00',
            panel: null,
            panel_name: null,
            panel_code: null,
        },
        {
            id: 7,
            order: 1,
            test: 7,
            test_name: 'Vitamin D (25-Hydroxy) - Total',
            test_code: 'VIT-D',
            price: '2200.00',
            panel: null,
            panel_name: null,
            panel_code: null,
        },
        {
            id: 8,
            order: 1,
            test: 8,
            test_name: 'C-Reactive Protein (CRP) - High Sensitivity',
            test_code: 'CRP-HS',
            price: '1500.00',
            panel: null,
            panel_name: null,
            panel_code: null,
        },
    ],
};

export const TEST_ORDER_PARTIAL_PAYMENT: Order = {
    ...TEST_ORDER_MULTIPLE_ITEMS,
    id: 2,
    order_id: 'ORD-20260206-0002',
    paid_amount: '10000.00',
    due_amount: '4000.00',
};

export const TEST_ORDER_NO_DISCOUNT: Order = {
    ...TEST_ORDER_MULTIPLE_ITEMS,
    id: 3,
    order_id: 'ORD-20260206-0003',
    discount: '0.00',
    net_amount: '15500.00',
    paid_amount: '15500.00',
    due_amount: '0.00',
};

export const TEST_ORDER_SINGLE_ITEM: Order = {
    id: 4,
    order_id: 'ORD-20260206-0004',
    patient: 1,
    status: 'paid',
    total_amount: '800.00',
    discount: '0.00',
    net_amount: '800.00',
    paid_amount: '800.00',
    due_amount: '0.00',
    payment_method: 'cash',
    referred_by: 'Dr. Ahmed',
    created_at: '2026-02-06T11:00:00Z',
    updated_at: '2026-02-06T11:00:00Z',
    items: [
        {
            id: 1,
            order: 4,
            test: 1,
            test_name: 'Blood Sugar Random',
            test_code: 'BSR',
            price: '800.00',
            panel: null,
            panel_name: null,
            panel_code: null,
        },
    ],
};

export const TEST_SETTINGS: SystemSettings = {
    id: 1,
    lab_name: 'Al-Shifa Medical Laboratory',
    lab_display_name: 'AL-SHIFA MEDICAL LABORATORY',
    lab_address: 'Main Boulevard, Gulberg III, Lahore, Punjab, Pakistan',
    lab_phone: '+92-42-35714567, +92-300-8765432',
    lab_email: 'info@alshifalab.pk',
    lab_website: 'https://alshifalab.pk',
    currency: 'PKR',
    report_header_image: null,
    report_footer_image: null,
    report_footer: 'Thank you for choosing Al-Shifa Medical Laboratory. For queries, call +92-42-35714567',
    lab_logo: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
};

export const TEST_SETTINGS_WITH_IMAGES: SystemSettings = {
    ...TEST_SETTINGS,
    lab_logo: 'https://via.placeholder.com/150x50/2563eb/ffffff?text=AL-SHIFA+LAB',
    report_header_image: null,
    report_footer_image: null,
};

/**
 * Test scenarios for manual verification
 */
export const TEST_SCENARIOS = {
    'Long Names + Multiple Items': {
        patient: TEST_PATIENT_LONG_NAME,
        order: TEST_ORDER_MULTIPLE_ITEMS,
        settings: TEST_SETTINGS,
    },
    'Partial Payment': {
        patient: TEST_PATIENT_LONG_NAME,
        order: TEST_ORDER_PARTIAL_PAYMENT,
        settings: TEST_SETTINGS,
    },
    'No Discount': {
        patient: TEST_PATIENT_LONG_NAME,
        order: TEST_ORDER_NO_DISCOUNT,
        settings: TEST_SETTINGS,
    },
    'Single Item': {
        patient: TEST_PATIENT_LONG_NAME,
        order: TEST_ORDER_SINGLE_ITEM,
        settings: TEST_SETTINGS,
    },
    'With Logo': {
        patient: TEST_PATIENT_LONG_NAME,
        order: TEST_ORDER_MULTIPLE_ITEMS,
        settings: TEST_SETTINGS_WITH_IMAGES,
    },
};

/**
 * Instructions for using test data:
 * 
 * 1. Import this file in PrintReceiptPage.tsx
 * 2. Add a dev-only toggle to use test data
 * 3. Example:
 * 
 * ```tsx
 * import { TEST_SCENARIOS } from './testData';
 * 
 * // In component:
 * const [useTestData, setUseTestData] = useState(false);
 * 
 * // In render:
 * const displayOrder = useTestData ? TEST_SCENARIOS['Long Names + Multiple Items'].order : order;
 * const displayPatient = useTestData ? TEST_SCENARIOS['Long Names + Multiple Items'].patient : patient;
 * ```
 */
