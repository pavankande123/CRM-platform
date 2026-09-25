import { apiRequest } from './apiClient';
import type { StandardResponse, Note, DocumentMetadata, SearchResponse, CoreDashboardResponse } from '../types';

export const noteService = {
  async getNotes(params: { customer_id?: string; project_id?: string }): Promise<Note[]> {
    const q = new URLSearchParams();
    if (params.customer_id) q.append('customer_id', params.customer_id);
    if (params.project_id) q.append('project_id', params.project_id);

    const res = await apiRequest<StandardResponse<Note[]>>(`/notes?${q.toString()}`);
    return res.data;
  },

  async createNote(payload: {
    customer_id?: string;
    project_id?: string;
    follow_up_id?: string;
    payment_id?: string;
    content: string;
  }): Promise<Note> {
    const res = await apiRequest<StandardResponse<Note>>('/notes', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },
};

export const documentService = {
  async getDocuments(params: { customer_id?: string; project_id?: string }): Promise<DocumentMetadata[]> {
    const q = new URLSearchParams();
    if (params.customer_id) q.append('customer_id', params.customer_id);
    if (params.project_id) q.append('project_id', params.project_id);

    const res = await apiRequest<StandardResponse<DocumentMetadata[]>>(`/documents?${q.toString()}`);
    return res.data;
  },

  async createDocument(payload: {
    customer_id?: string;
    project_id?: string;
    file_name: string;
    file_type: string;
    file_size_bytes: number;
    document_category?: string;
    storage_url?: string;
  }): Promise<DocumentMetadata> {
    const res = await apiRequest<StandardResponse<DocumentMetadata>>('/documents', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },
};

export const searchService = {
  async search(query: string, limit: number = 10): Promise<SearchResponse> {
    const res = await apiRequest<StandardResponse<SearchResponse>>(
      `/search?q=${encodeURIComponent(query)}&limit=${limit}`
    );
    return res.data;
  },
};

export const dashboardService = {
  async getDashboard(): Promise<CoreDashboardResponse> {
    const res = await apiRequest<StandardResponse<CoreDashboardResponse>>('/dashboard');
    return res.data;
  },
};
