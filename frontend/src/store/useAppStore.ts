import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, Message, Conversation, AgentActivity, Task, VoiceState, Memory } from "@/types";

interface AppState {
  // Auth
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;

  // Active conversation
  activeConversationId: string | null;
  setActiveConversation: (id: string | null) => void;

  // Messages
  messages: Message[];
  addMessage: (msg: Message) => void;
  updateLastMessage: (content: string, done?: boolean) => void;
  clearMessages: () => void;
  setMessages: (msgs: Message[]) => void;

  // Agent activity
  agentActivities: AgentActivity[];
  addAgentActivity: (activity: AgentActivity) => void;
  clearAgentActivities: () => void;

  // Voice state
  voiceState: VoiceState;
  setVoiceState: (state: VoiceState) => void;

  // Ava visual details
  avatarAction: string;
  avatarEmotion: string;
  setAvatarAction: (action: string) => void;
  setAvatarEmotion: (emotion: string) => void;

  // Mode: "chat" | "voice"
  mode: "chat" | "voice";
  setMode: (mode: "chat" | "voice") => void;

  // Tasks
  tasks: Task[];
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  removeTask: (id: string) => void;

  // Memories
  memories: Memory[];
  setMemories: (memories: Memory[]) => void;
  addMemory: (memory: Memory) => void;
  removeMemory: (id: string) => void;

  // UI
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  theme: "dark" | "light";
  setTheme: (theme: "dark" | "light") => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  // Settings
  selectedVoice: string;
  setSelectedVoice: (voice: string) => void;
  ttsEnabled: boolean;
  setTtsEnabled: (enabled: boolean) => void;
  autoListen: boolean;
  setAutoListen: (enabled: boolean) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Auth
      user: null,
      token: null,
      setAuth: (user, token) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", token);
          localStorage.setItem("user", JSON.stringify(user));
        }
        set({ user, token });
      },
      logout: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
        }
        set({ user: null, token: null, messages: [], activeConversationId: null });
      },

      // Conversation
      activeConversationId: null,
      setActiveConversation: (id) => set({ activeConversationId: id }),

      // Messages
      messages: [],
      addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
      updateLastMessage: (content, done = false) =>
        set((s) => {
          const msgs = [...s.messages];
          const last = msgs[msgs.length - 1];
          if (last && last.role === "assistant") {
            msgs[msgs.length - 1] = {
              ...last,
              content: done ? last.content : (last.isStreaming ? last.content + content : content),
              isStreaming: !done,
            };
          }
          return { messages: msgs };
        }),
      clearMessages: () => set({ messages: [] }),
      setMessages: (msgs) => set({ messages: msgs }),

      // Agent activities
      agentActivities: [],
      addAgentActivity: (activity) =>
        set((s) => ({ agentActivities: [...s.agentActivities, activity] })),
      clearAgentActivities: () => set({ agentActivities: [] }),

      // Voice
      voiceState: "idle",
      setVoiceState: (voiceState) => set({ voiceState }),

      // Ava visual details
      avatarAction: "idle",
      avatarEmotion: "calm",
      setAvatarAction: (avatarAction) => set({ avatarAction }),
      setAvatarEmotion: (avatarEmotion) => set({ avatarEmotion }),

      // Mode
      mode: "chat",
      setMode: (mode) => set({ mode }),

      // Tasks
      tasks: [],
      setTasks: (tasks) => set({ tasks }),
      addTask: (task) => set((s) => ({ tasks: [task, ...s.tasks] })),
      updateTask: (id, updates) =>
        set((s) => ({
          tasks: s.tasks.map((t) => (t.id === id ? { ...t, ...updates } : t)),
        })),
      removeTask: (id) => set((s) => ({ tasks: s.tasks.filter((t) => t.id !== id) })),

      // Memories
      memories: [],
      setMemories: (memories) => set({ memories }),
      addMemory: (memory) => set((s) => ({ memories: [memory, ...s.memories] })),
      removeMemory: (id) =>
        set((s) => ({ memories: s.memories.filter((m) => m.id !== id) })),

      // UI
      sidebarOpen: true,
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
      theme: "dark",
      setTheme: (theme) => set({ theme }),
      isLoading: false,
      setIsLoading: (isLoading) => set({ isLoading }),

      // Settings
      selectedVoice: "alloy",
      setSelectedVoice: (selectedVoice) => set({ selectedVoice }),
      ttsEnabled: true,
      setTtsEnabled: (ttsEnabled) => set({ ttsEnabled }),
      autoListen: false,
      setAutoListen: (autoListen) => set({ autoListen }),
    }),
    {
      name: "voice-agent-store",
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        theme: state.theme,
        selectedVoice: state.selectedVoice,
        ttsEnabled: state.ttsEnabled,
        autoListen: state.autoListen,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);
