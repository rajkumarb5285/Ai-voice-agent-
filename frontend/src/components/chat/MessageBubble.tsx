"use client";
import { motion } from "framer-motion";
import { memo, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { Message } from "@/types";

interface MessageBubbleProps {
  message: Message;
  isLast?: boolean;
}

export const MessageBubble = memo(function MessageBubble({ message, isLast }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const cursorRef = useRef<HTMLSpanElement>(null);

  // Blinking cursor while streaming
  useEffect(() => {
    if (cursorRef.current) {
      cursorRef.current.style.display = message.isStreaming ? "inline" : "none";
    }
  }, [message.isStreaming]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} group`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold
          ${isUser
            ? "bg-gradient-to-br from-brand-500 to-purple-600 text-white"
            : "bg-gradient-to-br from-surface-3 to-surface-4 text-brand-400 border border-surface-border"
          }`}
      >
        {isUser ? "U" : "✦"}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 shadow-sm
          ${isUser
            ? "bg-brand-600 text-white rounded-tr-sm ml-auto"
            : "bg-surface-2 text-white/90 rounded-tl-sm border border-surface-border"
          }`}
      >
        {/* Agent badge */}
        {!isUser && message.agent_name && (
          <div className="text-xs text-brand-400 font-medium mb-1 opacity-70">
            {message.agent_name.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
          </div>
        )}

        {/* Content */}
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            {/* Custom Video Renderer */}
            {message.content.includes("[video:") && (
              <div className="my-3">
                {message.content.match(/\[video:(.*?)\]/g)?.map((match, idx) => {
                  const videoUrl = match.replace("[video:", "").replace("]", "");
                  return (
                    <div key={idx} className="relative rounded-2xl overflow-hidden border border-brand-500/30 shadow-2xl bg-black/60 my-2">
                      <video
                        src={videoUrl}
                        controls
                        autoPlay
                        loop
                        muted
                        playsInline
                        className="w-full max-h-80 object-contain rounded-xl"
                      />
                    </div>
                  );
                })}
              </div>
            )}
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                img({ node, src, alt, ...props }) {
                  return (
                    <img
                      src={src}
                      alt={alt || "AI Media"}
                      className="rounded-2xl max-h-96 w-full object-cover border border-white/10 shadow-xl my-2"
                      {...props}
                    />
                  );
                },
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || "");
                  return match ? (
                    <SyntaxHighlighter
                      style={oneDark as any}
                      language={match[1]}
                      PreTag="div"
                      className="rounded-xl text-xs my-2"
                    >
                      {String(children).replace(/\n$/, "")}
                    </SyntaxHighlighter>
                  ) : (
                    <code
                      className="bg-surface-4 text-brand-300 px-1 py-0.5 rounded text-xs"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
                p: ({ children }) => (
                  <p className="text-sm leading-relaxed text-white/90 mb-2 last:mb-0">{children}</p>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside space-y-1 text-sm text-white/80 ml-2">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside space-y-1 text-sm text-white/80 ml-2">{children}</ol>
                ),
                h1: ({ children }) => (
                  <h1 className="text-lg font-bold text-white mb-2">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-base font-semibold text-white mb-1">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-sm font-semibold text-brand-300 mb-1">{children}</h3>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-white">{children}</strong>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-brand-500 pl-3 text-white/60 italic">{children}</blockquote>
                ),
              }}
            >
              {message.content.replace(/\[video:.*?\]/g, "")}
            </ReactMarkdown>
            {/* Streaming cursor */}
            <span
              ref={cursorRef}
              className="inline-block w-0.5 h-4 bg-brand-400 ml-0.5 animate-pulse"
            />
          </div>
        )}


        {/* Timestamp */}
        {message.created_at && (
          <div className={`text-xs mt-1 opacity-40 ${isUser ? "text-right" : "text-left"}`}>
            {new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </div>
        )}
      </div>
    </motion.div>
  );
});
