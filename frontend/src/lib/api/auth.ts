import apiClient from "./client";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
  ChangePasswordRequest,
} from "@/types";

export const authApi = {
  async login(data: LoginRequest): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>("/auth/login", data);
  },

  async register(data: RegisterRequest): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>("/auth/register", data);
  },

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>("/auth/refresh", { refresh_token: refreshToken });
  },

  async logout(): Promise<void> {
    return apiClient.post("/auth/logout");
  },

  async getMe(): Promise<User> {
    return apiClient.get<User>("/auth/me");
  },

  async changePassword(data: ChangePasswordRequest): Promise<void> {
    return apiClient.post("/auth/change-password", data);
  },

  async getSessions(): Promise<unknown[]> {
    return apiClient.get("/auth/sessions");
  },

  async revokeSession(sessionId: string): Promise<void> {
    return apiClient.delete(`/auth/sessions/${sessionId}`);
  },
};

export default authApi;
