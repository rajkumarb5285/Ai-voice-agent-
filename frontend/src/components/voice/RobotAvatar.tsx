"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import type { VoiceState } from "@/types";

interface RobotAvatarProps {
  state: VoiceState;
  audioLevel?: number;
  onClick?: () => void;
  size?: "sm" | "md" | "lg";
}

const stateConfig: Record<VoiceState, {
  primary: string;
  secondary: string;
  glow: string;
  eyeColor: string;
  label: string;
  hint: string;
}> = {
  idle: {
    primary: "#00f0ff",
    secondary: "#a855f7",
    glow: "rgba(0,240,255,0.45)",
    eyeColor: "#00f0ff",
    label: "ROBOT READY",
    hint: "Click to speak",
  },
  listening: {
    primary: "#3b82f6",
    secondary: "#6366f1",
    glow: "rgba(59,130,246,0.6)",
    eyeColor: "#38bdf8",
    label: "LISTENING...",
    hint: "I'm hearing you",
  },
  processing: {
    primary: "#f59e0b",
    secondary: "#f97316",
    glow: "rgba(245,158,11,0.55)",
    eyeColor: "#fbbf24",
    label: "THINKING...",
    hint: "Processing request",
  },
  speaking: {
    primary: "#10b981",
    secondary: "#06b6d4",
    glow: "rgba(16,185,129,0.6)",
    eyeColor: "#34d399",
    label: "SPEAKING",
    hint: "Listen carefully",
  },
  error: {
    primary: "#ef4444",
    secondary: "#ec4899",
    glow: "rgba(239,68,68,0.5)",
    eyeColor: "#f87171",
    label: "ERROR",
    hint: "Click to retry",
  },
};

const sizeMap = { sm: 0.55, md: 0.78, lg: 1 };

