"use client";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity, Zap, Clock, CheckCircle, XCircle, Sparkles,
  Brain, Search, Code, ListChecks, Leaf, Briefcase, Mail,
  Navigation, Server, RefreshCw, TrendingUp,
} from "lucide-react";
import { useAppStore } from "@/store/useAppStore";

const AGENT_CATALOG: Record<string, {
  emoji: string;
  icon: React.ElementType;
  desc: string;
  color: string;
  gradient: string;
  specialty: string;
}> = {
  "Intent Classifier":     { emoji: "🧭", icon: Navigation,  desc: "Classifies user intent and routes request flow to the right specialists", color: "text-violet-300", gradient: "from-violet-500/15 to-purple-600/5 border-violet-500/20", specialty: "NLP · Routing" },
  "Memory Agent":          { emoji: "🧠", icon: Brain,        desc: "Indexes semantic vectors, retrieves contextual memory from past sessions", color: "text-blue-300",   gradient: "from-blue-500/15 to-cyan-500/5 border-blue-500/20",   specialty: "ChromaDB · Redis" },
  "Research Agent":        { emoji: "🔍", icon: Search,       desc: "Fetches live data, synthesizes facts from web search and knowledge graphs", color: "text-amber-300", gradient: "from-amber-500/15 to-orange-500/5 border-amber-500/20", specialty: "Tavily · Web" },
  "Planner Agent":         { emoji: "📋", icon: ListChecks,   desc: "Formulates step-by-step action plans with priority hierarchies and timelines", color: "text-emerald-300", gradient: "from-emerald-500/15 to-teal-500/5 border-emerald-500/20", specialty: "Planning · Tasks" },
  "Coding Agent":          { emoji: "💻", icon: Code,         desc: "Writes, debugs and explains code across Python, JS, SQL and more", color: "text-sky-300",    gradient: "from-sky-500/15 to-blue-600/5 border-sky-500/20",    specialty: "Python · TypeScript" },
  "Learning Coach":        { emoji: "📚", icon: Brain,        desc: "Provides personalized tutoring, quizzes and interactive learning roadmaps", color: "text-pink-300",   gradient: "from-pink-500/15 to-rose-500/5 border-pink-500/20",   specialty: "Education · Quizzes" },
  "Productivity Agent":    { emoji: "✅", icon: ListChecks,   desc: "Manages tasks, deadlines, calendar timers and workflow status summaries", color: "text-green-300",  gradient: "from-green-500/15 to-emerald-500/5 border-green-500/20",  specialty: "GTD · Scheduling" },
  "Wellness Coach":        { emoji: "🌿", icon: Leaf,         desc: "Delivers fitness plans, stress-reduction techniques and mindfulness routines", color: "text-fuchsia-300", gradient: "from-fuchsia-500/15 to-pink-500/5 border-fuchsia-500/20", specialty: "Health · Mindfulness" },
  "Career Coach":          { emoji: "💼", icon: Briefcase,    desc: "Refines resumes, preps for interviews and maps out career growth strategies", color: "text-indigo-300", gradient: "from-indigo-500/15 to-violet-600/5 border-indigo-500/20", specialty: "Resume · Interviews" },
  "Email Agent":           { emoji: "📧", icon: Mail,         desc: "Drafts professional emails, summaries, and communication templates", color: "text-teal-300",   gradient: "from-teal-500/15 to-cyan-600/5 border-teal-500/20",   specialty: "Email · Comms" },
  "Orchestrator":          { emoji: "⚡", icon: Zap,          desc: "General-purpose conversational AI that handles chitchat and multi-turn dialogue", color: "text-yellow-300", gradient: "from-yellow-500/15 to-amber-500/5 border-yellow-500/20", specialty: "GPT-4o · Chat" },
  "Response Synthesizer":  { emoji: "✨", icon: Sparkles,     desc: "Merges all specialist outputs into a single coherent final response", color: "text-brand-300",  gradient: "from-brand-500/15 to-purple-600/5 border-brand-500/20",  specialty: "Synthesis · Merging" },
};

