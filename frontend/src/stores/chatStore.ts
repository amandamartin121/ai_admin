import { create } from "zustand";
import type { Conversation, Message, AgentRun } from "@/types";

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  isLoading: boolean;
  isGenerating: boolean;
  agentRun: AgentRun | null;
  
  // Actions
  setConversations: (conversations: Conversation[]) => void;
  addConversation: (conversation: Conversation) => void;
  updateConversation: (conversation: Conversation) => void;
  removeConversation: (id: string) => void;
  setActiveConversation: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setGenerating: (generating: boolean) => void;
  setAgentRun: (run: AgentRun | null) => void;
  addMessageToConversation: (conversationId: string, message: Message) => void;
  clearActiveConversation: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  isLoading: false,
  isGenerating: false,
  agentRun: null,

  setConversations: (conversations) => set({ conversations }),
  
  addConversation: (conversation) =>
    set((state) => ({
      conversations: [conversation, ...state.conversations],
    })),
  
  updateConversation: (conversation) =>
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === conversation.id ? conversation : c
      ),
    })),
  
  removeConversation: (id) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      activeConversationId: state.activeConversationId === id ? null : state.activeConversationId,
    })),
  
  setActiveConversation: (id) => set({ activeConversationId: id }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setGenerating: (generating) => set({ isGenerating: generating }),
  
  setAgentRun: (run) => set({ agentRun: run }),
  
  addMessageToConversation: (conversationId, message) =>
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === conversationId
          ? { ...c, messages: [...c.messages, message], updated_at: new Date().toISOString() }
          : c
      ),
    })),
  
  clearActiveConversation: () => set({ activeConversationId: null }),
}));

export default useChatStore;
