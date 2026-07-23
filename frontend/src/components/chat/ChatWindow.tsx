"use client";
import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageBubble } from "./MessageBubble";
import { useAppStore } from "@/store/useAppStore";
import { Sparkles, MessageCircle } from "lucide-react";

interface ChatWindowProps {
  isStreaming?: boolean;
  onSendMessage?: (message: string) => void;
}

export function ChatWindow({ isStreaming, onSendMessage }: ChatWindowProps) {
  const messages = useAppStore((s) => s.messages);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return <EmptyState onSendMessage={onSendMessage} />;
  }

  return (
    <div className="flex flex-col gap-5 p-6 pb-2">
      <AnimatePresence initial={false}>
        {messages.map((msg, i) => (
          <MessageBubble
            key={msg.id || `msg-${i}`}
            message={msg}
            isLast={i === messages.length - 1}
          />
        ))}
      </AnimatePresence>

      {/* Streaming indicator */}
      {isStreaming && messages[messages.length - 1]?.role !== "assistant" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 pl-12"
        >
          <div className="flex gap-1.5">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-2.5 h-2.5 bg-brand-400 rounded-full"
                animate={{ y: [0, -6, 0] }}
                transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
              />
            ))}
          </div>
          <span className="text-xs text-white/40 tracking-wider">Agent compiling response...</span>
        </motion.div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}

function EmptyState({ onSendMessage }: { onSendMessage?: (message: string) => void }) {
  const suggestions = [
    "Good morning! What should I focus on today?",
    "Help me prepare for my interview next week",
    "I'm feeling overwhelmed. Can we talk?",
    "Explain quantum computing in simple terms",
    "Create a Python script to analyze CSV data",
    "What are the best resources to learn AI?",
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full gap-8 p-8 relative">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(99,102,241,0.02)_0%,transparent_70%)] pointer-events-none" />

      {/* Interactive Floating Logo */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 180, delay: 0.15 }}
        whileHover={{ scale: 1.05, rotate: 10 }}
        className="w-20 h-20 rounded-3xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-xl shadow-indigo-500/10 cursor-pointer relative group"
      >
        <Sparkles className="w-9 h-9 text-white group-hover:scale-110 transition-transform duration-300" />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="text-center space-y-2 relative z-10"
      >
        <h2 className="text-2xl font-bold text-white tracking-tight">
          How can I help you today?
        </h2>
        <p className="text-white/40 text-sm max-w-md mx-auto leading-relaxed">
          I am your personal voice-first AI companion. Start a chat session or choose a suggested request below to begin.
        </p>
      </motion.div>

      {/* Suggestion Chips Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl w-full relative z-10"
      >
        {suggestions.map((s, i) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + i * 0.05 }}
            whileHover={{ scale: 1.015 }}
            whileTap={{ scale: 0.985 }}
            onClick={() => onSendMessage?.(s)}
            className="text-left p-4 rounded-2xl border border-white/[0.04] bg-[#161622]/40 hover:bg-[#1c1c2b]/60 hover:border-brand-500/30 transition-all text-sm text-white/60 hover:text-white/90 flex items-center gap-3 group"
          >
            <MessageCircle className="w-4 h-4 text-white/20 group-hover:text-brand-400 transition-colors flex-shrink-0" />
            <span className="truncate">{s}</span>
          </motion.button>
        ))}
      </motion.div>
    </div>
  );
}
