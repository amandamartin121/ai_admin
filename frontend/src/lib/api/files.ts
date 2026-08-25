import apiClient from "./client";
import type { FileDocument } from "@/types";

export const filesApi = {
  async getFiles(): Promise<FileDocument[]> {
    return apiClient.get<FileDocument[]>("/files");
  },

  async getFile(id: string): Promise<FileDocument> {
    return apiClient.get<FileDocument>(`/files/${id}`);
  },

  async uploadFile(file: File): Promise<{ file: FileDocument }> {
    return apiClient.uploadFile("/files", file) as Promise<{ file: FileDocument }>;
  },

  async deleteFile(id: string): Promise<void> {
    return apiClient.delete(`/files/${id}`);
  },

  async downloadFile(id: string): Promise<Blob> {
    const token = localStorage.getItem("access_token");
    
    const response = await fetch(`/api/v1/files/${id}/download`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || "Failed to download file");
    }

    return response.blob();
  },
};

export default filesApi;
