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

// -------------------------------------------------------------
// PHASE 2 DOMAIN TYPES
// -------------------------------------------------------------

export interface Contact {
  id: string;
  tenant_id: string;
  customer_id: string;
  name: string;
  designation?: string | null;
  email?: string | null;
  phone?: string | null;
  is_primary: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: string;
  tenant_id: string;
  customer_type: 'individual' | 'business' | 'commercial';
  name: string;
  email?: string | null;
  phone?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  country: string;
  status: 'lead' | 'active' | 'inactive';
  source?: string | null;
  notes?: string | null;
  created_by_id?: string | null;
  created_at: string;
  updated_at: string;
  primary_contact_name?: string | null;
  primary_contact_phone?: string | null;
  contacts?: Contact[];
  projects?: Project[];
  payments?: Payment[];
  follow_ups?: FollowUp[];
  notes_list?: Note[];
  documents?: DocumentMetadata[];
  activities?: Activity[];
}

export interface CustomerCreate {
  customer_type?: string;
  name: string;
  email?: string;
  phone?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  status?: string;
  source?: string;
  notes?: string;
  primary_contact_name?: string;
  primary_contact_phone?: string;
  primary_contact_email?: string;
  primary_contact_designation?: string;
}

export interface Product {
  id: string;
  tenant_id: string;
  name: string;
  sku?: string | null;
  category: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PipelineStage {
  id: string;
  tenant_id: string;
  pipeline_id: string;
  name: string;
  order: number;
  color: string;
  is_closed_won: boolean;
  is_closed_lost: boolean;
  is_active?: boolean;
  created_at: string;
  updated_at: string;
}

export interface Pipeline {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  stages: PipelineStage[];
}

export interface ProjectStageHistory {
  id: string;
  project_id: string;
  from_stage_id?: string | null;
  from_stage_name?: string | null;
  to_stage_id: string;
  to_stage_name: string;
  changed_by_id?: string | null;
  changed_by_name?: string | null;
  notes?: string | null;
  changed_at: string;
}

export interface Project {
  id: string;
  tenant_id: string;
  project_number: string;
  name: string;
  customer_id: string;
  product_id?: string | null;
  pipeline_id: string;
  stage_id: string;
  description?: string | null;
  value: string | number;
  currency: string;
  expected_completion_date?: string | null;
  status: string;
  priority: string;
  owner_id?: string | null;
  customer_name?: string | null;
  product_name?: string | null;
  pipeline_name?: string | null;
  stage_name?: string | null;
  stage_color?: string | null;
  owner_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  total_paid: string | number;
  outstanding_amount: string | number;
  stage_history: ProjectStageHistory[];
  payments: Payment[];
}

export interface ProjectCreate {
  name: string;
  customer_id: string;
  product_id?: string;
  pipeline_id?: string;
  stage_id?: string;
  description?: string;
  value?: number | string;
  currency?: string;
  expected_completion_date?: string;
  priority?: string;
}

export interface FollowUp {
  id: string;
  tenant_id: string;
  customer_id: string;
  project_id?: string | null;
  title: string;
  description?: string | null;
  due_date: string;
  status: 'pending' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  completed_at?: string | null;
  completed_notes?: string | null;
  created_by_id?: string | null;
  assigned_to_id?: string | null;
  customer_name?: string | null;
  project_name?: string | null;
  assigned_to_name?: string | null;
  is_overdue: boolean;
  is_today: boolean;
  created_at: string;
  updated_at: string;
}

export interface FollowUpCreate {
  customer_id: string;
  project_id?: string;
  title: string;
  description?: string;
  due_date: string;
  priority?: string;
  assigned_to_id?: string;
}

export interface Payment {
  id: string;
  tenant_id: string;
  customer_id: string;
  project_id: string;
  payment_number: string;
  amount: string | number;
  currency: string;
  payment_date: string;
  payment_method: string;
  reference_number?: string | null;
  status: string;
  notes?: string | null;
  recorded_by_id?: string | null;
  customer_name?: string | null;
  project_name?: string | null;
  project_number?: string | null;
  recorded_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentCreate {
  project_id: string;
  amount: number | string;
  currency?: string;
  payment_date?: string;
  payment_method?: string;
  reference_number?: string;
  notes?: string;
}

export interface PaymentSummary {
  total_project_value: string | number;
  total_paid: string | number;
  total_outstanding: string | number;
  payment_count: number;
}

export interface Note {
  id: string;
  tenant_id: string;
  customer_id?: string | null;
  project_id?: string | null;
  follow_up_id?: string | null;
  payment_id?: string | null;
  author_id?: string | null;
  author_name?: string | null;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentMetadata {
  id: string;
  tenant_id: string;
  customer_id?: string | null;
  project_id?: string | null;
  payment_id?: string | null;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  document_category: string;
  storage_url?: string | null;
  uploaded_by_id?: string | null;
  uploaded_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Activity {
  id: string;
  tenant_id: string;
  customer_id?: string | null;
  project_id?: string | null;
  actor_id?: string | null;
  actor_name?: string | null;
  activity_type: string;
  title: string;
  description?: string | null;
  metadata_json?: string | null;
  created_at: string;
}

export interface SearchResult {
  entity_type: 'customer' | 'project' | 'product';
  id: string;
  title: string;
  subtitle?: string | null;
  details?: string | null;
  url: string;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: SearchResult[];
}

export interface StageDistribution {
  stage_id: string;
  stage_name: string;
  stage_color: string;
  count: number;
  total_value: string | number;
}

export interface CoreDashboardResponse {
  total_customers: number;
  active_projects: number;
  total_project_value: string | number;
  total_paid: string | number;
  total_outstanding: string | number;
  projects_by_stage: StageDistribution[];
  today_follow_ups?: FollowUp[];
  todays_follow_ups?: FollowUp[];
  overdue_follow_ups: FollowUp[];
  recent_customers: Customer[];
  recent_activity: Activity[];
}

// -------------------------------------------------------------
// PHASE 3 PLATFORM CONFIGURABILITY & AUTOMATION TYPES
// -------------------------------------------------------------

export interface PipelineStageCreate {
  name: string;
  order?: number;
  color?: string;
  is_closed_won?: boolean;
  is_closed_lost?: boolean;
  is_active?: boolean;
}

export interface PipelineCreate {
  name: string;
  description?: string;
  is_default?: boolean;
  is_active?: boolean;
  stages?: PipelineStageCreate[];
}

export type CustomFieldType = 'text' | 'number' | 'currency' | 'date' | 'boolean' | 'select';
export type CustomFieldEntityType = 'customer' | 'project' | 'product';

export interface CustomField {
  id: string;
  tenant_id: string;
  entity_type: CustomFieldEntityType;
  field_name: string;
  display_name: string;
  field_type: CustomFieldType;
  is_required: boolean;
  is_searchable: boolean;
  options?: string[];
  is_active: boolean;
  created_at: string;
}

export interface CustomFieldCreate {
  entity_type: CustomFieldEntityType;
  field_name: string;
  display_name: string;
  field_type: CustomFieldType;
  is_required?: boolean;
  is_searchable?: boolean;
  options?: string[];
  is_active?: boolean;
}

export interface CustomFieldValue {
  custom_field_id: string;
  field_name: string;
  display_name: string;
  field_type: string;
  value: unknown;
}

export type ViewEntityType = 'project' | 'customer' | 'payment' | 'follow_up';
export type FilterOperator = '=' | '!=' | '>' | '>=' | '<' | '<=' | 'contains' | 'in' | 'is empty' | 'is not empty';

export interface FilterRule {
  field: string;
  operator: FilterOperator;
  value?: unknown;
}

export interface SavedView {
  id: string;
  tenant_id: string;
  user_id?: string;
  name: string;
  entity_type: ViewEntityType;
  filters: FilterRule[];
  sort_by?: string;
  sort_direction: 'asc' | 'desc';
  visible_columns?: string[];
  is_shared: boolean;
  created_at: string;
}

export interface SavedViewCreate {
  name: string;
  entity_type: ViewEntityType;
  filters: FilterRule[];
  sort_by?: string;
  sort_direction?: 'asc' | 'desc';
  visible_columns?: string[];
  is_shared?: boolean;
}

export interface WorkflowCondition {
  field: string;
  operator: string;
  value?: unknown;
}

export type WorkflowActionType =
  | 'create_follow_up'
  | 'update_record'
  | 'create_notification'
  | 'send_internal_notification'
  | 'assign_record'
  | 'add_activity';

export interface WorkflowAction {
  action_type: WorkflowActionType;
  parameters: Record<string, unknown>;
}

export interface WorkflowDefinition {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  trigger_event: string;
  conditions: WorkflowCondition[];
  actions: WorkflowAction[];
  is_active: boolean;
  created_at: string;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  trigger_event: string;
  conditions?: WorkflowCondition[];
  actions: WorkflowAction[];
  is_active?: boolean;
}

export interface WorkflowExecution {
  id: string;
  tenant_id: string;
  workflow_id: string;
  trigger_event: string;
  entity_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'retrying';
  retry_count: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

export interface NotificationItem {
  id: string;
  tenant_id: string;
  user_id?: string;
  title: string;
  message: string;
  notification_type: 'info' | 'warning' | 'alert' | 'success';
  entity_type?: string;
  entity_id?: string;
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

export interface ApprovalDecision {
  id: string;
  approval_request_id: string;
  decided_by_id: string;
  decision: 'approved' | 'rejected';
  comments?: string;
  decided_at: string;
}

export interface ApprovalRequest {
  id: string;
  tenant_id: string;
  entity_type: string;
  entity_id: string;
  requested_by_id: string;
  status: 'pending' | 'approved' | 'rejected';
  approval_type: string;
  requested_at: string;
  decided_at?: string;
  decided_by_id?: string;
  decision_comments?: string;
  decisions?: ApprovalDecision[];
}

export interface ApprovalCreate {
  entity_type: string;
  entity_id: string;
  approval_type?: string;
}

export interface ApprovalDecisionPayload {
  decision: 'approved' | 'rejected';
  comments?: string;
}

