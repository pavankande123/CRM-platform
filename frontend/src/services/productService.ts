import { apiRequest } from './apiClient';
import type { StandardResponse, Product } from '../types';

export const productService = {
  async getProducts(params?: { search?: string; is_active?: boolean }): Promise<Product[]> {
    const q = new URLSearchParams();
    if (params?.search) q.append('search', params.search);
    if (params?.is_active !== undefined) q.append('is_active', String(params.is_active));

    const endpoint = `/products${q.toString() ? `?${q.toString()}` : ''}`;
    const res = await apiRequest<StandardResponse<any>>(endpoint);
    if (Array.isArray(res.data)) {
      return res.data;
    }
    if (res.data && Array.isArray(res.data.items)) {
      return res.data.items;
    }
    return [];
  },

  async createProduct(payload: {
    name: string;
    sku?: string;
    code?: string;
    category?: string;
    description?: string;
  }): Promise<Product> {
    const res = await apiRequest<StandardResponse<Product>>('/products', {
      method: 'POST',
      body: JSON.stringify({
        ...payload,
        code: payload.code || payload.sku || undefined,
        sku: payload.sku || payload.code || undefined,
      }),
    });
    return res.data;
  },
};
