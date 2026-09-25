import { apiRequest } from './apiClient';
import type { StandardResponse, Product } from '../types';

export const productService = {
  async getProducts(params?: { search?: string; is_active?: boolean }): Promise<Product[]> {
    const q = new URLSearchParams();
    if (params?.search) q.append('search', params.search);
    if (params?.is_active !== undefined) q.append('is_active', String(params.is_active));

    const endpoint = `/products${q.toString() ? `?${q.toString()}` : ''}`;
    const res = await apiRequest<StandardResponse<Product[]>>(endpoint);
    return res.data;
  },

  async createProduct(payload: {
    name: string;
    sku?: string;
    category?: string;
    description?: string;
  }): Promise<Product> {
    const res = await apiRequest<StandardResponse<Product>>('/products', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },
};
