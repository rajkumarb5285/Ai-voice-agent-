"use client";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Search, Plus, Trash2, Tag, Star, Sparkles } from "lucide-react";
import { memoryApi } from "@/lib/api";
import { useAppStore } from "@/store/useAppStore";
import type { Memory } from "@/types";
import toast from "react-hot-toast";

const memoryTypeColors: Record<string, string> = {
  long_term:  "bg-indigo-500/10 text-indigo-300 border-indigo-500/20",
  semantic:   "bg-purple-500/10 text-purple-300 border-purple-500/20",
  episodic:   "bg-amber-500/10 text-amber-300 border-amber-500/20",
  short_term: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
};

const categoryIcons: Record<string, string> = {
  goal: "🎯", skill: "⚡", preference: "❤️", routine: "🔁",
  career: "💼", wellness: "🌿", task: "✅", fact: "📌", general: "💡",
};

export default function MemoryPage() {
  const { memories, setMemories, removeMemory } = useAppStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<Memory[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadMemories();
  }, []);

  const loadMemories = async () => {
    try {
      const res = await memoryApi.list({ limit: 100 });
      setMemories(res.data);
    } catch {
      toast.error("Failed to load memories");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const res = await memoryApi.search(searchQuery);
      setSearchResults(res.data.results.map((r: { id: string; content: string; metadata?: Record<string, unknown> }) => ({
        id: r.id,
        content: r.content,
        memory_type: "semantic" as const,
        category: (r.metadata as Record<string, unknown>)?.category as string || "general",
        importance_score: 0.8,
        created_at: new Date().toISOString(),
      })));
    } catch {
      toast.error("Search failed");
    } finally {
      setIsSearching(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await memoryApi.delete(id);
      removeMemory(id);
      toast.success("Memory item deleted successfully");
    } catch {
      toast.error("Failed to delete memory item");
    }
  };

  const displayed = searchResults.length > 0
    ? searchResults
    : filter === "all"
      ? memories
      : memories.filter((m) => m.memory_type === filter);

  return (
    <div className="flex flex-col h-full bg-[#07070a] relative">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(99,102,241,0.01)_0%,transparent_60%)] pointer-events-none" />

      {/* Header Panel */}
      <div className="px-6 py-6 border-b border-white/[0.04] bg-[#09090e]/60 backdrop-blur-md sticky top-0 z-10 space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Brain className="w-4.5 h-4.5 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-wide">Memory Workspace</h1>
              <p className="text-[10px] text-white/35 font-semibold uppercase tracking-wider mt-0.5">Semantic database</p>
            </div>
          </div>
          <span className="text-xs text-white/40 font-medium bg-white/[0.02] border border-white/[0.04] px-2.5 py-1 rounded-lg">
            {memories.length} indices active
          </span>
        </div>

        {/* Semantic Search */}
        <div className="flex gap-2.5">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
            <input
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                if (!e.target.value) setSearchResults([]);
              }}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Query memory database semantically..."
              className="w-full bg-[#12121c]/90 border border-white/[0.05] rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 focus:ring-brand-500/30 transition-all"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isSearching}
            className="px-5 py-2.5 bg-gradient-to-r from-brand-600 to-indigo-600 text-white rounded-xl text-sm font-semibold hover:brightness-110 disabled:opacity-50 transition-all shadow-md shadow-brand-900/10"
          >
            {isSearching ? (
              <span className="flex items-center gap-1.5">
                <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Querying...
              </span>
            ) : "Search"}
          </button>
        </div>

        {/* Filter Categories */}
        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          {["all", "long_term", "semantic", "episodic"].map((type) => (
            <button
              key={type}
              onClick={() => { setFilter(type); setSearchResults([]); }}
              className={`text-xs px-3.5 py-1.5 rounded-lg border transition-all font-semibold ${
                filter === type
                  ? "bg-brand-600/15 text-brand-300 border-brand-500/25 shadow-sm"
                  : "bg-transparent border-white/[0.04] text-white/40 hover:text-white/60 hover:border-white/[0.08]"
              }`}
            >
              {type === "all" ? "All memories" : type.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase())}
            </button>
          ))}
        </div>
      </div>

      {/* Memory Cards Grid */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-white/30 text-sm gap-2">
            <svg className="animate-spin h-4 w-4 text-brand-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Loading indices...
          </div>
        ) : displayed.length === 0 ? (
          <EmptyMemories />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <AnimatePresence>
              {displayed.map((memory, i) => (
                <MemoryCard
                  key={memory.id}
                  memory={memory}
                  index={i}
                  onDelete={() => handleDelete(memory.id)}
                />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}

function MemoryCard({ memory, index, onDelete }: { memory: Memory; index: number; onDelete: () => void }) {
  const colorClass = memoryTypeColors[memory.memory_type] || "bg-white/5 text-white/60 border-white/10";
  const icon = categoryIcons[memory.category || "general"] || "💡";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.35, delay: index * 0.03 }}
      className="group bg-[#12121c]/40 border border-white/[0.04] rounded-2xl p-5 hover:border-brand-500/30 hover:bg-[#151522]/50 transition-all duration-300 shadow-sm relative overflow-hidden"
    >
      <div className="flex items-start justify-between gap-3 mb-3.5">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${colorClass}`}>
            {memory.memory_type.replace("_", " ")}
          </span>
          {memory.category && (
            <span className="text-[11px] text-white/35 font-semibold flex items-center gap-1">
              {icon} {memory.category}
            </span>
          )}
        </div>
        <button
          onClick={onDelete}
          className="opacity-0 group-hover:opacity-100 text-white/35 hover:text-rose-400 hover:bg-rose-500/10 p-1.5 rounded-lg transition-all"
          title="Delete memory item"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {memory.title && (
        <h3 className="text-xs font-bold text-white/70 mb-1.5 uppercase tracking-wide">{memory.title}</h3>
      )}
      <p className="text-sm text-white/80 leading-relaxed line-clamp-4">{memory.content}</p>

      <div className="flex items-center justify-between mt-5 pt-3 border-t border-white/[0.03]">
        <div className="flex items-center gap-1.5">
          <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500/20" />
          <span className="text-xs text-white/35 font-semibold">{Math.round(memory.importance_score * 100)}% weight</span>
        </div>
        <span className="text-[10px] text-white/30 font-semibold tracking-wider uppercase">
          {new Date(memory.created_at).toLocaleDateString([], { month: "short", day: "numeric" })}
        </span>
      </div>
    </motion.div>
  );
}

function EmptyMemories() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-5 text-center p-8">
      <div className="w-16 h-16 rounded-2xl bg-white/[0.01] border border-white/[0.03] flex items-center justify-center shadow-inner relative group">
        <div className="absolute inset-0 bg-indigo-500/5 rounded-2xl blur-xl" />
        <Brain className="w-7 h-7 text-white/15 relative z-10" />
      </div>
      <div className="space-y-1 max-w-sm">
        <p className="text-white/60 text-sm font-bold tracking-wide">No Memory Records Detected</p>
        <p className="text-white/30 text-xs leading-relaxed">
          Start a voice or chat stream! Your autonomous companion automatically indexes facts, goals, and routines from your dialogues.
        </p>
      </div>
    </div>
  );
}