export function RobotAvatar({ state, audioLevel = 0, onClick, size = "lg" }: RobotAvatarProps) {
  const cfg = stateConfig[state];
  const scale = sizeMap[size];
  const [blink, setBlink] = useState(false);
  const blinkRef = useRef<NodeJS.Timeout | null>(null);

  // Random blink
  useEffect(() => {
    const scheduleBlink = () => {
      const delay = 2000 + Math.random() * 4000;
      blinkRef.current = setTimeout(() => {
        setBlink(true);
        setTimeout(() => setBlink(false), 140);
        scheduleBlink();
      }, delay);
    };
    scheduleBlink();
    return () => { if (blinkRef.current) clearTimeout(blinkRef.current); };
  }, []);

  const audioFactor = 1 + (audioLevel / 100) * 0.12;
  const isSpeaking = state === "speaking";
  const isListening = state === "listening";
  const isProcessing = state === "processing";

  // Audio bar heights for mouth when speaking
  const barCount = 7;
  const barHeights = Array.from({ length: barCount }, (_, i) => {
    if (!isSpeaking) return 4;
    const base = 6 + Math.sin((Date.now() / 150) + i * 0.9) * 10;
    const fromAudio = (audioLevel / 100) * 18;
    return Math.max(4, base + fromAudio);
  });

  return (
    <div
      onClick={onClick}
      className="flex flex-col items-center cursor-pointer select-none relative"
      style={{ transform: `scale(${scale})`, transformOrigin: "center bottom" }}
    >
      {/* ── Outer orbital ring ── */}
      <motion.div
        className="absolute rounded-full border-[1.5px] border-dashed"
        style={{
          width: 380,
          height: 380,
          top: "50%",
          left: "50%",
          x: "-50%",
          y: "-54%",
          borderColor: cfg.primary + "44",
        }}
        animate={{ rotate: 360 }}
        transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
      >
        {/* Orbiting dot */}
        <motion.div
          className="absolute w-3 h-3 rounded-full"
          style={{
            background: cfg.primary,
            boxShadow: `0 0 12px ${cfg.primary}`,
            top: -6,
            left: "calc(50% - 6px)",
          }}
        />
      </motion.div>

      {/* ── Secondary orbital ring ── */}
      <motion.div
        className="absolute rounded-full border border-solid"
        style={{
          width: 320,
          height: 320,
          top: "50%",
          left: "50%",
          x: "-50%",
          y: "-54%",
          borderColor: cfg.secondary + "33",
        }}
        animate={{ rotate: -360 }}
        transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
      >
        <motion.div
          className="absolute w-2 h-2 rounded-full"
          style={{
            background: cfg.secondary,
            boxShadow: `0 0 8px ${cfg.secondary}`,
            bottom: -4,
            left: "calc(50% - 4px)",
          }}
        />
      </motion.div>

      {/* ── Ground glow ── */}
      <motion.div
        className="absolute bottom-[60px] left-1/2 -translate-x-1/2 rounded-full blur-2xl"
        style={{
          width: 260,
          height: 40,
          background: `radial-gradient(ellipse, ${cfg.glow}, transparent 70%)`,
        }}
        animate={{ opacity: [0.5, 1, 0.5], scaleX: [0.85, 1.15, 0.85] }}
        transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* ══════════════ ROBOT BODY ══════════════ */}
      <motion.div
        className="relative z-10 flex flex-col items-center"
        animate={
          isListening
            ? { y: [0, -6, 0], scale: [1, audioFactor, 1] }
            : isSpeaking
            ? { scale: [1, audioFactor, 1] }
            : isProcessing
            ? { rotate: [0, 2, -2, 0] }
            : { y: [0, -8, 0] }
        }
        transition={{
          duration: isSpeaking ? 0.25 : isListening ? 0.4 : 2.8,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >

        {/* ─── ANTENNA ─── */}
        <div className="flex flex-col items-center mb-1">
          <motion.div
            className="w-3 h-3 rounded-full"
            style={{
              background: cfg.primary,
              boxShadow: `0 0 16px ${cfg.primary}, 0 0 32px ${cfg.primary}60`,
            }}
            animate={{ scale: [1, 1.5, 1], opacity: [0.8, 1, 0.8] }}
            transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
          />
          <div
            className="w-[3px] h-8 rounded-full"
            style={{ background: `linear-gradient(to bottom, ${cfg.primary}, ${cfg.primary}40)` }}
          />
        </div>

        {/* ─── HEAD ─── */}
        <motion.div
          className="relative rounded-[28px] border-[2.5px] flex flex-col items-center justify-center"
          style={{
            width: 200,
            height: 170,
            background: "linear-gradient(145deg, #0f1628 0%, #1a1f3a 50%, #0d1220 100%)",
            borderColor: cfg.primary,
            boxShadow: `0 0 24px ${cfg.glow}, inset 0 0 30px rgba(0,0,0,0.6)`,
          }}
        >
          {/* Head top grill lines */}
          <div className="absolute top-3 left-1/2 -translate-x-1/2 flex gap-1.5">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="w-[3px] h-3 rounded-full opacity-30"
                style={{ background: cfg.primary }}
              />
            ))}
          </div>

          {/* ── EYES ── */}
          <div className="flex gap-8 mb-4 mt-4">
            {[0, 1].map((eye) => (
              <div key={eye} className="relative">
                {/* Outer ring */}
                <motion.div
                  className="rounded-full border-2 flex items-center justify-center"
                  style={{
                    width: 44,
                    height: 44,
                    borderColor: cfg.eyeColor + "80",
                    boxShadow: `0 0 16px ${cfg.eyeColor}60`,
                  }}
                  animate={
                    isProcessing
                      ? { rotate: [0, 360] }
                      : { borderColor: [cfg.eyeColor + "80", cfg.eyeColor + "ff", cfg.eyeColor + "80"] }
                  }
                  transition={
                    isProcessing
                      ? { duration: 1.5, repeat: Infinity, ease: "linear" }
                      : { duration: 2, repeat: Infinity, ease: "easeInOut", delay: eye * 0.3 }
                  }
                >
                  {/* Pupil / iris */}
                  <motion.div
                    className="rounded-full"
                    style={{
                      width: blink ? 30 : 30,
                      height: blink ? 2 : 30,
                      background: `radial-gradient(circle at 35% 35%, ${cfg.eyeColor}ff, ${cfg.eyeColor}80 60%, ${cfg.eyeColor}30 100%)`,
                      boxShadow: `0 0 12px ${cfg.eyeColor}`,
                    }}
                    animate={isListening ? { scale: [1, 1.15, 1] } : {}}
                    transition={{ duration: 0.5, repeat: Infinity }}
                  />
                </motion.div>
                {/* Eye shine */}
                {!blink && (
                  <div
                    className="absolute top-2 left-2 w-2 h-2 rounded-full opacity-70"
                    style={{ background: "white" }}
                  />
                )}
              </div>
            ))}
          </div>

          {/* ── NOSE / SENSOR dot ── */}
          <motion.div
            className="w-2 h-2 rounded-full mb-3"
            style={{
              background: cfg.secondary,
              boxShadow: `0 0 8px ${cfg.secondary}`,
            }}
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.4, repeat: Infinity }}
          />

          {/* ── MOUTH ── */}
          <div
            className="flex items-end justify-center gap-[3px] rounded-full overflow-hidden"
            style={{
              width: 80,
              height: 24,
              background: "#0a0e1a",
              border: `1.5px solid ${cfg.primary}50`,
              padding: "3px 8px",
            }}
          >
            {isSpeaking ? (
              // Animated audio bars when speaking
              Array.from({ length: barCount }).map((_, i) => (
                <motion.div
                  key={i}
                  className="rounded-full flex-1"
                  style={{ background: cfg.primary, minWidth: 4 }}
                  animate={{
                    height: [
                      4,
                      4 + ((audioLevel / 100) * 16) + Math.random() * 10,
                      4,
                    ],
                  }}
                  transition={{
                    duration: 0.2 + i * 0.04,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: i * 0.03,
                  }}
                />
              ))
            ) : isListening ? (
              // Pulse bars while listening
              Array.from({ length: 5 }).map((_, i) => (
                <motion.div
                  key={i}
                  className="rounded-full flex-1"
                  style={{ background: cfg.primary + "80", minWidth: 4, height: 4 }}
                  animate={{ height: [4, 12, 4], opacity: [0.4, 0.9, 0.4] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.1 }}
                />
              ))
            ) : (
              // Flat line / smile at idle
              <motion.div
                className="w-full rounded-full"
                style={{
                  height: 3,
                  background: `linear-gradient(to right, transparent, ${cfg.primary}80, transparent)`,
                }}
                animate={{ opacity: [0.4, 0.9, 0.4] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            )}
          </div>

          {/* Side ear panels */}
          {[-1, 1].map((side) => (
            <motion.div
              key={side}
              className="absolute top-1/2 -translate-y-1/2 rounded-lg border flex flex-col gap-1 items-center justify-center"
              style={{
                width: 14,
                height: 50,
                [side === -1 ? "left" : "right"]: -16,
                background: "#0f1628",
                borderColor: cfg.primary + "60",
              }}
            >
              {[...Array(3)].map((_, j) => (
                <motion.div
                  key={j}
                  className="w-1 h-1 rounded-full"
                  style={{ background: cfg.primary }}
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1, repeat: Infinity, delay: j * 0.25 }}
                />
              ))}
            </motion.div>
          ))}
        </motion.div>

        {/* ─── NECK ─── */}
        <div
          className="w-8 h-5 mx-auto flex gap-1 items-center justify-center rounded"
          style={{
            background: "linear-gradient(to bottom, #1a1f3a, #0d1220)",
            border: `1px solid ${cfg.primary}30`,
          }}
        >
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="w-[3px] h-3 rounded-full opacity-40"
              style={{ background: cfg.primary }}
            />
          ))}
        </div>

        {/* ─── TORSO / BODY ─── */}
        <motion.div
          className="relative rounded-[24px] border-[2px] flex flex-col items-center justify-start pt-4"
          style={{
            width: 230,
            height: 200,
            background: "linear-gradient(160deg, #111827 0%, #1e2540 40%, #0d1220 100%)",
            borderColor: cfg.primary + "60",
            boxShadow: `0 8px 32px rgba(0,0,0,0.5), inset 0 0 24px rgba(0,0,0,0.4)`,
          }}
        >
          {/* Center chest panel — circular reactor */}
          <motion.div
            className="relative rounded-full border-4 flex items-center justify-center mb-3"
            style={{
              width: 70,
              height: 70,
              borderColor: cfg.primary + "80",
              background: "radial-gradient(circle, #0a0e1a 30%, #111827 100%)",
              boxShadow: `0 0 20px ${cfg.glow}, inset 0 0 16px ${cfg.primary}20`,
            }}
          >
            {/* Reactor core */}
            <motion.div
              className="rounded-full"
              style={{
                width: 36,
                height: 36,
                background: `radial-gradient(circle at 35% 35%, ${cfg.primary}ff, ${cfg.primary}80 60%, ${cfg.primary}20)`,
                boxShadow: `0 0 20px ${cfg.primary}, 0 0 40px ${cfg.primary}60`,
              }}
              animate={{
                scale: isProcessing ? [1, 1.3, 1] : isSpeaking ? [1, 1.15, 1] : [1, 1.08, 1],
                opacity: [0.8, 1, 0.8],
              }}
              transition={{ duration: isProcessing ? 0.6 : 1.8, repeat: Infinity }}
            />
            {/* Rotating ring */}
            <motion.div
              className="absolute rounded-full border border-dashed"
              style={{
                width: 56,
                height: 56,
                borderColor: cfg.secondary + "60",
              }}
              animate={{ rotate: 360 }}
              transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
            />
          </motion.div>

          {/* Status indicator row */}
          <div className="flex gap-2 mb-3">
            {[cfg.primary, cfg.secondary, "#ffffff30"].map((color, i) => (
              <motion.div
                key={i}
                className="w-2 h-2 rounded-full"
                style={{ background: color }}
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.4 }}
              />
            ))}
          </div>

          {/* Bottom grid lines decoration */}
          <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-1 px-6">
            {[...Array(6)].map((_, i) => (
              <motion.div
                key={i}
                className="flex-1 rounded-full"
                style={{
                  height: 3,
                  background: cfg.primary + "40",
                }}
                animate={{ opacity: [0.2, 0.7, 0.2] }}
                transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
              />
            ))}
          </div>

          {/* Side shoulder accents */}
          {[-1, 1].map((side) => (
            <div
              key={side}
              className="absolute top-6 rounded-lg"
              style={{
                width: 18,
                height: 60,
                [side === -1 ? "left" : "right"]: -18,
                background: `linear-gradient(to bottom, ${cfg.primary}30, transparent)`,
                border: `1px solid ${cfg.primary}40`,
                borderRadius: 6,
              }}
            />
          ))}
        </motion.div>

        {/* ─── FLOATING PARTICLES ─── */}
        <div className="absolute inset-0 pointer-events-none overflow-visible">
          {[...Array(10)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute rounded-full"
              style={{
                width: 3 + (i % 3),
                height: 3 + (i % 3),
                background: i % 2 === 0 ? cfg.primary : cfg.secondary,
                left: `${5 + i * 9}%`,
                top: `${15 + (i * 17) % 70}%`,
                boxShadow: `0 0 6px ${i % 2 === 0 ? cfg.primary : cfg.secondary}`,
              }}
              animate={{
                y: [-15, 15, -15],
                x: [-(6 + i * 1.5), (6 + i * 1.5), -(6 + i * 1.5)],
                opacity: [0.15, 0.8, 0.15],
              }}
              transition={{
                duration: 3 + i * 0.5,
                repeat: Infinity,
                ease: "easeInOut",
                delay: i * 0.25,
              }}
            />
          ))}
        </div>
      </motion.div>

      {/* ══ STATUS LABEL ══ */}
      <div className="text-center space-y-1 mt-5 relative z-10">
        <motion.p
          key={state}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-xs font-black uppercase tracking-[0.25em]"
          style={{ color: cfg.primary, textShadow: `0 0 12px ${cfg.glow}` }}
        >
          {cfg.label}
        </motion.p>
        <p className="text-[10px] text-white/30 uppercase tracking-widest font-semibold">
          {cfg.hint}
        </p>
      </div>
    </div>
  );
}
