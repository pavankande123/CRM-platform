import { apiRequest } from './apiClient';
import type {
  StandardResponse,
  PaginatedResponse,
  Payment,
  PaymentCreate,
  PaymentSummary,
} from '../types';

export const paymentService = {
  async getPayments(params?: {
    customer_id?: string;
    project_id?: string;
    status?: string;
    page?: number;
    pageSize?: number;
  }): Promise<PaginatedResponse<Payment>> {
    const q = new URLSearchParams();
    if (params?.customer_id) q.append('customer_id', params.customer_id);
    if (params?.project_id) q.append('project_id', params.project_id);
    if (params?.status) q.append('status', params.status);
    if (params?.page) q.append('page', String(params.page));
    if (params?.pageSize) q.append('page_size', String(params.pageSize));

    const endpoint = `/payments${q.toString() ? `?${q.toString()}` : ''}`;
    const res = await apiRequest<StandardResponse<PaginatedResponse<Payment>>>(endpoint);
    return res.data;
  },

  async getSummary(projectId?: string): Promise<PaymentSummary> {
    const endpoint = projectId ? `/payments/summary?project_id=${projectId}` : '/payments/summary';
    const res = await apiRequest<StandardResponse<PaymentSummary>>(endpoint);
    return res.data;
  },

  async createPayment(payload: PaymentCreate): Promise<Payment> {
    const res = await apiRequest<StandardResponse<Payment>>('/payments', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },
};
