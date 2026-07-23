"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useRef, useState, useCallback } from "react";
import type { VoiceState } from "@/types";
import { useAppStore } from "@/store/useAppStore";

interface JarvisAvatarProps {
  state: VoiceState;
  audioLevel?: number;
  onClick?: () => void;
  size?: "sm" | "md" | "lg";
}

/* ── colour palette per voice state ────────────────────────────────── */
const palette: Record<VoiceState, { core: string; ring: string; glow: string; accent: string }> = {
  idle:       { core: "#00f0ff", ring: "#00d4ff", glow: "rgba(0,240,255,0.35)", accent: "#38bdf8" },
  listening:  { core: "#818cf8", ring: "#6366f1", glow: "rgba(129,140,248,0.45)", accent: "#a5b4fc" },
  processing: { core: "#f59e0b", ring: "#f97316", glow: "rgba(245,158,11,0.4)", accent: "#fbbf24" },
  speaking:   { core: "#10b981", ring: "#06b6d4", glow: "rgba(16,185,129,0.45)", accent: "#34d399" },
  error:      { core: "#ef4444", ring: "#ec4899", glow: "rgba(239,68,68,0.4)", accent: "#f87171" },
};

const emotionAccents: Record<string, string> = {
  calm: "#00f0ff", happy: "#10b981", sad: "#3b82f6", excited: "#a855f7",
  confused: "#f59e0b", nervous: "#ec4899", angry: "#ef4444", frustrated: "#e11d48",
  motivated: "#06b6d4", curious: "#6366f1", fearful: "#f43f5e", confident: "#0ea5e9",
};

const actionLabels: Record<string, { emoji: string; text: string }> = {
  walk: { emoji: "🚶", text: "Walking" }, wave: { emoji: "👋", text: "Greeting" },
  nod: { emoji: "👍", text: "Nodding" }, think: { emoji: "🤔", text: "Thinking" },
  laugh: { emoji: "😂", text: "Laughing" }, celebrate: { emoji: "🎉", text: "Celebrating" },
  clap: { emoji: "👏", text: "Clapping" }, point: { emoji: "👉", text: "Pointing" },
  look_around: { emoji: "👀", text: "Scanning" }, sit: { emoji: "🪑", text: "Sitting" },
  stand: { emoji: "🧍", text: "Standing" },
};

const scaleMap = { sm: 0.5, md: 0.72, lg: 1 };

/* ── Canvas-based particle field ───────────────────────────────────── */
function ParticleField({ color, speed }: { color: string; speed: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const particlesRef = useRef<Array<{ x: number; y: number; vx: number; vy: number; r: number; a: number }>>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = 420, H = 420;
    canvas.width = W;
    canvas.height = H;

    if (particlesRef.current.length === 0) {
      particlesRef.current = Array.from({ length: 60 }, () => ({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * speed * 0.6,
        vy: (Math.random() - 0.5) * speed * 0.6,
        r: 1 + Math.random() * 2,
        a: 0.2 + Math.random() * 0.5,
      }));
    }

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      const cx = W / 2, cy = H / 2;
      const particles = particlesRef.current;

      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > W) p.vx *= -1;
        if (p.y < 0 || p.y > H) p.vy *= -1;

        const dist = Math.sqrt((p.x - cx) ** 2 + (p.y - cy) ** 2);
        if (dist < 120) continue; // don't draw inside core

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = color + Math.round(p.a * 255).toString(16).padStart(2, "0");
        ctx.fill();

        // Draw connection lines to nearby particles
        for (const q of particles) {
          const d = Math.sqrt((p.x - q.x) ** 2 + (p.y - q.y) ** 2);
          if (d < 70 && d > 0) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.strokeStyle = color + Math.round((1 - d / 70) * 40).toString(16).padStart(2, "0");
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [color, speed]);

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none z-0" />;
}

/* ── Waveform ring (audio-reactive) ────────────────────────────────── */
function WaveformRing({ audioLevel, color, radius }: { audioLevel: number; color: string; radius: number }) {
  const points = 64;
  const path = Array.from({ length: points + 1 }, (_, i) => {
    const angle = (i / points) * Math.PI * 2;
    const noise = Math.sin(Date.now() / 200 + i * 0.6) * (audioLevel / 100) * 14;
    const r = radius + noise;
    const x = Math.cos(angle) * r;
    const y = Math.sin(angle) * r;
    return `${i === 0 ? "M" : "L"}${x},${y}`;
  }).join(" ");

  return (
    <svg className="absolute inset-0 w-full h-full z-[3]" viewBox="-210 -210 420 420">
      <motion.path
        d={path + "Z"}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeOpacity={0.6}
        animate={{ rotate: 360 }}
        transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
      />
    </svg>
  );
}

