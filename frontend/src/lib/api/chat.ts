import apiClient from "./client";
import type { Conversation, Message, CreateConversationRequest, CreateMessageRequest } from "@/types";

export const chatApi = {
  async getConversations(): Promise<Conversation[]> {
    return apiClient.get<Conversation[]>("/conversations");
  },

  async getConversation(id: string): Promise<Conversation> {
    return apiClient.get<Conversation>(`/conversations/${id}`);
  },

  async createConversation(data?: CreateConversationRequest): Promise<Conversation> {
    return apiClient.post<Conversation>("/conversations", data || {});
  },

  async updateConversation(id: string, data: { title?: string }): Promise<Conversation> {
    return apiClient.patch<Conversation>(`/conversations/${id}`, data);
  },

  async deleteConversation(id: string): Promise<void> {
    return apiClient.delete(`/conversations/${id}`);
  },

  async sendMessage(conversationId: string, data: CreateMessageRequest): Promise<Message> {
    return apiClient.post<Message>(`/conversations/${conversationId}/messages`, data);
  },

  async regenerateMessage(messageId: string): Promise<Message> {
    return apiClient.post<Message>(`/messages/${messageId}/regenerate`);
  },

  async editMessage(messageId: string, content: string): Promise<Message> {
    return apiClient.patch<Message>(`/messages/${messageId}`, { content });
  },

  async deleteMessage(messageId: string): Promise<void> {
    return apiClient.delete(`/messages/${messageId}`);
  },

  // Streaming chat with SSE
  async *streamMessage(
    conversationId: string,
    data: CreateMessageRequest
  ): AsyncGenerator<{ type: string; content?: string }, void, unknown> {
    const token = localStorage.getItem("access_token");
    
    const response = await fetch(`/api/v1/conversations/${conversationId}/messages/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || "Failed to stream message");
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const jsonStr = line.slice(6);
            if (jsonStr === "[DONE]") {
              return;
            }
            const data = JSON.parse(jsonStr);
            yield data;
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }
  },

  async *streamAgentMessage(
    conversationId: string,
    data: CreateMessageRequest
  ): AsyncGenerator<{ type: string; content?: string; step?: unknown }, void, unknown> {
    const token = localStorage.getItem("access_token");
    
    const response = await fetch(`/api/v1/conversations/${conversationId}/messages/agent/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || "Failed to stream agent message");
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const jsonStr = line.slice(6);
            if (jsonStr === "[DONE]") {
              return;
            }
            const data = JSON.parse(jsonStr);
            yield data;
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }
  },
};

export default chatApi;
