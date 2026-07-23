"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import { motion, AnimatePresence } from "framer-motion";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { InputBar } from "@/components/chat/InputBar";
import { AgentActivityPanel } from "@/components/agents/AgentActivityPanel";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useAppStore } from "@/store/useAppStore";
import { chatApi } from "@/lib/api";
import {
  MessageSquare, Wifi, WifiOff, Plus, ChevronRight,
  Clock, Sparkles, AlertTriangle,
} from "lucide-react";

interface Conversation {
  id: string;
  title: string;
  mode: string;
  updated_at: string;
}

export default function ChatPage() {
  const conversationIdRef = useRef(uuidv4());
  const {
    activeConversationId, setActiveConversation,
    clearMessages, setMessages, token,
  } = useAppStore();

  const { sendMessage, isConnected, isStreaming, connect, disconnect } = useWebSocket();
  const connectRef = useRef(connect);
  const disconnectRef = useRef(disconnect);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [isMockKey, setIsMockKey] = useState(false);

  useEffect(() => {
    connectRef.current = connect;
    disconnectRef.current = disconnect;
  }, [connect, disconnect]);

  // Connect WS once token is ready
  useEffect(() => {
    if (!token) return;
    const id = conversationIdRef.current;
    setActiveConversation(id);
    connectRef.current(id);
    return () => { disconnectRef.current(); };
  }, [token, setActiveConversation]);

  // Load conversation list
  const loadConversations = useCallback(async () => {
    try {
      const res = await chatApi.listConversations();
      setConversations(res.data);
    } catch { /* silent */ }
  }, []);

  useEffect(() => { loadConversations(); }, [loadConversations]);

  // Check if using mock API key
  useEffect(() => {
    const isMock = typeof window !== "undefined" &&
      (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");
    if (isMock) {
      // Probe the backend /health endpoint for mock key indicator
      fetch("/api/health").then(r => r.json()).then(data => {
        setIsMockKey(data?.mock_llm === true);
      }).catch(() => {});
    }
  }, []);

  // Switch to a past conversation
  const switchConversation = async (conv: Conversation) => {
    setLoadingHistory(true);
    disconnectRef.current();
    clearMessages();
    conversationIdRef.current = conv.id;
    setActiveConversation(conv.id);

    try {
      const res = await chatApi.getMessages(conv.id);
      setMessages(
        res.data.map((m: { id: string; role: string; content: string }) => ({
          id: m.id,
          role: m.role as "user" | "assistant",
          content: m.content,
          isStreaming: false,
        }))
      );
    } catch { /* silent */ } finally {
      setLoadingHistory(false);
    }
    connectRef.current(conv.id);
  };

  // Start a new conversation
  const newConversation = () => {
    const newId = uuidv4();
    conversationIdRef.current = newId;
    clearMessages();
    disconnectRef.current();
    connectRef.current(newId);
    setActiveConversation(newId);
    loadConversations();
  };

  const handleSend = (message: string, mode = "chat") => {
    sendMessage(message, mode);
    // Refresh conversation list after first message
    setTimeout(loadConversations, 2000);
  };

  return (
    <div className="flex h-full">
      {/* ── Conversation history sidebar ── */}
      <AnimatePresence>
        {showSidebar && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 240, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col border-r border-white/[0.04] bg-[#09090e]/60 backdrop-blur-sm overflow-hidden flex-shrink-0"
          >
            {/* Sidebar header */}
            <div className="flex items-center justify-between px-4 py-3.5 border-b border-white/[0.04]">
              <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">History</span>
              <button
                onClick={newConversation}
                className="flex items-center gap-1 text-[10px] font-bold text-brand-400 hover:text-brand-300 bg-brand-500/10 hover:bg-brand-500/20 border border-brand-500/20 px-2.5 py-1 rounded-lg transition-all"
              >
                <Plus className="w-3 h-3" /> New
              </button>
            </div>

            {/* Conversation list */}
            <div className="flex-1 overflow-y-auto py-2 space-y-0.5 px-2">
              {conversations.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-2 py-8">
                  <MessageSquare className="w-6 h-6 text-white/10" />
                  <p className="text-[10px] text-white/25 text-center px-2">
                    Start chatting to see conversations here
                  </p>
                </div>
              ) : (
                conversations.map((conv) => {
                  const isActive = conv.id === activeConversationId;
                  return (
                    <button
                      key={conv.id}
                      onClick={() => switchConversation(conv)}
                      className={`w-full text-left px-3 py-2.5 rounded-xl transition-all duration-200 group ${
                        isActive
                          ? "bg-brand-500/10 border border-brand-500/20 text-white"
                          : "hover:bg-white/[0.03] text-white/50 hover:text-white/80"
                      }`}
                    >
                      <p className="text-xs font-semibold truncate leading-tight">
                        {conv.title || "New conversation"}
                      </p>
                      <div className="flex items-center gap-1 mt-1">
                        <Clock className="w-2.5 h-2.5 text-white/20" />
                        <span className="text-[9px] text-white/25 font-medium">
                          {new Date(conv.updated_at).toLocaleDateString([], {
                            month: "short", day: "numeric",
                          })}
                        </span>
                        {isActive && (
                          <span className="ml-auto">
                            <ChevronRight className="w-3 h-3 text-brand-400" />
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Main chat panel ── */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-5 h-14 border-b border-white/[0.04] bg-surface-1/60 backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="p-1.5 rounded-lg hover:bg-white/[0.04] text-white/40 hover:text-white transition-all"
              title="Toggle history"
            >
              <MessageSquare className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-400" />
              <h1 className="text-sm font-bold text-white tracking-wide">Chat</h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Connection pill */}
            <motion.div
              animate={{ opacity: 1 }}
              className={`flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border ${
                isConnected
                  ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                  : "text-amber-400 bg-amber-500/10 border-amber-500/20"
              }`}
            >
              {isConnected ? (
                <>
                  <motion.div
                    className="w-1.5 h-1.5 rounded-full bg-emerald-400"
                    animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                  <Wifi className="w-3 h-3" /> Live
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3" /> Connecting...
                </>
              )}
            </motion.div>

            {/* New chat button */}
            <button
              onClick={newConversation}
              className="flex items-center gap-1.5 text-xs text-white/50 hover:text-white px-3 py-1.5 rounded-lg hover:bg-white/[0.04] border border-transparent hover:border-white/[0.06] transition-all"
            >
              <Plus className="w-3.5 h-3.5" /> New Chat
            </button>
          </div>
        </div>

        {/* Mock API key banner */}
        <AnimatePresence>
          {isMockKey && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="flex items-center gap-2.5 px-5 py-2.5 bg-amber-500/8 border-b border-amber-500/15"
            >
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <p className="text-xs text-amber-300/80 font-medium">
                Running in <span className="font-bold">mock mode</span> — responses are simulated.
                Add your <span className="font-bold">OPENAI_API_KEY</span> to{" "}
                <code className="bg-amber-500/10 px-1.5 py-0.5 rounded text-amber-200">.env</code>{" "}
                and restart to enable real AI.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto relative">
          {loadingHistory ? (
            <div className="flex items-center justify-center h-full gap-2 text-white/30 text-sm">
              <motion.div
                className="w-4 h-4 border-2 border-brand-400 border-t-transparent rounded-full"
                animate={{ rotate: 360 }}
                transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
              />
              Loading conversation...
            </div>
          ) : (
            <ChatWindow isStreaming={isStreaming} onSendMessage={handleSend} />
          )}
        </div>

        {/* Agent activity ticker */}
        <AgentActivityPanel />

        {/* Input bar */}
        <InputBar
          onSendMessage={handleSend}
          isStreaming={isStreaming}
          isConnected={isConnected}
        />
      </div>
    </div>
  );
}
