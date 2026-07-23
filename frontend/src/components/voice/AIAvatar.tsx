"use client";
import { motion, AnimatePresence } from "framer-motion";
import type { VoiceState } from "@/types";
import { useAppStore } from "@/store/useAppStore";

interface AIAvatarProps {
  state: VoiceState;
  audioLevel?: number;
  onClick?: () => void;
  size?: "sm" | "md" | "lg";
  action?: string;
  emotion?: string;
}

const themeColors: Record<VoiceState, {
  primary: string;
  secondary: string;
  glow: string;
}> = {
  idle: {
    primary: "#00f0ff",
    secondary: "#a855f7",
    glow: "rgba(0, 240, 255, 0.3)",
  },
  listening: {
    primary: "#3b82f6",
    secondary: "#818cf8",
    glow: "rgba(59, 130, 246, 0.4)",
  },
  processing: {
    primary: "#f59e0b",
    secondary: "#f97316",
    glow: "rgba(245, 158, 11, 0.4)",
  },
  speaking: {
    primary: "#10b981",
    secondary: "#06b6d4",
    glow: "rgba(16, 185, 129, 0.45)",
  },
  error: {
    primary: "#ef4444",
    secondary: "#ec4899",
    glow: "rgba(239, 68, 68, 0.4)",
  },
};

const emotionThemes: Record<string, {
  glow: string;
  particle: string;
  speed: number;
  label: string;
  accent: string;
}> = {
  calm: { glow: "rgba(0, 240, 255, 0.3)", particle: "#00f0ff", speed: 4.5, label: "Calm", accent: "#00f0ff" },
  happy: { glow: "rgba(16, 185, 129, 0.45)", particle: "#10b981", speed: 2.8, label: "Happy", accent: "#10b981" },
  sad: { glow: "rgba(59, 130, 246, 0.35)", particle: "#3b82f6", speed: 6.0, label: "Empathetic", accent: "#3b82f6" },
  excited: { glow: "rgba(168, 85, 247, 0.6)", particle: "#a855f7", speed: 1.6, label: "Excited", accent: "#a855f7" },
  confused: { glow: "rgba(245, 158, 11, 0.4)", particle: "#f59e0b", speed: 4.0, label: "Puzzled", accent: "#f59e0b" },
  nervous: { glow: "rgba(236, 72, 153, 0.4)", particle: "#ec4899", speed: 2.0, label: "Attentive", accent: "#ec4899" },
  angry: { glow: "rgba(239, 68, 68, 0.5)", particle: "#ef4444", speed: 1.5, label: "Firm", accent: "#ef4444" },
  frustrated: { glow: "rgba(225, 29, 72, 0.45)", particle: "#e11d48", speed: 2.2, label: "Concerned", accent: "#e11d48" },
  motivated: { glow: "rgba(6, 182, 212, 0.5)", particle: "#06b6d4", speed: 2.4, label: "Inspired", accent: "#06b6d4" },
  curious: { glow: "rgba(99, 102, 241, 0.4)", particle: "#6366f1", speed: 3.2, label: "Curious", accent: "#6366f1" },
  fearful: { glow: "rgba(244, 63, 94, 0.4)", particle: "#f43f5e", speed: 2.2, label: "Concerned", accent: "#f43f5e" },
  confident: { glow: "rgba(14, 165, 233, 0.5)", particle: "#0ea5e9", speed: 3.0, label: "Confident", accent: "#0ea5e9" },
};

const actionEmoji: Record<string, string> = {
  walk: "🚶",
  sit: "🪑",
  wave: "👋",
  nod: "👍",
  shake: "👎",
  clap: "👏",
  point: "👉",
  think: "🤔",
  laugh: "😂",
  celebrate: "🎉",
  sad: "😢",
  confused: "❓",
  surprised: "😮",
  listening: "👂",
  look_around: "👀",
  stand: "🧍",
};

const actionLabel: Record<string, string> = {
  walk: "Walking Mode",
  sit: "Sitting Down",
  wave: "Greeting You",
  nod: "Nodding",
  shake: "Disagreeing",
  clap: "Clapping",
  point: "Pointing",
  think: "Thinking",
  laugh: "Laughing",
  celebrate: "Celebrating",
  sad: "Sighing",
  confused: "Confused",
  surprised: "Surprised",
  listening: "Listening",
  look_around: "Looking Around",
  stand: "Standing",
};

const scaleMap = { sm: 0.55, md: 0.8, lg: 1 };

