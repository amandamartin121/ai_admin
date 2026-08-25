import type { ApiError } from "@/types";

const BASE_URL = "/api/v1";

export class ApiClientError extends Error {
  code: string;
  request_id?: string;
  details?: Record<string, string[]>;

  constructor(error: ApiError) {
    super(error.message);
    this.code = error.code;
    this.request_id = error.request_id;
    this.details = error.details;
    this.name = "ApiClientError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiClientError({
      code: errorData.code || "UNKNOWN_ERROR",
      message: errorData.message || "An unexpected error occurred",
      request_id: errorData.request_id,
      details: errorData.details,
    });
  }
  
  // Handle empty responses
  const contentType = response.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    return response.json();
  }
  return {} as T;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("access_token");
  
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  return handleResponse<T>(response);
}

export const apiClient = {
  async get<T>(endpoint: string): Promise<T> {
    return request<T>(endpoint, { method: "GET" });
  },

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  async patch<T>(endpoint: string, data?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  async delete<T>(endpoint: string): Promise<T> {
    return request<T>(endpoint, { method: "DELETE" });
  },

  async uploadFile(endpoint: string, file: File): Promise<unknown> {
    const token = localStorage.getItem("access_token");
    
    const formData = new FormData();
    formData.append("file", file);

    const headers: HeadersInit = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: "POST",
      headers,
      body: formData,
    });

    return handleResponse(response);
  },

  setToken(token: string) {
    localStorage.setItem("access_token", token);
  },

  getToken(): string | null {
    return localStorage.getItem("access_token");
  },

  clearToken() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  },

  setRefreshToken(token: string) {
    localStorage.setItem("refresh_token", token);
  },

  getRefreshToken(): string | null {
    return localStorage.getItem("refresh_token");
  },
};

export default apiClient;
