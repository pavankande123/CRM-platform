import { apiRequest } from './apiClient';
import type {
  StandardResponse,
  PaginatedResponse,
  Pipeline,
  PipelineCreate,
  PipelineStage,
  PipelineStageCreate,
  CustomField,
  CustomFieldCreate,
  CustomFieldValue,
  SavedView,
  SavedViewCreate,
  WorkflowDefinition,
  WorkflowCreate,
  WorkflowExecution,
  NotificationItem,
  ApprovalRequest,
  ApprovalCreate,
  ApprovalDecisionPayload,
} from '../types';

// ==========================================
// 1. PIPELINE CONFIGURATION SERVICE
// ==========================================
export const pipelineConfigService = {
  async getPipelines(): Promise<Pipeline[]> {
    const res = await apiRequest<StandardResponse<Pipeline[]>>('/pipelines');
    return res.data;
  },

  async createPipeline(payload: PipelineCreate): Promise<Pipeline> {
    const res = await apiRequest<StandardResponse<Pipeline>>('/pipelines', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async updatePipeline(pipelineId: string, payload: Partial<PipelineCreate>): Promise<Pipeline> {
    const res = await apiRequest<StandardResponse<Pipeline>>(`/pipelines/${pipelineId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async createStage(pipelineId: string, payload: PipelineStageCreate): Promise<PipelineStage> {
    const res = await apiRequest<StandardResponse<PipelineStage>>(`/pipelines/${pipelineId}/stages`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async updateStage(pipelineId: string, stageId: string, payload: Partial<PipelineStageCreate>): Promise<PipelineStage> {
    const res = await apiRequest<StandardResponse<PipelineStage>>(`/pipelines/${pipelineId}/stages/${stageId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async reorderStages(pipelineId: string, stageIds: string[]): Promise<PipelineStage[]> {
    const res = await apiRequest<StandardResponse<PipelineStage[]>>(`/pipelines/${pipelineId}/stages/reorder`, {
      method: 'POST',
      body: JSON.stringify({ stage_ids: stageIds }),
    });
    return res.data;
  },

  async deactivateStage(pipelineId: string, stageId: string): Promise<PipelineStage> {
    const res = await apiRequest<StandardResponse<PipelineStage>>(`/pipelines/${pipelineId}/stages/${stageId}`, {
      method: 'DELETE',
    });
    return res.data;
  },
};

// ==========================================
// 2. CUSTOM FIELDS SERVICE
// ==========================================
export const customFieldService = {
  async getCustomFields(entityType?: string): Promise<CustomField[]> {
    const q = entityType ? `?entity_type=${entityType}` : '';
    const res = await apiRequest<StandardResponse<CustomField[]>>(`/custom-fields${q}`);
    return res.data;
  },

  async createCustomField(payload: CustomFieldCreate): Promise<CustomField> {
    const res = await apiRequest<StandardResponse<CustomField>>('/custom-fields', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async updateCustomField(id: string, payload: Partial<CustomFieldCreate>): Promise<CustomField> {
    const res = await apiRequest<StandardResponse<CustomField>>(`/custom-fields/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async deactivateCustomField(id: string): Promise<CustomField> {
    const res = await apiRequest<StandardResponse<CustomField>>(`/custom-fields/${id}`, {
      method: 'DELETE',
    });
    return res.data;
  },

  async getEntityValues(entityType: string, entityId: string): Promise<CustomFieldValue[]> {
    const res = await apiRequest<StandardResponse<CustomFieldValue[]>>(`/custom-fields/values/${entityType}/${entityId}`);
    return res.data;
  },

  async saveEntityValues(entityType: string, entityId: string, values: Record<string, unknown>): Promise<CustomFieldValue[]> {
    const res = await apiRequest<StandardResponse<CustomFieldValue[]>>(`/custom-fields/values/${entityType}/${entityId}`, {
      method: 'POST',
      body: JSON.stringify({ values }),
    });
    return res.data;
  },
};

// ==========================================
// 3. SAVED VIEWS SERVICE
// ==========================================
export const savedViewService = {
  async getViews(entityType?: string): Promise<SavedView[]> {
    const q = entityType ? `?entity_type=${entityType}` : '';
    const res = await apiRequest<StandardResponse<SavedView[]>>(`/views${q}`);
    return res.data;
  },

  async getView(id: string): Promise<SavedView> {
    const res = await apiRequest<StandardResponse<SavedView>>(`/views/${id}`);
    return res.data;
  },

  async createView(payload: SavedViewCreate): Promise<SavedView> {
    const res = await apiRequest<StandardResponse<SavedView>>('/views', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async updateView(id: string, payload: Partial<SavedViewCreate>): Promise<SavedView> {
    const res = await apiRequest<StandardResponse<SavedView>>(`/views/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async deleteView(id: string): Promise<void> {
    await apiRequest<StandardResponse<{ message: string }>>(`/views/${id}`, {
      method: 'DELETE',
    });
  },

  async executeView(id: string, page = 1, pageSize = 25): Promise<PaginatedResponse<Record<string, unknown>>> {
    const res = await apiRequest<StandardResponse<PaginatedResponse<Record<string, unknown>>>>(
      `/views/${id}/execute?page=${page}&page_size=${pageSize}`,
      { method: 'POST' }
    );
    return res.data;
  },
};

// ==========================================
// 4. WORKFLOW ENGINE SERVICE
// ==========================================
export const workflowService = {
  async getWorkflows(): Promise<WorkflowDefinition[]> {
    const res = await apiRequest<StandardResponse<WorkflowDefinition[]>>('/workflows');
    return res.data;
  },

  async createWorkflow(payload: WorkflowCreate): Promise<WorkflowDefinition> {
    const res = await apiRequest<StandardResponse<WorkflowDefinition>>('/workflows', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async updateWorkflow(id: string, payload: Partial<WorkflowCreate>): Promise<WorkflowDefinition> {
    const res = await apiRequest<StandardResponse<WorkflowDefinition>>(`/workflows/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async activateWorkflow(id: string): Promise<WorkflowDefinition> {
    const res = await apiRequest<StandardResponse<WorkflowDefinition>>(`/workflows/${id}/activate`, {
      method: 'POST',
    });
    return res.data;
  },

  async deactivateWorkflow(id: string): Promise<WorkflowDefinition> {
    const res = await apiRequest<StandardResponse<WorkflowDefinition>>(`/workflows/${id}/deactivate`, {
      method: 'POST',
    });
    return res.data;
  },

  async deleteWorkflow(id: string): Promise<void> {
    await apiRequest<StandardResponse<{ message: string }>>(`/workflows/${id}`, {
      method: 'DELETE',
    });
  },

  async getExecutions(workflowId?: string, limit = 50): Promise<WorkflowExecution[]> {
    const q = new URLSearchParams();
    if (workflowId) q.append('workflow_id', workflowId);
    q.append('limit', String(limit));
    const res = await apiRequest<StandardResponse<WorkflowExecution[]>>(`/workflows/executions?${q.toString()}`);
    return res.data;
  },

  async retryExecution(executionId: string): Promise<WorkflowExecution> {
    const res = await apiRequest<StandardResponse<WorkflowExecution>>(`/workflows/executions/${executionId}/retry`, {
      method: 'POST',
    });
    return res.data;
  },
};

// ==========================================
// 5. NOTIFICATION CENTER SERVICE
// ==========================================
export const notificationCenterService = {
  async getNotifications(unreadOnly = false, limit = 50): Promise<NotificationItem[]> {
    const q = new URLSearchParams();
    if (unreadOnly) q.append('unread_only', 'true');
    q.append('limit', String(limit));
    const res = await apiRequest<StandardResponse<NotificationItem[]>>(`/notifications?${q.toString()}`);
    return res.data;
  },

  async getUnreadCount(): Promise<number> {
    const res = await apiRequest<StandardResponse<{ unread_count: number }>>('/notifications/unread-count');
    return res.data.unread_count;
  },

  async markAsRead(id: string): Promise<NotificationItem> {
    const res = await apiRequest<StandardResponse<NotificationItem>>(`/notifications/${id}/read`, {
      method: 'POST',
    });
    return res.data;
  },

  async markAllAsRead(): Promise<void> {
    await apiRequest<StandardResponse<{ message: string }>>('/notifications/mark-all-read', {
      method: 'POST',
    });
  },
};

// ==========================================
// 6. APPROVALS SERVICE
// ==========================================
export const approvalService = {
  async getApprovals(params?: { status?: string; entityType?: string }): Promise<ApprovalRequest[]> {
    const q = new URLSearchParams();
    if (params?.status) q.append('status', params.status);
    if (params?.entityType) q.append('entity_type', params.entityType);
    const endpoint = `/approvals${q.toString() ? `?${q.toString()}` : ''}`;
    const res = await apiRequest<StandardResponse<ApprovalRequest[]>>(endpoint);
    return res.data;
  },

  async getApproval(id: string): Promise<ApprovalRequest> {
    const res = await apiRequest<StandardResponse<ApprovalRequest>>(`/approvals/${id}`);
    return res.data;
  },

  async requestApproval(payload: ApprovalCreate): Promise<ApprovalRequest> {
    const res = await apiRequest<StandardResponse<ApprovalRequest>>('/approvals', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async decideApproval(id: string, payload: ApprovalDecisionPayload): Promise<ApprovalRequest> {
    const res = await apiRequest<StandardResponse<ApprovalRequest>>(`/approvals/${id}/decision`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },
};
