export interface Organization {
  id: string;
  name: string;
  slug: string;
  tier: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  role_name?: string;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  organization: Organization;
}

export interface StandardResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface ApiError {
  code: string;
  message: string;
  request_id: string;
  details?: unknown;
}

export interface AuditLog {
  id: string;
  tenant_id: string;
  actor_id?: string;
  actor_email?: string;
  action: string;
  resource: string;
  resource_id?: string;
  ip_address?: string;
  user_agent?: string;
  metadata_json?: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DependencyStatus {
  status: 'healthy' | 'unhealthy' | 'degraded';
  latency_ms?: number;
  error?: string;
}

export interface ReadinessResponse {
  status: 'ready' | 'not_ready';
  dependencies: Record<string, DependencyStatus>;
  timestamp: string;
}

export interface HealthCheckResponse {
  status: string;
  version: string;
  timestamp: string;
}
