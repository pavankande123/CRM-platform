import { apiRequest } from './apiClient';
import type { StandardResponse, PaginatedResponse, FollowUp, FollowUpCreate } from '../types';

export const followUpService = {
  async getFollowUps(params?: {
    customer_id?: string;
    project_id?: string;
    status?: string;
    overdue_only?: boolean;
    today_only?: boolean;
    page?: number;
    pageSize?: number;
  }): Promise<PaginatedResponse<FollowUp>> {
    const q = new URLSearchParams();
    if (params?.customer_id) q.append('customer_id', params.customer_id);
    if (params?.project_id) q.append('project_id', params.project_id);
    if (params?.status) q.append('status', params.status);
    if (params?.overdue_only) q.append('overdue_only', 'true');
    if (params?.today_only) q.append('today_only', 'true');
    if (params?.page) q.append('page', String(params.page));
    if (params?.pageSize) q.append('page_size', String(params.pageSize));

    const endpoint = `/follow-ups${q.toString() ? `?${q.toString()}` : ''}`;
    const res = await apiRequest<StandardResponse<PaginatedResponse<FollowUp>>>(endpoint);
    return res.data;
  },

  async createFollowUp(payload: FollowUpCreate): Promise<FollowUp> {
    const res = await apiRequest<StandardResponse<FollowUp>>('/follow-ups', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async completeFollowUp(id: string, notes?: string): Promise<FollowUp> {
    const res = await apiRequest<StandardResponse<FollowUp>>(`/follow-ups/${id}/complete`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
    return res.data;
  },

  async cancelFollowUp(id: string): Promise<FollowUp> {
    const res = await apiRequest<StandardResponse<FollowUp>>(`/follow-ups/${id}/cancel`, {
      method: 'POST',
    });
    return res.data;
  },
};
