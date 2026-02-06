import apiClient from '../client';
import type { Order, OrderItem } from '../../types';
import { OrderSchema } from '../contracts/schemas';

export const orderApi = {
  get: async (id: number) => {
    const response = await apiClient.get<Order>(`/orders/${id}`);
    // Runtime contract validation (Gate S4)
    try {
      OrderSchema.parse(response.data);
    } catch (e) {
      console.error('API Contract Violation:', e);
    }
    return response;
  },
  getOrderItem: (id: number) => apiClient.get<OrderItem>(`/orders/items/${id}`),
};