/* ════════════════════════════════════════════════════════════════════ */
export function JarvisAvatar({ state, audioLevel = 0, onClick, size = "lg" }: JarvisAvatarProps) {
  const storeAction = useAppStore((s) => s.avatarAction);
  const storeEmotion = useAppStore((s) => s.avatarEmotion);
  const action = storeAction || "idle";
  const emotion = storeEmotion || "calm";

  const p = palette[state];
  const sc = scaleMap[size];
  const emotionColor = emotionAccents[emotion] || p.core;
  const activeAction = actionLabels[action];

  const [tick, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 80);
    return () => clearInterval(id);
  }, []);

  const audioFactor = 1 + (audioLevel / 100) * 0.18;

  /* Core animation per state */
  let coreAnim: any = { scale: [1, 1.04, 1] };
  let coreTrans: any = { duration: 4, repeat: Infinity, ease: "easeInOut" };

  if (state === "speaking") {
    coreAnim = { scale: [1, audioFactor, 1] };
    coreTrans = { duration: 0.15, repeat: Infinity, ease: "easeOut" };
  } else if (state === "listening") {
    coreAnim = { scale: [1, 1.06, 1], rotate: [0, -2, 2, 0] };
    coreTrans = { duration: 2.4, repeat: Infinity, ease: "easeInOut" };
  } else if (state === "processing") {
    coreAnim = { rotate: [0, 360] };
    coreTrans = { duration: 3, repeat: Infinity, ease: "linear" };
  }

  /* Scan line offset */
  const scanY = ((tick * 3) % 240) - 120;

  return (
    <div
      onClick={onClick}
      className="flex flex-col items-center cursor-pointer select-none relative"
      style={{ transform: `scale(${sc})`, transformOrigin: "center bottom" }}
    >
      {/* ── Action badge ── */}
      <AnimatePresence>
        {activeAction && action !== "idle" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.7, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, y: -14 }}
            className="absolute -top-8 z-30 px-4 py-2 rounded-full text-[10px] font-bold tracking-[0.2em] uppercase flex items-center gap-2 backdrop-blur-xl"
            style={{
              background: "rgba(8,12,24,0.88)",
              border: `1px solid ${emotionColor}40`,
              boxShadow: `0 0 20px ${emotionColor}30`,
              color: emotionColor,
            }}
          >
            <span className="text-sm">{activeAction.emoji}</span>
            {activeAction.text}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Container (420×420) ── */}
      <div className="relative w-[420px] h-[420px] flex items-center justify-center">

        {/* Particle field */}
        <ParticleField color={emotionColor} speed={state === "processing" ? 2.2 : 1} />

        {/* ── Outer orbital ring 1 (dashed, slow) ── */}
        <motion.div
          className="absolute rounded-full border border-dashed"
          style={{ width: 400, height: 400, borderColor: p.ring + "30" }}
          animate={{ rotate: 360 }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
        >
          <div className="absolute w-2.5 h-2.5 rounded-full top-0 left-1/2 -translate-x-1/2 -translate-y-1/2"
            style={{ background: p.core, boxShadow: `0 0 12px ${p.core}` }} />
        </motion.div>

        {/* ── Outer orbital ring 2 (solid, reverse) ── */}
        <motion.div
          className="absolute rounded-full border"
          style={{ width: 360, height: 360, borderColor: emotionColor + "25" }}
          animate={{ rotate: -360 }}
          transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
        >
          <div className="absolute w-2 h-2 rounded-full bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2"
            style={{ background: emotionColor, boxShadow: `0 0 10px ${emotionColor}` }} />
        </motion.div>

        {/* ── Outer orbital ring 3 (thin, fast) ── */}
        <motion.div
          className="absolute rounded-full"
          style={{
            width: 330, height: 330,
            border: `0.5px solid ${p.accent}18`,
          }}
          animate={{ rotate: 360 }}
          transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
        >
          <div className="absolute w-1.5 h-1.5 rounded-full top-1/2 right-0 translate-x-1/2 -translate-y-1/2"
            style={{ background: p.accent, boxShadow: `0 0 8px ${p.accent}` }} />
        </motion.div>

        {/* ── Audio-reactive waveform ring ── */}
        {(state === "listening" || state === "speaking") && (
          <WaveformRing audioLevel={audioLevel} color={emotionColor} radius={155} />
        )}

        {/* ── Glow halo ── */}
        <motion.div
          className="absolute rounded-full"
          style={{
            width: 280, height: 280,
            background: `radial-gradient(circle, ${p.glow} 0%, transparent 70%)`,
          }}
          animate={{ scale: [1, 1.15, 1], opacity: [0.5, 0.85, 0.5] }}
          transition={{ duration: state === "speaking" ? 0.3 : 3.5, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* ── Core hexagonal container ── */}
        <motion.div
          className="absolute z-10 flex items-center justify-center"
          style={{ width: 240, height: 240 }}
          animate={coreAnim}
          transition={coreTrans}
        >
          {/* Outer ring glow */}
          <div
            className="absolute inset-0 rounded-full"
            style={{
              border: `2px solid ${p.core}60`,
              boxShadow: `0 0 30px ${p.glow}, inset 0 0 30px ${p.glow}`,
            }}
          />

          {/* Inner glass circle */}
          <div
            className="absolute rounded-full flex items-center justify-center overflow-hidden"
            style={{
              width: 220, height: 220,
              background: `radial-gradient(circle at 35% 35%, rgba(20,28,50,0.95), rgba(8,12,24,0.98))`,
              border: `1.5px solid ${p.core}50`,
              boxShadow: `inset 0 0 60px ${p.glow}`,
            }}
          >
            {/* ── Scan line ── */}
            <motion.div
              className="absolute w-full z-20 pointer-events-none"
              style={{
                height: 2,
                top: `calc(50% + ${scanY}px)`,
                background: `linear-gradient(90deg, transparent 0%, ${p.core}50 30%, ${p.core}80 50%, ${p.core}50 70%, transparent 100%)`,
              }}
            />

            {/* ── Central "A" / Ava icon ── */}
            <div className="relative z-10 flex flex-col items-center">
              {/* Glowing avatar initial */}
              <motion.div
                className="text-6xl font-black tracking-tighter select-none"
                style={{
                  color: p.core,
                  textShadow: `0 0 30px ${p.core}, 0 0 60px ${p.glow}, 0 0 90px ${p.glow}`,
                  fontFamily: "'Inter', 'SF Pro Display', system-ui, sans-serif",
                }}
                animate={{ opacity: [0.85, 1, 0.85] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              >
                A
              </motion.div>

              {/* Name text */}
              <motion.p
                className="text-[10px] font-bold tracking-[0.5em] uppercase mt-1"
                style={{
                  color: p.core + "cc",
                  textShadow: `0 0 10px ${p.glow}`,
                }}
                animate={{ opacity: [0.6, 1, 0.6] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              >
                AVA
              </motion.p>

              {/* Status dots */}
              <div className="flex items-center gap-1.5 mt-3">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="rounded-full"
                    style={{
                      width: 4, height: 4,
                      background: p.core,
                      boxShadow: `0 0 6px ${p.core}`,
                    }}
                    animate={{
                      scale: state === "processing" ? [1, 1.8, 1] : [1, 1.3, 1],
                      opacity: [0.4, 1, 0.4],
                    }}
                    transition={{
                      duration: state === "processing" ? 0.6 : 1.5,
                      repeat: Infinity,
                      delay: i * 0.2,
                    }}
                  />
                ))}
              </div>
            </div>

            {/* ── Cross-hair grid lines ── */}
            <svg className="absolute inset-0 w-full h-full z-[1] opacity-[0.08]" viewBox="0 0 220 220">
              <line x1="110" y1="0" x2="110" y2="220" stroke={p.core} strokeWidth="0.5" />
              <line x1="0" y1="110" x2="220" y2="110" stroke={p.core} strokeWidth="0.5" />
              <circle cx="110" cy="110" r="70" fill="none" stroke={p.core} strokeWidth="0.5" strokeDasharray="4 4" />
              <circle cx="110" cy="110" r="40" fill="none" stroke={p.core} strokeWidth="0.5" strokeDasharray="2 6" />
            </svg>
          </div>
        </motion.div>

        {/* ── Corner HUD markers ── */}
        {[
          { top: "15%", left: "15%", rotate: 0 },
          { top: "15%", right: "15%", rotate: 90 },
          { bottom: "15%", right: "15%", rotate: 180 },
          { bottom: "15%", left: "15%", rotate: 270 },
        ].map((pos, i) => (
          <div
            key={i}
            className="absolute w-5 h-5"
            style={{ ...pos, transform: `rotate(${pos.rotate}deg)` } as any}
          >
            <div className="absolute top-0 left-0 w-full h-[1px]" style={{ background: p.core + "40" }} />
            <div className="absolute top-0 left-0 w-[1px] h-full" style={{ background: p.core + "40" }} />
          </div>
        ))}

        {/* ── Ground reflection ── */}
        <motion.div
          className="absolute -bottom-4 left-1/2 -translate-x-1/2 rounded-full blur-3xl z-0"
          style={{ width: 300, height: 40, background: `radial-gradient(ellipse, ${p.glow}, transparent 70%)` }}
          animate={{ opacity: [0.3, 0.7, 0.3], scaleX: [0.85, 1.1, 0.85] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      {/* ── Status label ── */}
      <div className="text-center space-y-1.5 mt-2 relative z-10">
        <motion.p
          key={state + emotion}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-[11px] font-bold uppercase tracking-[0.35em]"
          style={{ color: emotionColor, textShadow: `0 0 12px ${emotionColor}80` }}
        >
          {stateLabels[state]}
          {emotion !== "calm" && (
            <span className="ml-2 opacity-70">• {emotion}</span>
          )}
        </motion.p>
        <p className="text-[10px] text-white/25 uppercase tracking-[0.2em] font-medium">
          {state === "idle" ? "Click to Activate" : state === "speaking" ? "Voice Active" : "System Online"}
        </p>
      </div>
    </div>
  );
}

const stateLabels: Record<VoiceState, string> = {
  idle: "Awaiting Command",
  listening: "Listening",
  processing: "Analyzing",
  speaking: "Speaking",
  error: "Offline",
};
