import { z } from 'zod';

// Helper for strings that might be numbers in JSON
const StringOrNumber = z.union([z.string(), z.number()]).transform((val) => String(val));

// Order Status Enum
export const OrderStatusSchema = z.enum(['NEW', 'COLLECTED', 'IN_PROCESS', 'VERIFIED', 'PUBLISHED', 'CANCELLED']);

// Order Item Schema
export const OrderItemSchema = z.object({
    id: z.number(),
    test: z.number().optional(),
    panel: z.number().optional(),
    test_name: z.string().optional(),
    panel_name: z.string().optional(),
    test_code: z.string().optional(),
    panel_code: z.string().optional(),
    price: StringOrNumber,
    status: z.string(),
});

// Order Schema
export const OrderSchema = z.object({
    id: z.number(),
    order_id: z.string(),
    patient: z.number(),
    patient_name: z.string(),
    ordered_by: z.number().optional(),
    ordered_by_name: z.string().optional(),
    created_at: z.string(), // DateTime string
    updated_at: z.string(),
    status: OrderStatusSchema,
    notes: z.string(), // might be empty string
    referred_by: z.string().optional(),
    total_amount: StringOrNumber,
    discount: StringOrNumber,
    discount_percent: StringOrNumber,
    paid_amount: StringOrNumber,
    due_amount: StringOrNumber,
    net_amount: StringOrNumber,
    is_paid: z.boolean(),
    items: z.array(OrderItemSchema),
});

// Patient Schema
export const PatientSchema = z.object({
    id: z.number(),
    patient_id: z.string(),
    first_name: z.string(),
    last_name: z.string(),
    full_name: z.string(),
    age: z.number(),
    gender: z.enum(['Male', 'Female', 'Other']),
    phone: z.string(),
    created_at: z.string(),
    updated_at: z.string(),
    total_orders: z.number(),
}).passthrough(); // Allow other fields

// Login Response Schema
export const UserSchema = z.object({
    id: z.number(),
    username: z.string(),
    email: z.string(),
    full_name: z.string(),
    role: z.string(), // We can be specific if we want
});

export const LoginResponseSchema = z.object({
    success: z.boolean(),
    data: z.object({
        user: UserSchema,
        access_token: z.string(),
        refresh_token: z.string(),
    }),
    message: z.string(),
});
