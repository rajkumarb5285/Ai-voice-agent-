import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token from localStorage
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 — redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    return Promise.reject(err);
  }
);


// ─── Auth ────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post("/api/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/api/auth/login", data),
  firebaseLogin: (id_token: string) =>
    api.post("/api/auth/firebase-login", { id_token }),
  me: () => api.get("/api/auth/me"),
};


// ─── Chat ────────────────────────────────────────────────────────────────────
export const chatApi = {
  send: (message: string, conversationId?: string, mode = "chat") =>
    api.post("/api/chat/", { message, conversation_id: conversationId, mode }),
  listConversations: () => api.get("/api/chat/conversations"),
  getMessages: (conversationId: string, limit = 50) =>
    api.get(`/api/chat/conversations/${conversationId}/messages`, { params: { limit } }),
};

// ─── Voice ───────────────────────────────────────────────────────────────────
export const voiceApi = {
  transcribe: async (audioBlob: Blob, language?: string) => {
    const form = new FormData();
    form.append("audio", audioBlob, "audio.webm");
    if (language) form.append("language", language);
    return api.post("/api/voice/transcribe", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  synthesize: (text: string, voice?: string) =>
    api.post("/api/voice/synthesize", { text, voice }),
  synthesizeStream: (text: string, voice?: string): string => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : "";
    const params = new URLSearchParams({ text, ...(voice && { voice }) });
    const base = API_URL || (typeof window !== "undefined" ? window.location.origin : "");
    return `${base}/api/voice/synthesize/stream?${params}&token=${token}`;
  },
  listVoices: () => api.get("/api/voice/voices"),
};

// ─── Memory ──────────────────────────────────────────────────────────────────
export const memoryApi = {
  list: (params?: { memory_type?: string; category?: string; limit?: number }) =>
    api.get("/api/memory/", { params }),
  create: (data: { content: string; category?: string; title?: string; importance_score?: number }) =>
    api.post("/api/memory/", data),
  search: (query: string, n_results = 5) =>
    api.post("/api/memory/search", { query, n_results }),
  delete: (id: string) => api.delete(`/api/memory/${id}`),
  getProfile: () => api.get("/api/memory/profile"),
  updateProfile: (updates: Record<string, unknown>) =>
    api.patch("/api/memory/profile", updates),
};

// ─── Tasks ───────────────────────────────────────────────────────────────────
export const tasksApi = {
  list: (params?: { status?: string; priority?: string }) =>
    api.get("/api/tasks/", { params }),
  create: (data: { title: string; description?: string; priority?: string; due_date?: string }) =>
    api.post("/api/tasks/", data),
  update: (id: string, data: Partial<{ status: string; priority: string; title: string }>) =>
    api.patch(`/api/tasks/${id}`, data),
  delete: (id: string) => api.delete(`/api/tasks/${id}`),
  summary: () => api.get("/api/tasks/summary"),
};
