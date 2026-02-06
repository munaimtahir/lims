import { describe, it, expect } from 'vitest';
import { OrderSchema, PatientSchema } from './schemas';

// Sample Fixtures (idealized)
const validOrder = {
    id: 123,
    order_id: 'ORD-2023-001',
    patient: 45,
    patient_name: 'John Doe',
    created_at: '2023-10-27T10:00:00Z',
    updated_at: '2023-10-27T12:00:00Z',
    status: 'NEW',
    notes: '',
    total_amount: '1500.00',
    discount: '0.00',
    discount_percent: '0.00',
    paid_amount: '0.00',
    due_amount: '1500.00',
    net_amount: '1500.00',
    is_paid: false,
    items: [
        {
            id: 1,
            price: '500.00',
            status: 'PENDING'
        }
    ]
};

const validPatient = {
    id: 45,
    patient_id: 'PAT-001',
    first_name: 'John',
    last_name: 'Doe',
    full_name: 'John Doe',
    age: 30,
    gender: 'Male',
    phone: '1234567890',
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
    total_orders: 5
};

describe('API Contract Schemas', () => {
    it('validates a correct Order object', () => {
        const result = OrderSchema.safeParse(validOrder);
        if (!result.success) {
            console.error('Order Validation Errors:', result.error);
        }
        expect(result.success).toBe(true);
    });

    it('validates a correct Patient object', () => {
        const result = PatientSchema.safeParse(validPatient);
        if (!result.success) {
            console.error('Patient Validation Errors:', result.error);
        }
        expect(result.success).toBe(true);
    });

    it('fails on missing required fields', () => {
        const invalidOrder = { ...validOrder };
        // @ts-expect-error Tests invalid schema
        delete invalidOrder.id;
        const result = OrderSchema.safeParse(invalidOrder);
        expect(result.success).toBe(false);
    });
});
