export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  profile?: UserProfile;
  created_at: string;
}

export interface UserProfile {
  name?: string;
  goals?: string[];
  skills?: string[];
  timezone?: string;
  language?: string;
  voice?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Message {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  agent_name?: string;
  intent?: string;
  created_at?: string;
  isStreaming?: boolean;
}

export interface Conversation {
  id: string;
  title?: string;
  mode: "chat" | "voice";
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface AgentActivity {
  agent_name: string;
  action: string;
  status: "running" | "completed" | "error";
  input_summary?: string;
  output_summary?: string;
  duration_ms?: number;
  timestamp?: string;
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  intent?: string;
  agents_used?: string[];
  agent_activities?: AgentActivity[];
  plan?: PlanStep[];
  latency_ms?: number;
}

export interface PlanStep {
  step: number;
  title: string;
  description: string;
  estimated_time?: string;
  priority?: string;
  dependencies?: number[];
  tools_needed?: string[];
}

export type WSMessageType = "text" | "agent_activity" | "status" | "done" | "error" | "audio" | "connected";

export interface WSMessage {
  type: WSMessageType;
  content?: string;
  code?: string;
  user_id?: string;
  agent_activity?: AgentActivity;
  metadata?: Record<string, unknown>;
  audio_base64?: string;
}

export interface Memory {
  id: string;
  memory_type: "short_term" | "long_term" | "semantic" | "episodic";
  category?: string;
  title?: string;
  content: string;
  importance_score: number;
  created_at: string;
  accessed_at?: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: "pending" | "in_progress" | "completed" | "cancelled";
  priority: "low" | "medium" | "high" | "urgent";
  category?: string;
  steps?: PlanStep[];
  due_date?: string;
  is_ai_generated: boolean;
  created_at: string;
}

export interface TaskSummary {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  cancelled: number;
}

export type VoiceState =
  | "idle"
  | "listening"
  | "processing"
  | "speaking"
  | "error";

export type Theme = "dark" | "light";
