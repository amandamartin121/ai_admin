import { useState, useRef, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useChat, useConversation } from "@/hooks";
import { useAuthStore } from "@/stores";
import { Send, Plus, StopCircle, Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { conversations, createConversation, setActiveConversation } = useChat();
  const { conversation, sendMessage, isSending } = useConversation(conversationId || null);
  const { hasAgentAccess } = useAuthStore();
  
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState<"chat" | "agent">("chat");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation?.messages]);

  const handleNewChat = async () => {
    try {
      const newConv = await createConversation({ mode, title: "New Conversation" });
      setActiveConversation(newConv.id);
    } catch (err) {
      console.error("Failed to create conversation:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isSending) return;

    const content = message.trim();
    setMessage("");

    try {
      await sendMessage({ content, mode });
    } catch (err) {
      console.error("Failed to send message:", err);
      setMessage(content); // Restore message on error
    }
  };

  const currentConversation = conversation || conversations.find(c => c.id === conversationId);

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Conversations sidebar */}
      <div className="w-64 flex-shrink-0 overflow-y-auto rounded-lg border bg-card p-2">
        <Button onClick={handleNewChat} size="sm" className="mb-2 w-full">
          <Plus className="mr-2 h-4 w-4" />
          New Chat
        </Button>
        <div className="space-y-1">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => setActiveConversation(conv.id)}
              className={`w-full truncate rounded-md px-3 py-2 text-left text-sm ${
                conv.id === conversationId
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              }`}
            >
              {conv.title || "Untitled"}
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex flex-1 flex-col overflow-hidden rounded-lg border bg-card">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          {!currentConversation || currentConversation.messages.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center text-muted-foreground">
                <Bot className="mx-auto mb-4 h-12 w-12" />
                <h2 className="text-xl font-semibold">Start a conversation</h2>
                <p>Send a message to begin chatting with AI</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {currentConversation.messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                >
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-full ${
                      msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                    }`}
                  >
                    {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Composer */}
        <form onSubmit={handleSubmit} className="border-t p-4">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Mode:</span>
            <Button
              type="button"
              variant={mode === "chat" ? "default" : "outline"}
              size="sm"
              onClick={() => setMode("chat")}
            >
              Chat
            </Button>
            <Button
              type="button"
              variant={mode === "agent" ? "default" : "outline"}
              size="sm"
              onClick={() => setMode("agent")}
              disabled={!hasAgentAccess()}
              title={!hasAgentAccess() ? "Agent access not granted" : undefined}
            >
              Agent
            </Button>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={isSending ? "AI is responding..." : "Type your message..."}
              disabled={isSending}
              className="flex-1 rounded-md border bg-background px-4 py-2 focus:outline-none focus:ring-2 focus:ring-ring"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            <Button type="submit" size="icon" disabled={isSending || !message.trim()}>
              {isSending ? <StopCircle className="h-4 w-4" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