export function AIAvatar({
  state,
  audioLevel = 0,
  onClick,
  size = "lg",
  action: propAction,
  emotion: propEmotion,
}: AIAvatarProps) {
  const storeAction = useAppStore((s) => s.avatarAction);
  const storeEmotion = useAppStore((s) => s.avatarEmotion);

  const action = propAction || storeAction || "idle";
  const emotion = propEmotion || storeEmotion || "calm";

  const color = themeColors[state];
  const scale = scaleMap[size];
  const audioFactor = 1 + (audioLevel / 100) * 0.15;

  const currentTheme = emotionThemes[emotion] || emotionThemes.calm;

  // Determine motion path and animation based on current action & state
  let avatarAnimation: any = { y: [-5, 5, -5] };
  let animationTransition: any = { duration: 3.5, repeat: Infinity, ease: "easeInOut" };

  if (state === "speaking") {
    avatarAnimation = { scale: [1, audioFactor, 1] };
    animationTransition = { duration: 0.18, repeat: Infinity, ease: "easeInOut" };
  } else if (state === "listening") {
    avatarAnimation = { scale: [1, 1.04, 1], rotate: [0, -1, 1, 0] };
    animationTransition = { duration: 2.0, repeat: Infinity, ease: "easeInOut" };
  } else if (state === "processing") {
    avatarAnimation = { rotate: [0, 4, -4, 0] };
    animationTransition = { duration: 1.5, repeat: Infinity, ease: "easeInOut" };
  } else if (action === "walk") {
    // Left-right + up-down step sway
    avatarAnimation = {
      x: [-8, 8, -8],
      y: [-10, 0, -10],
      rotate: [-2, 2, -2],
    };
    animationTransition = { duration: 1.8, repeat: Infinity, ease: "easeInOut" };
  } else if (action === "laugh" || action === "celebrate") {
    // Energetic vertical bounce + zoom
    avatarAnimation = {
      scale: [1, 1.07, 0.96, 1.04, 1],
      y: [0, -14, 2, -4, 0],
    };
    animationTransition = { duration: 0.9, repeat: 2, ease: "easeOut" };
  } else if (action === "think") {
    // Slow head tilt + float
    avatarAnimation = {
      rotate: [-3, 3, -3],
      y: [-2, 2, -2],
    };
    animationTransition = { duration: 4.2, repeat: Infinity, ease: "easeInOut" };
  } else if (action === "wave") {
    // Playful rotation sway
    avatarAnimation = {
      rotate: [-4, 4, -4, 4, 0],
      y: [-3, 0, -3],
    };
    animationTransition = { duration: 1.2, repeat: 2, ease: "easeInOut" };
  } else if (action === "point") {
    // Press forward zoom
    avatarAnimation = {
      scale: [1, 1.05, 1.05, 1],
      y: [0, -6, -6, 0],
    };
    animationTransition = { duration: 1.4, repeat: 1, ease: "easeInOut" };
  } else if (action === "nod") {
    // Double head nod
    avatarAnimation = {
      y: [0, -10, 0, -6, 0],
    };
    animationTransition = { duration: 0.8, repeat: 2, ease: "easeInOut" };
  } else if (action === "shake") {
    // Side to side head shake
    avatarAnimation = {
      x: [0, -10, 10, -8, 8, 0],
    };
    animationTransition = { duration: 0.8, repeat: 1, ease: "easeInOut" };
  }

  return (
    <div
      className="flex flex-col items-center cursor-pointer select-none relative"
      onClick={onClick}
      style={{ transform: `scale(${scale})`, transformOrigin: "center bottom" }}
    >
      {/* Floating Action/Status Badge */}
      <AnimatePresence>
        {action && action !== "idle" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: -10 }}
            className="absolute -top-7 px-4 py-2 rounded-full text-[10px] font-bold tracking-widest uppercase flex items-center gap-1.5 z-20 shadow-lg backdrop-blur-md"
            style={{
              background: "rgba(13, 18, 32, 0.85)",
              border: `1px solid ${currentTheme.accent}35`,
              color: "#ffffff",
              boxShadow: `0 8px 24px ${currentTheme.glow}`,
            }}
          >
            <span className="text-xs">{actionEmoji[action] || "✨"}</span>
            <span style={{ color: currentTheme.accent }}>{actionLabel[action] || action}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Ground glow effect */}
      <motion.div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 rounded-full blur-2xl z-0"
        style={{
          width: 220,
          height: 35,
          background: `radial-gradient(ellipse, ${currentTheme.glow}, transparent 70%)`,
        }}
        animate={{ opacity: [0.4, 0.8, 0.4], scaleX: [0.9, 1.15, 0.9] }}
        transition={{ duration: currentTheme.speed, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Floating neon particles */}
      <div className="absolute inset-0 pointer-events-none overflow-visible z-0">
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full"
            style={{
              width: 4 + (i % 3) * 2,
              height: 4 + (i % 3) * 2,
              background: currentTheme.particle,
              left: `${15 + i * 10}%`,
              top: `${10 + (i * 13) % 70}%`,
              boxShadow: `0 0 10px ${currentTheme.particle}`,
            }}
            animate={{
              y: [-25, 25, -25],
              x: [-(10 + i * 2), (10 + i * 2), -(10 + i * 2)],
              opacity: [0.15, 0.65, 0.15],
            }}
            transition={{
              duration: currentTheme.speed * (0.8 + i * 0.1),
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 0.25,
            }}
          />
        ))}
      </div>

      {/* Avatar Container */}
      <motion.div
        className="relative z-10 w-[310px] h-[310px] rounded-full overflow-hidden border-4 transition-colors duration-500"
        style={{
          borderColor: currentTheme.accent,
          boxShadow: `0 0 24px ${currentTheme.glow}`,
        }}
        animate={avatarAnimation}
        transition={animationTransition}
      >
        <img
          src="/avatar.jpg"
          alt="AI Avatar"
          className="w-full h-full object-cover"
        />
      </motion.div>

      {/* Status Label */}
      <div className="text-center space-y-1 mt-6 relative z-10">
        <motion.p
          key={state + emotion}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-xs font-bold uppercase tracking-[0.25em] transition-colors duration-500"
          style={{ color: currentTheme.accent, textShadow: `0 0 8px ${currentTheme.glow}` }}
        >
          {stateLabels[state]} {emotion !== "calm" ? `(${currentTheme.label})` : ""}
        </motion.p>
        <p className="text-[10px] text-white/30 uppercase tracking-widest font-semibold">
          {state === "idle"
            ? "Tap to Speak"
            : state === "speaking"
            ? "Speaking back to you"
            : "Processing request"}
        </p>
      </div>
    </div>
  );
}

const stateLabels: Record<VoiceState, string> = {
  idle: "Ava Ready",
  listening: "Listening...",
  processing: "Thinking...",
  speaking: "Speaking",
  error: "Connection Lost",
};
