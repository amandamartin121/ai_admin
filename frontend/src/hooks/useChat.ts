import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { chatApi } from "@/lib/api";
import { useChatStore } from "@/stores";
import type { CreateMessageRequest, CreateConversationRequest } from "@/types";

export function useChat() {
  const queryClient = useQueryClient();
  const { 
    conversations, 
    setConversations, 
    addConversation, 
    updateConversation, 
    removeConversation,
    setActiveConversation,
    addMessageToConversation,
  } = useChatStore();

  const { data: conversationsData, isLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => chatApi.getConversations(),
    onSuccess: (data) => setConversations(data),
  });

  const createConversationMutation = useMutation({
    mutationFn: (data?: CreateConversationRequest) => chatApi.createConversation(data),
    onSuccess: (conversation) => {
      addConversation(conversation);
      setActiveConversation(conversation.id);
    },
  });

  const deleteConversationMutation = useMutation({
    mutationFn: (id: string) => chatApi.deleteConversation(id),
    onSuccess: (_, id) => {
      removeConversation(id);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  const updateConversationMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string } }) =>
      chatApi.updateConversation(id, data),
    onSuccess: (conversation) => {
      updateConversation(conversation);
    },
  });

  return {
    conversations,
    isLoading,
    createConversation: createConversationMutation.mutateAsync,
    deleteConversation: deleteConversationMutation.mutateAsync,
    updateConversation: updateConversationMutation.mutateAsync,
    setActiveConversation,
    isCreating: createConversationMutation.isPending,
    isDeleting: deleteConversationMutation.isPending,
  };
}

export function useConversation(conversationId: string | null) {
  const queryClient = useQueryClient();
  const { addMessageToConversation } = useChatStore();

  const { data: conversation, isLoading } = useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => conversationId ? chatApi.getConversation(conversationId) : null,
    enabled: !!conversationId,
  });

  const sendMessageMutation = useMutation({
    mutationFn: ({ content, mode, model_name, attachment_ids }: CreateMessageRequest) => {
      if (!conversationId) throw new Error("No active conversation");
      return chatApi.sendMessage(conversationId, { content, mode, model_name, attachment_ids });
    },
    onSuccess: (message) => {
      if (conversationId) {
        addMessageToConversation(conversationId, message);
      }
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  return {
    conversation: conversation || null,
    isLoading,
    sendMessage: sendMessageMutation.mutateAsync,
    isSending: sendMessageMutation.isPending,
  };
}

export default useChat;
