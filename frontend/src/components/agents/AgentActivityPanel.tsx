"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useAppStore } from "@/store/useAppStore";
import type { AgentActivity } from "@/types";

const agentColors: Record<string, string> = {
  "Intent Classifier": "from-violet-500 to-purple-600",
  "Memory Agent": "from-blue-500 to-cyan-500",
  "Research Agent": "from-amber-500 to-orange-500",
  "Planner Agent": "from-emerald-500 to-teal-500",
  "Coding Agent": "from-sky-500 to-blue-600",
  "Learning Coach": "from-pink-500 to-rose-500",
  "Productivity Agent": "from-green-500 to-emerald-500",
  "Wellness Coach": "from-fuchsia-500 to-pink-500",
  "Career Coach": "from-indigo-500 to-violet-600",
  "Email Agent": "from-teal-500 to-cyan-600",
  "Response Synthesizer": "from-brand-500 to-purple-600",
};

const statusIcon: Record<string, string> = {
  running: "⟳",
  completed: "✓",
  error: "✕",
};

const statusColor: Record<string, string> = {
  running: "text-amber-400",
  completed: "text-emerald-400",
  error: "text-rose-400",
};

export function AgentActivityPanel() {
  const activities = useAppStore((s) => s.agentActivities);

  if (activities.length === 0) return null;

  return (
    <div className="border-t border-surface-border bg-surface-1/50 backdrop-blur-sm px-4 py-3">
      <h3 className="text-xs font-semibold text-white/40 uppercase tracking-widest mb-2">
        Agent Activity
      </h3>
      <div className="flex flex-wrap gap-2">
        <AnimatePresence>
          {activities.map((activity, i) => (
            <AgentBadge key={i} activity={activity} index={i} />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

function AgentBadge({ activity, index }: { activity: AgentActivity; index: number }) {
  const gradient = agentColors[activity.agent_name] || "from-gray-500 to-gray-600";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8, y: 5 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ delay: index * 0.05 }}
      className="group relative"
    >
      <div
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gradient-to-r ${gradient} text-white text-xs font-medium shadow-sm cursor-default`}
      >
        <span className={`${statusColor[activity.status]} font-bold text-xs`}>
          {statusIcon[activity.status]}
        </span>
        {activity.agent_name}
        {activity.duration_ms && (
          <span className="opacity-60 text-[10px]">{activity.duration_ms}ms</span>
        )}
      </div>

      {/* Tooltip on hover */}
      {activity.output_summary && (
        <div className="absolute bottom-full left-0 mb-2 z-50 hidden group-hover:block">
          <div className="bg-surface-3 border border-surface-border rounded-xl p-3 shadow-xl max-w-xs">
            <p className="text-xs text-white/50 font-medium mb-1">{activity.action}</p>
            <p className="text-xs text-white/80 leading-relaxed">{activity.output_summary}</p>
          </div>
        </div>
      )}
    </motion.div>
  );
}
