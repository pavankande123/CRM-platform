import { apiRequest } from './apiClient';
import type { AuditLog, PaginatedResponse, StandardResponse } from '../types';

export const auditService = {
  async getAuditLogs(
    page: number = 1,
    pageSize: number = 20,
    action?: string,
    resource?: string
  ): Promise<PaginatedResponse<AuditLog>> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (action) params.append('action', action);
    if (resource) params.append('resource', resource);

    const res = await apiRequest<StandardResponse<PaginatedResponse<AuditLog>>>(
      `/audit/logs?${params.toString()}`
    );
    return res.data;
  },
};
