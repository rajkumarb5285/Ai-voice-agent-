"use client";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckSquare, Plus, Trash2, Circle, CheckCircle, Clock, Flag, X, Sparkles } from "lucide-react";
import { tasksApi } from "@/lib/api";
import { useAppStore } from "@/store/useAppStore";
import type { Task } from "@/types";
import toast from "react-hot-toast";

const priorityConfig = {
  urgent: { color: "text-rose-400 border-rose-500/20 bg-rose-500/5", icon: "🔥", badge: "Urgent" },
  high:   { color: "text-amber-400 border-amber-500/20 bg-amber-500/5", icon: "⚡", badge: "High" },
  medium: { color: "text-brand-400 border-brand-500/20 bg-brand-500/5", icon: "◆", badge: "Medium" },
  low:    { color: "text-white/40 border-white/10 bg-white/5", icon: "▪", badge: "Low" },
};

const statusConfig = {
  pending:     { label: "Pending",     color: "text-white/50" },
  in_progress: { label: "In Progress", color: "text-amber-400" },
  completed:   { label: "Done",        color: "text-emerald-400" },
  cancelled:   { label: "Cancelled",   color: "text-white/30" },
};

export default function TasksPage() {
  const { tasks, setTasks, addTask, updateTask, removeTask } = useAppStore();
  const [isLoading, setIsLoading] = useState(true);
  const [summary, setSummary] = useState({ total: 0, pending: 0, in_progress: 0, completed: 0 });
  const [filter, setFilter] = useState("all");
  const [showAdd, setShowAdd] = useState(false);
  const [newTask, setNewTask] = useState({ title: "", description: "", priority: "medium" });

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      const [tasksRes, summaryRes] = await Promise.all([
        tasksApi.list(),
        tasksApi.summary(),
      ]);
      setTasks(tasksRes.data);
      setSummary(summaryRes.data);
    } catch {
      toast.error("Failed to load tasks");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newTask.title.trim()) return;
    try {
      const res = await tasksApi.create(newTask);
      addTask(res.data);
      setNewTask({ title: "", description: "", priority: "medium" });
      setShowAdd(false);
      // Reload stats
      const summaryRes = await tasksApi.summary();
      setSummary(summaryRes.data);
      toast.success("Task created");
    } catch {
      toast.error("Failed to create task");
    }
  };

  const handleToggle = async (task: Task) => {
    const newStatus = task.status === "completed" ? "pending" : "completed";
    try {
      await tasksApi.update(task.id, { status: newStatus });
      updateTask(task.id, { status: newStatus });
      // Reload stats
      const summaryRes = await tasksApi.summary();
      setSummary(summaryRes.data);
    } catch {
      toast.error("Failed to update task");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await tasksApi.delete(id);
      removeTask(id);
      // Reload stats
      const summaryRes = await tasksApi.summary();
      setSummary(summaryRes.data);
      toast.success("Task deleted");
    } catch {
      toast.error("Failed to delete task");
    }
  };

  const filtered = filter === "all" ? tasks : tasks.filter((t) => t.status === filter);

  return (
    <div className="flex flex-col h-full bg-[#07070a] relative">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_20%,rgba(99,102,241,0.01)_0%,transparent_60%)] pointer-events-none" />

      {/* Header Panel */}
      <div className="px-6 py-5 border-b border-white/[0.04] bg-[#09090e]/60 backdrop-blur-md sticky top-0 z-10 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <CheckSquare className="w-4.5 h-4.5 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-wide">Task Command Center</h1>
              <p className="text-[10px] text-white/35 font-semibold uppercase tracking-wider mt-0.5">Execution panel</p>
            </div>
          </div>
          <motion.button
            onClick={() => setShowAdd(true)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-gradient-to-r from-brand-600 to-indigo-600 text-white rounded-xl text-xs font-semibold hover:brightness-110 transition-all shadow-md"
          >
            <Plus className="w-4 h-4" /> Add Task
          </motion.button>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: "Total", value: summary.total, color: "text-white" },
            { label: "Pending", value: summary.pending, color: "text-white/40" },
            { label: "In Progress", value: summary.in_progress, color: "text-amber-400" },
            { label: "Completed", value: summary.completed, color: "text-emerald-400" },
          ].map((stat) => (
            <div key={stat.label} className="bg-[#12121c]/40 border border-white/[0.03] rounded-xl p-3.5 text-center shadow-sm relative overflow-hidden">
              <p className={`text-xl font-extrabold ${stat.color}`}>{stat.value}</p>
              <p className="text-[10px] text-white/30 tracking-wider font-semibold uppercase mt-0.5">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Filter categories */}
        <div className="flex gap-2 overflow-x-auto no-scrollbar pt-1">
          {["all", "pending", "in_progress", "completed"].map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`text-xs px-3.5 py-1.5 rounded-lg border transition-all font-semibold ${
                filter === s
                  ? "bg-brand-600/15 text-brand-300 border-brand-500/25 shadow-sm"
                  : "bg-transparent border-white/[0.04] text-white/40 hover:text-white/60 hover:border-white/[0.08]"
              }`}
            >
              {s === "all" ? "All tasks" : statusConfig[s as keyof typeof statusConfig]?.label}
            </button>
          ))}
        </div>
      </div>

      {/* Add Task Modal */}
      <AnimatePresence>
        {showAdd && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-6"
            onClick={(e) => e.target === e.currentTarget && setShowAdd(false)}
          >
            <motion.div
              initial={{ scale: 0.96, y: 15 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.96, y: 15 }}
              className="bg-[#12121c] border border-white/[0.05] rounded-3xl p-6.5 w-full max-w-md shadow-3xl relative overflow-hidden"
            >
              <div className="absolute top-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-brand-500 to-transparent" />
              <div className="flex items-center justify-between mb-5">
                <h2 className="font-bold text-white tracking-wide text-base uppercase">Deploy Task</h2>
                <button onClick={() => setShowAdd(false)} className="p-1 text-white/40 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                  <X className="w-4.5 h-4.5" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-semibold text-white/50 tracking-wide uppercase">Title</label>
                  <input
                    value={newTask.title}
                    onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                    placeholder="Plan presentation, debug database..."
                    className="w-full bg-[#09090e] border border-white/[0.05] rounded-xl px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 focus:ring-brand-500/30 transition-all"
                    autoFocus
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-semibold text-white/50 tracking-wide uppercase">Description (optional)</label>
                  <textarea
                    value={newTask.description}
                    onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                    placeholder="Enter task context details..."
                    rows={3}
                    className="w-full bg-[#09090e] border border-white/[0.05] rounded-xl px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 focus:ring-brand-500/30 transition-all resize-none"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-semibold text-white/50 tracking-wide uppercase">Priority Weight</label>
                  <select
                    value={newTask.priority}
                    onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                    className="w-full bg-[#09090e] border border-white/[0.05] rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-1 focus:ring-brand-500/30 transition-all"
                  >
                    <option value="low">Low Priority</option>
                    <option value="medium">Medium Priority</option>
                    <option value="high">High Priority</option>
                    <option value="urgent">Urgent Priority</option>
                  </select>
                </div>

                <button
                  onClick={handleCreate}
                  className="w-full mt-2 py-3 bg-gradient-to-r from-brand-600 via-indigo-600 to-purple-600 text-white rounded-xl text-sm font-semibold hover:brightness-110 transition-all shadow-xl shadow-brand-900/10"
                >
                  Create Task
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Task list container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-2.5">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-white/30 text-sm gap-2">
            <svg className="animate-spin h-4 w-4 text-brand-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Loading checklist...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center p-8">
            <div className="w-16 h-16 rounded-2xl bg-white/[0.01] border border-white/[0.03] flex items-center justify-center shadow-inner">
              <CheckSquare className="w-7 h-7 text-white/15" />
            </div>
            <div className="space-y-1.5 max-w-xs mx-auto">
              <p className="text-white/60 text-sm font-bold tracking-wide">No Tasks Located</p>
              <p className="text-white/30 text-xs leading-relaxed">
                Add a task manually, or dictate/chat to your agent and ask it to assemble a checklist.
              </p>
            </div>
          </div>
        ) : (
          <AnimatePresence>
            {filtered.map((task, i) => {
              const pc = priorityConfig[task.priority as keyof typeof priorityConfig] || priorityConfig.medium;
              const sc = statusConfig[task.status as keyof typeof statusConfig] || statusConfig.pending;
              const isCompleted = task.status === "completed";

              return (
                <motion.div
                  key={task.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.35, delay: i * 0.03 }}
                  className={`group flex items-start gap-4 p-4.5 rounded-2xl border transition-all duration-300 shadow-sm
                    ${isCompleted
                      ? "bg-white/[0.01] border-white/[0.03] opacity-50"
                      : `bg-[#12121c]/40 border-white/[0.04] hover:border-brand-500/25 hover:bg-[#151522]/50`
                    }`}
                >
                  {/* Status Toggle Box */}
                  <button onClick={() => handleToggle(task)} className="mt-0.5 flex-shrink-0 focus:outline-none">
                    {isCompleted ? (
                      <CheckCircle className="w-5 h-5 text-emerald-400 hover:scale-105 transition-transform" />
                    ) : (
                      <Circle className="w-5 h-5 text-white/20 hover:text-brand-400 hover:scale-105 transition-transform" />
                    )}
                  </button>

                  {/* Task details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <h3 className={`text-sm font-bold tracking-wide ${isCompleted ? "line-through text-white/30" : "text-white/95"}`}>
                        {task.title}
                      </h3>
                      <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${pc.color}`}>
                        {pc.icon} {pc.badge}
                      </span>
                      {task.is_ai_generated && (
                        <span className="text-[10px] font-bold tracking-widest text-indigo-400 uppercase bg-indigo-500/10 px-1.5 py-0.5 rounded">✦ AI</span>
                      )}
                    </div>
                    {task.description && (
                      <p className={`text-xs mt-1 leading-relaxed ${isCompleted ? "text-white/20" : "text-white/40"}`}>{task.description}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2">
                      <span className={`text-[10px] font-semibold flex items-center gap-1.5 ${sc.color}`}>
                        <Clock className="w-3.5 h-3.5" /> {sc.label}
                      </span>
                    </div>
                  </div>

                  {/* Action Delete */}
                  <button
                    onClick={() => handleDelete(task.id)}
                    className="opacity-0 group-hover:opacity-100 text-white/30 hover:text-rose-400 hover:bg-rose-500/10 p-1.5 rounded-lg transition-all"
                    title="Remove Task"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
