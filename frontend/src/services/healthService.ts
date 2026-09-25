import { apiRequest } from './apiClient';
import type { HealthCheckResponse, ReadinessResponse } from '../types';

export const healthService = {
  async getHealth(): Promise<HealthCheckResponse> {
    return await apiRequest<HealthCheckResponse>('/health', { skipAuth: true });
  },

  async getReadiness(): Promise<ReadinessResponse> {
    return await apiRequest<ReadinessResponse>('/ready', { skipAuth: true });
  },
};
