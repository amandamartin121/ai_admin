import apiClient from "./client";
import type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
  Role,
  Permission,
  AuditLog,
  LLMModel,
  LLMProvider,
} from "@/types";

export const adminApi = {
  // Users
  async getUsers(params?: {
    page?: number;
    limit?: number;
    search?: string;
    is_active?: boolean;
  }): Promise<{ users: User[]; total: number }> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set("page", params.page.toString());
    if (params?.limit) queryParams.set("limit", params.limit.toString());
    if (params?.search) queryParams.set("search", params.search);
    if (params?.is_active !== undefined) queryParams.set("is_active", params.is_active.toString());
    
    const query = queryParams.toString();
    return apiClient.get(`/admin/users${query ? `?${query}` : ""}`);
  },

  async getUser(id: string): Promise<User> {
    return apiClient.get<User>(`/admin/users/${id}`);
  },

  async createUser(data: CreateUserRequest): Promise<User> {
    return apiClient.post<User>("/admin/users", data);
  },

  async updateUser(id: string, data: UpdateUserRequest): Promise<User> {
    return apiClient.patch<User>(`/admin/users/${id}`, data);
  },

  async deleteUser(id: string): Promise<void> {
    return apiClient.delete(`/admin/users/${id}`);
  },

  async assignRoles(userId: string, roleIds: string[]): Promise<User> {
    return apiClient.post<User>(`/admin/users/${userId}/roles`, { role_ids: roleIds });
  },

  async resetPassword(userId: string, newPassword: string): Promise<void> {
    return apiClient.post(`/admin/users/${userId}/reset-password`, { new_password: newPassword });
  },

  // Roles
  async getRoles(): Promise<Role[]> {
    return apiClient.get<Role[]>("/admin/roles");
  },

  async createRole(data: { name: string; description?: string }): Promise<Role> {
    return apiClient.post<Role>("/admin/roles", data);
  },

  async updateRole(id: string, data: { name?: string; description?: string }): Promise<Role> {
    return apiClient.patch<Role>(`/admin/roles/${id}`, data);
  },

  async deleteRole(id: string): Promise<void> {
    return apiClient.delete(`/admin/roles/${id}`);
  },

  async assignPermissionsToRole(roleId: string, permissionNames: string[]): Promise<Role> {
    return apiClient.post<Role>(`/admin/roles/${roleId}/permissions`, { permission_names: permissionNames });
  },

  // Permissions
  async getPermissions(): Promise<Permission[]> {
    return apiClient.get<Permission[]>("/admin/permissions");
  },

  // Audit Logs
  async getAuditLogs(params?: {
    page?: number;
    limit?: number;
    action?: string;
    user_id?: string;
  }): Promise<{ logs: AuditLog[]; total: number }> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set("page", params.page.toString());
    if (params?.limit) queryParams.set("limit", params.limit.toString());
    if (params?.action) queryParams.set("action", params.action);
    if (params?.user_id) queryParams.set("user_id", params.user_id);
    
    const query = queryParams.toString();
    return apiClient.get(`/admin/audit-logs${query ? `?${query}` : ""}`);
  },

  // Models
  async getModels(): Promise<LLMModel[]> {
    return apiClient.get<LLMModel[]>("/admin/models");
  },

  async createModel(data: {
    provider_id: string;
    name: string;
    display_name: string;
    max_tokens?: number;
    supports_tools?: boolean;
  }): Promise<LLMModel> {
    return apiClient.post<LLMModel>("/admin/models", data);
  },

  async updateModel(
    id: string,
    data: {
      display_name?: string;
      max_tokens?: number;
      supports_tools?: boolean;
      is_active?: boolean;
    }
  ): Promise<LLMModel> {
    return apiClient.patch<LLMModel>(`/admin/models/${id}`, data);
  },

  async deleteModel(id: string): Promise<void> {
    return apiClient.delete(`/admin/models/${id}`);
  },

  // Providers
  async getProviders(): Promise<LLMProvider[]> {
    return apiClient.get<LLMProvider[]>("/admin/providers");
  },

  async createProvider(data: {
    name: string;
    provider_type: string;
    base_url: string;
    api_key?: string;
  }): Promise<LLMProvider> {
    return apiClient.post<LLMProvider>("/admin/providers", data);
  },

  async updateProvider(
    id: string,
    data: {
      name?: string;
      base_url?: string;
      api_key?: string;
      is_active?: boolean;
    }
  ): Promise<LLMProvider> {
    return apiClient.patch<LLMProvider>(`/admin/providers/${id}`, data);
  },

  async deleteProvider(id: string): Promise<void> {
    return apiClient.delete(`/admin/providers/${id}`);
  },

  // Dashboard stats
  async getDashboardStats(): Promise<{
    total_users: number;
    active_users: number;
    disabled_users: number;
    total_conversations: number;
    total_messages: number;
    total_agent_runs: number;
    failed_agent_runs: number;
  }> {
    return apiClient.get("/admin/dashboard/stats");
  },
};

export default adminApi;
