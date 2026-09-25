import { apiRequest } from './apiClient';
import type {
  StandardResponse,
  PaginatedResponse,
  Project,
  ProjectDetail,
  ProjectCreate,
  Pipeline,
} from '../types';

export const pipelineService = {
  async getPipelines(): Promise<Pipeline[]> {
    const res = await apiRequest<StandardResponse<Pipeline[]>>('/pipelines');
    return res.data;
  },
};

export const projectService = {
  async getProjects(params?: {
    customer_id?: string;
    stage_id?: string;
    status?: string;
    search?: string;
    page?: number;
    pageSize?: number;
  }): Promise<PaginatedResponse<Project>> {
    const q = new URLSearchParams();
    if (params?.customer_id) q.append('customer_id', params.customer_id);
    if (params?.stage_id) q.append('stage_id', params.stage_id);
    if (params?.status) q.append('status', params.status);
    if (params?.search) q.append('search', params.search);
    if (params?.page) q.append('page', String(params.page));
    if (params?.pageSize) q.append('page_size', String(params.pageSize));

    const endpoint = `/projects${q.toString() ? `?${q.toString()}` : ''}`;
    const res = await apiRequest<StandardResponse<PaginatedResponse<Project>>>(endpoint);
    return res.data;
  },

  async getProject(id: string): Promise<ProjectDetail> {
    const res = await apiRequest<StandardResponse<ProjectDetail>>(`/projects/${id}`);
    return res.data;
  },

  async createProject(payload: ProjectCreate): Promise<Project> {
    const res = await apiRequest<StandardResponse<Project>>('/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async changeStage(projectId: string, stageId: string, notes?: string): Promise<Project> {
    const res = await apiRequest<StandardResponse<Project>>(`/projects/${projectId}/stage`, {
      method: 'POST',
      body: JSON.stringify({ stage_id: stageId, notes }),
    });
    return res.data;
  },

  async updateProject(projectId: string, payload: Partial<ProjectCreate>): Promise<Project> {
    const res = await apiRequest<StandardResponse<Project>>(`/projects/${projectId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return res.data;
  },
};
