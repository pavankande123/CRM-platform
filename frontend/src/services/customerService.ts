import { apiRequest } from './apiClient';
import type { StandardResponse, PaginatedResponse, Customer, CustomerCreate, Contact } from '../types';

export const customerService = {
  async getCustomers(params?: {
    search?: string;
    status?: string;
    page?: number;
    pageSize?: number;
  }): Promise<PaginatedResponse<Customer>> {
    const q = new URLSearchParams();
    if (params?.search) q.append('search', params.search);
    if (params?.status) q.append('status', params.status);
    if (params?.page) q.append('page', String(params.page));
    if (params?.pageSize) q.append('page_size', String(params.pageSize));

    const endpoint = `/customers${q.toString() ? `?${q.toString()}` : ''}`;
    const res = await apiRequest<StandardResponse<PaginatedResponse<Customer>>>(endpoint);
    return res.data;
  },

  async getCustomer(id: string): Promise<Customer> {
    const res = await apiRequest<StandardResponse<Customer>>(`/customers/${id}`);
    return res.data;
  },

  async createCustomer(payload: CustomerCreate): Promise<Customer> {
    const res = await apiRequest<StandardResponse<Customer>>('/customers', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async updateCustomer(id: string, payload: Partial<CustomerCreate>): Promise<Customer> {
    const res = await apiRequest<StandardResponse<Customer>>(`/customers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async deleteCustomer(id: string): Promise<void> {
    await apiRequest<StandardResponse<{ deleted: boolean }>>(`/customers/${id}`, {
      method: 'DELETE',
    });
  },

  async createContact(customerId: string, payload: {
    name: string;
    designation?: string;
    email?: string;
    phone?: string;
    is_primary?: boolean;
    notes?: string;
  }): Promise<Contact> {
    const res = await apiRequest<StandardResponse<Contact>>(`/customers/${customerId}/contacts`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },
};
