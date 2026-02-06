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

import type { Order, Patient, SystemSettings, OrderItem } from '../../types';

export const TEST_PATIENT_LONG_NAME: Patient = {
    id: 1,
    patient_id: 'MRN-2026-00001',
    first_name: 'Muhammad',
    last_name: 'Abdullah',
    full_name: 'Muhammad Abdullah Al-Rahman Khan bin Yusuf Al-Hashimi',
    age: 39,
    gender: 'Male',
    total_orders: 5,
    phone: '+92-300-1234567',
    date_of_birth: '1985-03-15',
    age_years: 39,
    age_months: 0,
    age_days: 0,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
};

const createMockOrderItem = (id: number, name: string, code: string, price: string): OrderItem => ({
    id,
    test_name: name,
    test_code: code,
    price,
    status: 'NEW',
    panel: undefined,
    panel_name: undefined,
    panel_code: undefined,
});

export const TEST_ORDER_MULTIPLE_ITEMS: Order = {
    id: 1,
    order_id: 'ORD-20260206-0001',
    patient: 1,
    patient_name: 'Muhammad Abdullah',
    status: 'NEW',
    notes: 'Test order with multiple items',
    discount_percent: '10.0',
    is_paid: true,
    total_amount: '15500.00',
    discount: '1500.00',
    net_amount: '14000.00',
    paid_amount: '14000.00',
    due_amount: '0.00',
    referred_by: 'Dr. Professor Muhammad Shahid Ahmed Al-Qureshi, MBBS, FCPS, FRCP',
    created_at: '2026-02-06T10:30:00Z',
    updated_at: '2026-02-06T10:30:00Z',
    items: [
        createMockOrderItem(1, 'Complete Blood Count with Differential and Platelet Count', 'CBC-DIFF', '1200.00'),
        createMockOrderItem(2, 'Liver Function Test (Complete Panel)', 'LFT-COMP', '2500.00'),
        createMockOrderItem(3, 'Kidney Function Test with Electrolytes', 'KFT-ELEC', '2800.00'),
        createMockOrderItem(4, 'Lipid Profile (Total Cholesterol, HDL, LDL, Triglycerides)', 'LIPID-PRO', '2000.00'),
        createMockOrderItem(5, 'Thyroid Stimulating Hormone (TSH) - Ultra Sensitive', 'TSH-US', '1500.00'),
        createMockOrderItem(6, 'Hemoglobin A1c (HbA1c) - Glycated Hemoglobin', 'HBA1C', '1800.00'),
        createMockOrderItem(7, 'Vitamin D (25-Hydroxy) - Total', 'VIT-D', '2200.00'),
        createMockOrderItem(8, 'C-Reactive Protein (CRP) - High Sensitivity', 'CRP-HS', '1500.00'),
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
    patient_name: 'Muhammad Abdullah',
    status: 'NEW',
    notes: 'Single item order',
    discount_percent: '0.0',
    is_paid: true,
    total_amount: '800.00',
    discount: '0.00',
    net_amount: '800.00',
    paid_amount: '800.00',
    due_amount: '0.00',
    referred_by: 'Dr. Ahmed',
    created_at: '2026-02-06T11:00:00Z',
    updated_at: '2026-02-06T11:00:00Z',
    items: [
        createMockOrderItem(1, 'Blood Sugar Random', 'BSR', '800.00'),
    ],
};

export const TEST_SETTINGS: SystemSettings = {
    id: 1,
    lab_name: 'Al-Shifa Medical Laboratory',
    lab_display_name: 'AL-SHIFA MEDICAL LABORATORY',
    lab_address: 'Main Boulevard, Gulberg III, Lahore, Punjab, Pakistan',
    lab_phone: '+92-42-35714567, +92-300-8765432',
    lab_email: 'info@alshifalab.pk',
    currency: 'PKR',
    tax_rate: '0.0',
    email_port: 587,
    email_use_tls: true,
    email_use_ssl: false,
    backup_enabled: true,
    backup_frequency: 'daily',
    report_header_image: undefined,
    report_footer_image: undefined,
    report_footer: 'Thank you for choosing Al-Shifa Medical Laboratory. For queries, call +92-42-35714567',
    lab_logo: undefined,
    updated_at: '2026-01-01T00:00:00Z',
};

export const TEST_SETTINGS_WITH_IMAGES: SystemSettings = {
    ...TEST_SETTINGS,
    lab_logo: 'https://via.placeholder.com/150x50/2563eb/ffffff?text=AL-SHIFA+LAB',
    report_header_image: undefined,
    report_footer_image: undefined,
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
