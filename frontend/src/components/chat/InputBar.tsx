"use client";
import { useState, useRef, KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Send, Square, Loader2, MicOff, Paperclip } from "lucide-react";
import { useAppStore } from "@/store/useAppStore";
import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";
import { voiceApi, uploadApi } from "@/lib/api";
import toast from "react-hot-toast";

interface InputBarProps {
  onSendMessage: (message: string, mode?: string) => void;
  isStreaming?: boolean;
  isConnected?: boolean;
}

export function InputBar({ onSendMessage, isStreaming, isConnected }: InputBarProps) {
  const [input, setInput] = useState("");
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { voiceState, mode } = useAppStore();
  const { isRecording, startRecording, stopRecording, audioLevel, detectedLang, error: recError } = useVoiceRecorder();

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    try {
      const res = await uploadApi.uploadFile(file);
      const fileData = res.data;
      const fileTag = fileData.file_type === "image"
        ? `![${fileData.filename}](${fileData.url})\n`
        : `[Attachment: ${fileData.filename}](${fileData.url})\n`;
      setInput((prev) => prev + (prev ? "\n" : "") + fileTag);
      toast.success(`Attached ${fileData.filename}`);
    } catch {
      toast.error("File upload failed");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };



  const canSend = input.trim().length > 0 && !isStreaming && isConnected;

  const handleSend = () => {
    if (!canSend) return;
    onSendMessage(input.trim(), mode);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
  };

  const handleVoiceToggle = async () => {
    if (isRecording) {
      setIsTranscribing(true);
      const blob = await stopRecording();
      if (blob && blob.size > 0) {
        try {
          const res = await voiceApi.transcribe(blob, detectedLang);

          const text = res.data.text;
          if (text) {
            onSendMessage(text, "voice");
          }
        } catch {
          // fallback: put in input
        }
      }
      setIsTranscribing(false);
    } else {
      await startRecording();
    }
  };

  return (
    <div className="p-4 border-t border-surface-border bg-surface-1/80 backdrop-blur-xl">
      {/* Connection status */}
      {!isConnected && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="flex items-center gap-2 text-amber-400 text-xs mb-2"
        >
          <Loader2 className="w-3 h-3 animate-spin" />
          Connecting to agent...
        </motion.div>
      )}

      {/* Recording indicator */}
      <AnimatePresence>
        {isRecording && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-center gap-3 mb-3 px-2"
          >
            <div className="flex items-center gap-1">
              {Array.from({ length: 20 }).map((_, i) => (
                <motion.div
                  key={i}
                  className="w-0.5 rounded-full bg-rose-400"
                  animate={{ height: `${Math.max(4, (audioLevel / 100) * 24 * Math.random())}px` }}
                  transition={{ duration: 0.1 }}
                />
              ))}
            </div>
            <span className="text-xs text-rose-400 font-medium">Recording...</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main input row */}
      <div className="flex items-end gap-2">
        {/* Hidden File Input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          className="hidden"
          accept="image/*,video/*,audio/*,.pdf,.txt,.py,.js,.ts,.json"
        />
        <motion.button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading || isStreaming}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.92 }}
          className="p-3 rounded-xl bg-surface-3 text-white/70 hover:text-white hover:bg-surface-4 border border-surface-border transition-all disabled:opacity-40"
          title="Upload file or image"
        >
          {isUploading ? (
            <Loader2 className="w-5 h-5 animate-spin text-brand-400" />
          ) : (
            <Paperclip className="w-5 h-5" />
          )}
        </motion.button>

        {/* Text input */}

        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder={isRecording ? "Listening..." : "Message your AI agent... (Enter to send, Shift+Enter for newline)"}
            disabled={isRecording || isTranscribing}
            rows={1}
            className="w-full bg-surface-2 border border-surface-border rounded-2xl px-4 py-3 pr-12 text-sm text-white placeholder-white/30 resize-none focus:outline-none focus:ring-1 focus:ring-brand-500/50 focus:border-brand-500/50 transition-all disabled:opacity-50 max-h-48"
          />

          {/* Character count (when long) */}
          {input.length > 200 && (
            <div className="absolute bottom-2 right-3 text-xs text-white/30">
              {input.length}
            </div>
          )}
        </div>

        {/* Voice button */}
        <motion.button
          onClick={handleVoiceToggle}
          disabled={isTranscribing || isStreaming}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.92 }}
          className={`p-3 rounded-xl transition-all disabled:opacity-40 ${
            isRecording
              ? "bg-rose-500 text-white shadow-lg shadow-rose-900/40 animate-pulse"
              : "bg-surface-3 text-white/70 hover:text-white hover:bg-surface-4 border border-surface-border"
          }`}
          title={isRecording ? "Stop recording" : "Voice input"}
        >
          {isTranscribing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : isRecording ? (
            <Square className="w-5 h-5" />
          ) : recError ? (
            <MicOff className="w-5 h-5 text-red-400" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </motion.button>

        {/* Send button */}
        <motion.button
          onClick={handleSend}
          disabled={!canSend}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.92 }}
          className="p-3 rounded-xl bg-brand-600 text-white hover:bg-brand-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-lg shadow-brand-900/30"
          title="Send message"
        >
          {isStreaming ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </motion.button>
      </div>

      <p className="text-xs text-white/20 text-center mt-2">
        AI may make mistakes. Verify important information.
      </p>
    </div>
  );
}
