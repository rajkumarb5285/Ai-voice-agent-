"use client";
import { motion, AnimatePresence } from "framer-motion";
import type { VoiceState } from "@/types";

interface VoiceOrbProps {
  state: VoiceState;
  audioLevel?: number; // 0-100
  onClick?: () => void;
  size?: "sm" | "md" | "lg";
}

const sizeMap = {
  sm: { orb: "w-20 h-20", ring: "w-28 h-28", inner: "w-14 h-14" },
  md: { orb: "w-36 h-36", ring: "w-48 h-48", inner: "w-24 h-24" },
  lg: { orb: "w-56 h-56", ring: "w-72 h-72", inner: "w-40 h-40" },
};

const stateConfig: Record<VoiceState, {
  gradient: string;
  ringColor: string;
  label: string;
  animate: boolean;
}> = {
  idle: {
    gradient: "from-brand-600 via-purple-600 to-brand-500",
    ringColor: "rgba(99, 102, 241, 0.2)",
    label: "Tap to speak",
    animate: false,
  },
  listening: {
    gradient: "from-violet-500 via-purple-500 to-pink-500",
    ringColor: "rgba(168, 85, 247, 0.4)",
    label: "Listening...",
    animate: true,
  },
  processing: {
    gradient: "from-amber-500 via-orange-500 to-yellow-400",
    ringColor: "rgba(245, 158, 11, 0.3)",
    label: "Thinking...",
    animate: true,
  },
  speaking: {
    gradient: "from-emerald-500 via-teal-500 to-cyan-400",
    ringColor: "rgba(16, 185, 129, 0.4)",
    label: "Speaking...",
    animate: true,
  },
  error: {
    gradient: "from-red-600 via-rose-500 to-pink-500",
    ringColor: "rgba(239, 68, 68, 0.3)",
    label: "Error — tap to retry",
    animate: false,
  },
};

export function VoiceOrb({ state, audioLevel = 0, onClick, size = "md" }: VoiceOrbProps) {
  const cfg = stateConfig[state];
  const sz = sizeMap[size];
  const scale = 1 + (audioLevel / 100) * 0.15;

  return (
    <div className="flex flex-col items-center gap-4">
      <button
        onClick={onClick}
        className="relative flex items-center justify-center focus:outline-none group"
        aria-label={cfg.label}
      >
        {/* Outer ripple rings (listening/speaking only) */}
        <AnimatePresence>
          {cfg.animate && [0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className={`absolute rounded-full`}
              initial={{ scale: 1, opacity: 0.6 }}
              animate={{ scale: 2.5 + i * 0.5, opacity: 0 }}
              exit={{ opacity: 0 }}
              transition={{
                duration: 2,
                repeat: Infinity,
                delay: i * 0.6,
                ease: "easeOut",
              }}
              style={{
                width: "100%",
                height: "100%",
                backgroundColor: cfg.ringColor,
              }}
            />
          ))}
        </AnimatePresence>

        {/* Main orb */}
        <motion.div
          className={`relative ${sz.orb} rounded-full bg-gradient-to-br ${cfg.gradient} shadow-2xl cursor-pointer`}
          animate={{
            scale: state === "listening" ? scale : cfg.animate ? [1, 1.05, 1] : 1,
            boxShadow: cfg.animate
              ? [
                  `0 0 30px ${cfg.ringColor}`,
                  `0 0 60px ${cfg.ringColor}`,
                  `0 0 30px ${cfg.ringColor}`,
                ]
              : `0 0 30px ${cfg.ringColor}`,
          }}
          transition={{
            scale: { duration: 0.1 },
            boxShadow: { duration: 2, repeat: Infinity },
          }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {/* Inner glow */}
          <div className="absolute inset-2 rounded-full bg-white/10 backdrop-blur-sm" />

          {/* Center icon */}
          <div className="absolute inset-0 flex items-center justify-center">
            {state === "idle" && (
              <svg className="w-1/3 h-1/3 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" />
                <line x1="12" y1="19" x2="12" y2="23" stroke="white" strokeWidth="2" strokeLinecap="round" />
                <line x1="8" y1="23" x2="16" y2="23" stroke="white" strokeWidth="2" strokeLinecap="round" />
              </svg>
            )}
            {state === "listening" && <AudioWave />}
            {state === "processing" && <ProcessingSpinner />}
            {state === "speaking" && <SpeakingWave />}
            {state === "error" && (
              <svg className="w-1/3 h-1/3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            )}
          </div>
        </motion.div>
      </button>

      {/* State label */}
      <motion.p
        key={state}
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-sm font-medium text-white/70 tracking-wide"
      >
        {cfg.label}
      </motion.p>
    </div>
  );
}

function AudioWave() {
  return (
    <div className="flex items-center gap-[3px]">
      {[0, 1, 2, 3, 4].map((i) => (
        <motion.div
          key={i}
          className="w-1 bg-white rounded-full"
          animate={{ height: ["4px", "20px", "8px", "16px", "4px"] }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            delay: i * 0.15,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}

function ProcessingSpinner() {
  return (
    <motion.div
      className="w-1/3 h-1/3 border-4 border-white/30 border-t-white rounded-full"
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
    />
  );
}

function SpeakingWave() {
  return (
    <div className="flex items-center gap-[3px]">
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <motion.div
          key={i}
          className="w-1 bg-white rounded-full"
          animate={{ height: ["6px", "18px", "10px", "22px", "6px"] }}
          transition={{
            duration: 0.8,
            repeat: Infinity,
            delay: i * 0.1,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}
