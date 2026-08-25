// User & Authentication
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserRole {
  id: string;
  user_id: string;
  role_id: string;
  role: Role;
}

export interface Role {
  id: string;
  name: string;
  description: string | null;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  description: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

// Conversations & Messages
export interface Conversation {
  id: string;
  title: string;
  user_id: string;
  mode: "chat" | "agent";
  model_name: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  attachments?: MessageAttachment[];
  agent_steps?: AgentStep[];
}

export interface MessageAttachment {
  id: string;
  message_id: string;
  file_id: string;
  file: FileDocument;
}

export interface CreateMessageRequest {
  content: string;
  mode?: "chat" | "agent";
  model_name?: string;
  attachment_ids?: string[];
}

export interface CreateConversationRequest {
  title?: string;
  mode?: "chat" | "agent";
  model_name?: string;
}

// Files
export interface FileDocument {
  id: string;
  filename: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  user_id: string;
  created_at: string;
}

export interface UploadFileResponse {
  file: FileDocument;
}

// Agents
export interface AgentRun {
  id: string;
  conversation_id: string;
  status: "pending" | "running" | "completed" | "failed" | "waiting_approval";
  current_step: string | null;
  created_at: string;
  updated_at: string;
  steps: AgentStep[];
}

export interface AgentStep {
  id: string;
  run_id: string;
  step_type: string;
  status: "pending" | "running" | "completed" | "failed" | "waiting_approval";
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  result_summary?: string;
  error_message?: string;
  duration_ms?: number;
  created_at: string;
  updated_at: string;
}

export interface ApprovalRequest {
  id: string;
  agent_step_id: string;
  tool_name: string;
  tool_args: Record<string, unknown>;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  reason: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
}

export interface ApproveRequest {
  approved: boolean;
  reason?: string;
}

// Models & Providers
export interface LLMProvider {
  id: string;
  name: string;
  provider_type: string;
  base_url: string;
  is_active: boolean;
}

export interface LLMModel {
  id: string;
  provider_id: string;
  name: string;
  display_name: string;
  max_tokens: number;
  supports_tools: boolean;
  is_active: boolean;
}

// Admin
export interface CreateUserRequest {
  email: string;
  password: string;
  full_name?: string;
  is_active?: boolean;
  role_ids?: string[];
}

export interface UpdateUserRequest {
  email?: string;
  full_name?: string;
  is_active?: boolean;
  role_ids?: string[];
}

export interface AuditLog {
  id: string;
  actor_user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  timestamp: string;
  ip_address: string | null;
  user_agent: string | null;
  metadata: Record<string, unknown> | null;
}

// API Error
export interface ApiError {
  code: string;
  message: string;
  request_id?: string;
  details?: Record<string, string[]>;
}

// Permissions check
export interface UserPermissions {
  chat_access: boolean;
  agent_access: boolean;
  files_upload: boolean;
  admin_access: boolean;
  permissions: string[];
}