function AgentCard({ name, cfg, isActive, runCount, avgLatency }: {
  name: string;
  cfg: typeof AGENT_CATALOG[string];
  isActive: boolean;
  runCount: number;
  avgLatency: number | null;
}) {
  const Icon = cfg.icon;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`relative group bg-gradient-to-br ${cfg.gradient} border rounded-2xl p-5 transition-all duration-300 overflow-hidden hover:scale-[1.01]`}
    >
      {/* Live pulse indicator */}
      {isActive && (
        <motion.div
          className="absolute top-3 right-3 w-2 h-2 rounded-full bg-emerald-400"
          animate={{ scale: [1, 1.6, 1], opacity: [1, 0.4, 1] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}

      <div className="flex items-start gap-3 mb-3">
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${cfg.gradient} border flex items-center justify-center text-lg flex-shrink-0`}>
          {cfg.emoji}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className={`text-xs font-bold tracking-wide uppercase ${cfg.color}`}>{name}</h3>
          <span className="text-[9px] text-white/30 font-semibold bg-white/[0.04] border border-white/[0.04] px-1.5 py-0.5 rounded mt-0.5 inline-block">
            {cfg.specialty}
          </span>
        </div>
      </div>

      <p className="text-[11px] text-white/45 leading-relaxed font-medium mb-4">{cfg.desc}</p>

      {/* Stats row */}
      <div className="flex items-center gap-3 pt-3 border-t border-white/[0.04]">
        <div className="flex items-center gap-1">
          <TrendingUp className="w-3 h-3 text-white/20" />
          <span className="text-[10px] text-white/30 font-semibold">
            {runCount > 0 ? `${runCount} run${runCount !== 1 ? "s" : ""}` : "Standby"}
          </span>
        </div>
        {avgLatency !== null && (
          <div className="flex items-center gap-1 ml-auto">
            <Clock className="w-3 h-3 text-white/20" />
            <span className="text-[10px] text-white/30 font-semibold font-mono">{avgLatency}ms avg</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function AgentsPage() {
  const agentActivities = useAppStore((s) => s.agentActivities);
  const [activeTab, setActiveTab] = useState<"dashboard" | "live">("dashboard");

  // Compute per-agent stats from activities
  const agentStats: Record<string, { count: number; totalLatency: number }> = {};
  agentActivities.forEach((a) => {
    if (!agentStats[a.agent_name]) agentStats[a.agent_name] = { count: 0, totalLatency: 0 };
    agentStats[a.agent_name].count++;
    if (a.duration_ms) agentStats[a.agent_name].totalLatency += a.duration_ms;
  });

  const activeAgentNames = new Set(agentActivities.map((a) => a.agent_name));

  return (
    <div className="flex flex-col h-full bg-[#07070a] relative overflow-y-auto">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(99,102,241,0.015)_0%,transparent_60%)] pointer-events-none" />

      {/* Header */}
      <div className="px-6 py-5 border-b border-white/[0.04] bg-[#09090e]/60 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Activity className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-wide">Agent Network</h1>
              <p className="text-[10px] text-white/35 font-semibold uppercase tracking-wider mt-0.5">
                {Object.keys(AGENT_CATALOG).length} agents · Autonomous cluster
              </p>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-1 bg-white/[0.03] border border-white/[0.05] rounded-xl p-1">
            {(["dashboard", "live"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${
                  activeTab === tab
                    ? "bg-brand-600/20 text-brand-300 border border-brand-500/25"
                    : "text-white/35 hover:text-white/60"
                }`}
              >
                {tab === "live" ? (
                  <span className="flex items-center gap-1.5">
                    {agentActivities.length > 0 && (
                      <motion.div
                        className="w-1.5 h-1.5 rounded-full bg-emerald-400"
                        animate={{ scale: [1, 1.5, 1] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                      />
                    )}
                    Live Feed
                  </span>
                ) : "Directory"}
              </button>
            ))}
          </div>
        </div>

        {/* Stats bar */}
        {agentActivities.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="flex items-center gap-4 mt-4 pt-4 border-t border-white/[0.03]"
          >
            {[
              { label: "Total Runs", value: agentActivities.length, color: "text-white" },
              { label: "Completed", value: agentActivities.filter(a => a.status === "completed").length, color: "text-emerald-400" },
              { label: "Errors", value: agentActivities.filter(a => a.status === "error").length, color: "text-rose-400" },
              { label: "Avg Latency", value: agentActivities.filter(a => a.duration_ms).length > 0
                ? `${Math.round(agentActivities.filter(a => a.duration_ms).reduce((acc, a) => acc + (a.duration_ms || 0), 0) / agentActivities.filter(a => a.duration_ms).length)}ms`
                : "—", color: "text-amber-400" },
            ].map((stat) => (
              <div key={stat.label} className="flex flex-col items-center px-3 first:pl-0">
                <span className={`text-sm font-extrabold ${stat.color}`}>{stat.value}</span>
                <span className="text-[9px] text-white/25 uppercase tracking-wider font-semibold mt-0.5">{stat.label}</span>
              </div>
            ))}
          </motion.div>
        )}
      </div>

      <div className="p-6">
        {activeTab === "live" ? (
          /* Live Activity Feed */
          <div>
            {agentActivities.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 gap-4">
                <motion.div
                  animate={{ scale: [1, 1.08, 1], opacity: [0.3, 0.6, 0.3] }}
                  transition={{ duration: 3, repeat: Infinity }}
                  className="w-16 h-16 rounded-2xl bg-white/[0.02] border border-white/[0.04] flex items-center justify-center"
                >
                  <Server className="w-7 h-7 text-white/15" />
                </motion.div>
                <div className="text-center">
                  <p className="text-white/50 text-sm font-bold">Agents On Standby</p>
                  <p className="text-white/25 text-xs mt-1">Send a message in Chat or Voice to see agents activate in real time.</p>
                </div>
              </div>
            ) : (
              <div className="space-y-2.5">
                <p className="text-[10px] text-white/35 font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5" />
                  Last session — {agentActivities.length} activations
                </p>
                <AnimatePresence>
                  {[...agentActivities].reverse().map((activity, i) => {
                    const cfg = AGENT_CATALOG[activity.agent_name];
                    return (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -12 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: i * 0.03 }}
                        className="flex items-start gap-3 bg-[#12121c]/50 border border-white/[0.04] rounded-2xl p-4"
                      >
                        <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-sm flex-shrink-0 border bg-gradient-to-br ${cfg?.gradient || "from-white/5 to-white/0 border-white/10"}`}>
                          {cfg?.emoji || "🤖"}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-bold text-white tracking-wide">{activity.agent_name}</span>
                            {activity.status === "completed" && (
                              <span className="flex items-center gap-1 text-[9px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
                                <CheckCircle className="w-2.5 h-2.5" /> Done
                              </span>
                            )}
                            {activity.status === "error" && (
                              <span className="flex items-center gap-1 text-[9px] text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
                                <XCircle className="w-2.5 h-2.5" /> Error
                              </span>
                            )}
                            {activity.duration_ms && (
                              <span className="text-[9px] text-white/25 flex items-center gap-0.5 ml-auto font-mono">
                                <Clock className="w-3 h-3" /> {activity.duration_ms}ms
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-white/40 mt-1.5 leading-relaxed">{activity.action}</p>
                          {activity.output_summary && (
                            <p className="text-[11px] text-white/25 mt-2 bg-white/[0.02] border border-white/[0.03] px-3 py-2 rounded-xl font-mono leading-relaxed">
                              {activity.output_summary}
                            </p>
                          )}
                        </div>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            )}
          </div>
        ) : (
          /* Agent Directory Grid */
          <div>
            <p className="text-[10px] text-white/35 font-bold uppercase tracking-widest mb-4">
              Deployment Directory — {Object.keys(AGENT_CATALOG).length} Specialist Agents
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {Object.entries(AGENT_CATALOG).map(([name, cfg], i) => {
                const stats = agentStats[name];
                return (
                  <motion.div
                    key={name}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35, delay: i * 0.04 }}
                  >
                    <AgentCard
                      name={name}
                      cfg={cfg}
                      isActive={activeAgentNames.has(name)}
                      runCount={stats?.count || 0}
                      avgLatency={stats ? Math.round(stats.totalLatency / stats.count) : null}
                    />
                  </motion.div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
