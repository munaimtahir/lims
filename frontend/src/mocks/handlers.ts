import { http, HttpResponse } from 'msw';

export const handlers = [
    http.get('*/orders/123', () => {
        return HttpResponse.json({
            id: 123,
            order_id: 'ORD-123',
            patient: 1,
            patient_name: 'Test Patient',
            created_at: '2023-01-01',
            updated_at: '2023-01-01',
            status: 'NEW',
            notes: '',
            total_amount: '100',
            discount: '0',
            discount_percent: '0',
            paid_amount: '0',
            due_amount: '100',
            net_amount: '100',
            is_paid: false,
            items: []
        });
    }),

    http.get('*/patients/1', () => {
        return HttpResponse.json({
            id: 1,
            full_name: 'Test Patient'
        });
    })
];
