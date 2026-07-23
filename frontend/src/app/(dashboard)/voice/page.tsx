"use client";
import { useState, useRef, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { motion, AnimatePresence } from "framer-motion";
import { JarvisAvatar } from "@/components/voice/JarvisAvatar";
import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";
import { useWebSocket, LANGUAGE_MAP } from "@/hooks/useWebSocket";
import { useAppStore } from "@/store/useAppStore";
import { voiceApi } from "@/lib/api";
import { Mic, Sparkles, Volume2, Radio, Zap, Globe, ChevronDown, Shield } from "lucide-react";
import { AgentActivityPanel } from "@/components/agents/AgentActivityPanel";
import toast from "react-hot-toast";

// ── Waveform bar visualizer ──────────────────────────────────────────────────
function WaveformBars({ audioLevel, state }: { audioLevel: number; state: string }) {
  const barCount = 40;
  return (
    <div className="flex items-center justify-center gap-[2px] h-8">
      {Array.from({ length: barCount }).map((_, i) => {
        const center = barCount / 2;
        const distFromCenter = Math.abs(i - center) / center;
        const t = Date.now() / 100;
        const baseH =
          state === "listening" || state === "speaking"
            ? Math.max(2, (1 - distFromCenter * 0.6) * ((audioLevel / 100) * 28 + 3) + Math.sin(t + i * 0.7) * 5)
            : state === "processing"
            ? 2 + Math.abs(Math.sin(t * 0.9 + i * 0.5)) * 14
            : 2;
        return (
          <motion.div
            key={i}
            className="rounded-full"
            style={{
              width: 2,
              background:
                state === "speaking"
                  ? "linear-gradient(to top, #10b981, #06b6d4)"
                  : state === "listening"
                  ? "linear-gradient(to top, #818cf8, #a5b4fc)"
                  : state === "processing"
                  ? "linear-gradient(to top, #f59e0b, #f97316)"
                  : "rgba(255,255,255,0.06)",
            }}
            animate={{ height: baseH }}
            transition={{ duration: 0.06, ease: "easeOut" }}
          />
        );
      })}
    </div>
  );
}

// ── Language Pill Selector ────────────────────────────────────────────────────
function LanguageSelector({ selected, onSelect }: { selected: string; onSelect: (lang: string) => void }) {
  const [open, setOpen] = useState(false);
  const cfg = LANGUAGE_MAP[selected] || LANGUAGE_MAP["en-US"];
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[9px] font-bold uppercase tracking-[0.15em] transition-all backdrop-blur-md"
        style={{ background: "rgba(0,240,255,0.06)", border: "1px solid rgba(0,240,255,0.15)", color: "#00f0ff" }}
      >
        <Globe className="w-3 h-3" />
        {cfg.flag} {cfg.name}
        <ChevronDown className={`w-3 h-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            className="absolute top-full mt-2 right-0 z-50 rounded-2xl p-2 min-w-[180px] max-h-72 overflow-y-auto backdrop-blur-xl"
            style={{
              background: "linear-gradient(135deg, rgba(8,12,24,0.96), rgba(13,18,32,0.98))",
              border: "1px solid rgba(0,240,255,0.12)",
              boxShadow: "0 20px 50px rgba(0,0,0,0.7)",
            }}
          >
            {Object.values(LANGUAGE_MAP).map((lang) => (
              <button
                key={lang.lang}
                onClick={() => { onSelect(lang.lang); setOpen(false); }}
                className={`w-full text-left flex items-center gap-2 px-3 py-2 rounded-xl text-[10px] font-medium transition-all ${
                  selected === lang.lang ? "text-[#00f0ff]" : "text-white/40 hover:text-white/70"
                }`}
                style={{ background: selected === lang.lang ? "rgba(0,240,255,0.08)" : "transparent" }}
              >
                <span className="text-base">{lang.flag}</span>
                <span className="uppercase tracking-wider">{lang.name}</span>
                {selected === lang.lang && <span className="ml-auto text-[#00f0ff]">✓</span>}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Latency Badge ─────────────────────────────────────────────────────────────
function LatencyBadge({ latency }: { latency: number | null }) {
  if (latency === null) return null;
  const color = latency < 300 ? "#10b981" : latency < 600 ? "#f59e0b" : "#ef4444";
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[9px] font-bold uppercase tracking-[0.15em]"
      style={{ background: `${color}10`, border: `1px solid ${color}30`, color }}
    >
      <Zap className="w-2.5 h-2.5" />
      {latency}ms
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
export default function VoicePage() {
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedLang, setSelectedLang] = useState("en-US");
  const [latency, setLatency] = useState<number | null>(null);
  const sendTimeRef = useRef<number>(0);
  const conversationId = useRef(uuidv4()).current;

  const { voiceState, setVoiceState, ttsEnabled, messages, token } = useAppStore();
  const {
    isRecording, startRecording, stopRecording,
    audioLevel, error, transcript: liveTranscript, detectedLang,
  } = useVoiceRecorder();
  const {
    sendMessage, isConnected, isStreaming, connect, disconnect,
    currentLang, setCurrentLang, cancelTTS,
  } = useWebSocket();

  const connectRef = useRef(connect);
  const disconnectRef = useRef(disconnect);

  useEffect(() => { connectRef.current = connect; disconnectRef.current = disconnect; }, [connect, disconnect]);
  useEffect(() => {
    if (!token) return;
    connectRef.current(conversationId);
    return () => { disconnectRef.current(); };
  }, [token, conversationId]);

  useEffect(() => {
    if (isRecording && liveTranscript) setTranscript(liveTranscript);
  }, [liveTranscript, isRecording]);

  useEffect(() => {
    if (isRecording && detectedLang && detectedLang !== selectedLang) {
      setSelectedLang(detectedLang);
      setCurrentLang(LANGUAGE_MAP[detectedLang] || LANGUAGE_MAP["en-US"]);
    }
  }, [detectedLang, selectedLang, setCurrentLang, isRecording]);

  useEffect(() => {
    const lastMsg = messages[messages.length - 1];
    if (lastMsg?.role === "assistant" && !lastMsg.isStreaming) {
      setResponse(lastMsg.content);
      setIsProcessing(false);
      if (sendTimeRef.current > 0) {
        setLatency(Date.now() - sendTimeRef.current);
        sendTimeRef.current = 0;
      }
      if (voiceState === "processing") {
        setVoiceState("idle");
      }
    }
  }, [messages, voiceState, setVoiceState]);

  const handleAvatarClick = async () => {
    if (isRecording) {
      setIsProcessing(true);
      const blob = await stopRecording();
      let finalText = liveTranscript.trim();
      if (!finalText) {
        if (!blob || blob.size < 300) {
          toast.error("No audio detected. Please speak clearly.");
          setVoiceState("idle");
          setIsProcessing(false);
          return;
        }
        try {
          const res = await voiceApi.transcribe(blob, selectedLang);
          finalText = res.data.text?.trim() || "";
        } catch {
          toast.error("Transcription failed.");
          setVoiceState("idle");
          setIsProcessing(false);
          return;
        }
      }
      setTranscript(finalText);
      if (finalText) {
        sendTimeRef.current = Date.now();
        setLatency(null);
        sendMessage(finalText, "voice", selectedLang);
      } else {
        toast.error("Couldn't understand. Please try again.");
        setVoiceState("idle");
        setIsProcessing(false);
      }
    } else if (isProcessing || isStreaming || voiceState === "speaking" || voiceState === "processing") {
      if (typeof cancelTTS === "function") cancelTTS();
      setIsProcessing(false);
      setVoiceState("idle");
      toast("Stopped speaking.");


    } else {
      setTranscript("");
      setResponse("");
      setLatency(null);
      await startRecording(selectedLang);
    }
  };


  const handleLangChange = (lang: string) => {
    setSelectedLang(lang);
    setCurrentLang(LANGUAGE_MAP[lang] || LANGUAGE_MAP["en-US"]);
  };

  const currentState = isStreaming ? "processing" : voiceState;

    const SUGGESTIONS: Record<string, string[]> = {
    "en-US": ["What are my top tasks today?", "How can I manage stress better?", "Research latest AI trends", "Create a reminder for my meeting"],
    "hi-IN": ["आज मेरे मुख्य काम क्या हैं?", "तनाव कैसे कम करें?", "नवीनतम AI ट्रेंड खोजें", "मेरी मीटिंग के लिए रिमाइंडर बनाएं"],
    "mr-IN": ["आजचे माझे मुख्य काम काय आहे?", "तणाव कसा कमी करावा?", "माझ्या मीटिंगसाठी रिमाइंडर तयार करा"],
    "kn-IN": ["ಇಂದಿನ ನನ್ನ ಮುಖ್ಯ ಕೆಲಸಗಳೇನು?", "ಒತ್ತಡ ಹೇಗೆ ಕಡಿಮೆ ಮಾಡಬಹುದು?", "ಹೊಸ AI ಟ್ರೆಂಡ್‌ಗಳನ್ನು ಹುಡುಕಿ"],
    "ta-IN": ["இன்று என் முக்கிய பணிகள் என்ன?", "மன அழுத்தத்தை எப்படி குறைப்பது?", "புதிய AI போக்குகளை ஆராயுங்கள்"],
    "te-IN": ["ఈరోజు నా ముఖ్యమైన పనులు ఏమిటి?", "ఒత్తిడిని ఎలా తగ్గించాలి?", "కొత్త AI ట్రెండ్లను పరిశోధించండి"],
    "ml-IN": ["ഇന്ന് എന്റെ പ്രധാന ജോലികൾ ഏതൊക്കെ?", "സ്ട്രെസ്സ് എങ്ങനെ കുറയ്ക്കാം?", "പുതിയ AI ട്രെൻഡുകൾ ഗവേഷണം ചെയ്യൂ"],
    "bn-IN": ["আজ আমার প্রধান কাজগুলো কী?", "মানসিক চাপ কীভাবে কমানো যায়?", "নতুন AI ট্রেন্ড গবেষণা করুন"],
    "gu-IN": ["આજે મારા મુખ્ય કાર્યો શું છે?", "તણાવ કેવી રીતે ઘટાડી શકાય?", "નવા AI ટ્રેન્ડ્સ સંશોધન કરો"],
    "or-IN": ["ଆଜି ମୋର ମੁଖ್ಯ କାม କ'ଣ?", "ଚାପ କିପରି କମ କରିବ?", "ନୂଆ AI ଟ୍ରେଣ୍ଡ ଖୋଜ"],
    "pa-IN": ["ਅੱਜ ਮੇਰੇ ਮੁੱਖ ਕੰਮ ਕੀ ਹਨ?", "ਤਣਾਅ ਕਿਵੇਂ ਘੱਟ ਕਰੀਏ?", "ਨਵੇਂ AI ਰੁਝਾਨ ਲੱਭੋ"],
    "bho-IN": ["आज हमार मुख्य काम का बा?", "तनाव कइसे कम कइल जाव?", "नया AI ट्रेंड के खोज करीं"],
    "bgc-IN": ["आज मेरे मुख्य काम के-के सैं?", "तनाव क्यूकर कम करां?", "नया AI ट्रेंड ढूंढो"],
    "awa-IN": ["आज हमार मुख्य काम का बा?", "तनाव कइसे कम करैं?", "नवा AI ट्रेंड खोजा"],
    "bra-IN": ["आज मेरे मुख्य काम का हैं?", "तनाव कइसे कम करीजै?", "नयौ AI ट्रेंड ढूँढ़ौ"],
    "mwr-IN": ["आज म्हारा मुख्य काम कांई है?", "तनाव क्यूं कर कम करां?", "नवो AI ट्रेंड खोजो"],
  };

  const suggestions = SUGGESTIONS[selectedLang] || SUGGESTIONS["en-US"];

  return (
    <div
      className="flex h-full relative overflow-hidden"
      style={{ background: "radial-gradient(ellipse at 50% 40%, #0a0f1a 0%, #050810 60%, #020306 100%)" }}
    >
      {/* ── Ambient background effects ── */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* Radial glow */}
        <motion.div
          className="absolute rounded-full blur-[150px]"
          style={{ width: 800, height: 800, top: "10%", left: "20%", background: "rgba(0,240,255,0.025)" }}
          animate={{ scale: [1, 1.3, 1], opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute rounded-full blur-[120px]"
          style={{ width: 500, height: 500, bottom: "5%", right: "10%", background: "rgba(168,85,247,0.02)" }}
          animate={{ scale: [1, 1.25, 1], opacity: [0.2, 0.5, 0.2] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 3 }}
        />
        {/* Grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(0,240,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(0,240,255,0.5) 1px, transparent 1px)",
            backgroundSize: "80px 80px",
          }}
        />
        {/* Horizon line */}
        <div className="absolute bottom-[28%] left-0 right-0 h-[1px]" style={{ background: "linear-gradient(90deg, transparent, rgba(0,240,255,0.06), transparent)" }} />
      </div>

      {/* ══ LEFT: JARVIS Avatar ══ */}
      <div className="flex-1 flex flex-col items-center justify-center relative z-10 px-4">
        {/* Top HUD bar */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-lg flex items-center justify-between mb-2"
        >
          <div className="flex items-center gap-2 text-[#00f0ff] font-bold text-[9px] uppercase tracking-[0.2em] bg-[#00f0ff]/5 border border-[#00f0ff]/15 px-3 py-1.5 rounded-full backdrop-blur-md">
            <Shield className="w-3 h-3" />
            AVA System Online
          </div>
          <div className="flex items-center gap-2">
            <LatencyBadge latency={latency} />
            <LanguageSelector selected={selectedLang} onSelect={handleLangChange} />
          </div>
        </motion.div>

        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-center mb-0"
        >
          <h1 className="text-3xl font-black text-white tracking-tight">
            <span style={{ color: "#00f0ff", textShadow: "0 0 40px rgba(0,240,255,0.4)" }}>
              AVA
            </span>
          </h1>
          <p className="text-white/25 text-[10px] mt-0.5 tracking-[0.25em] uppercase font-medium">
            {isConnected
              ? isRecording
                ? `🎙️ Listening in ${LANGUAGE_MAP[selectedLang]?.name || "English"}...`
                : voiceState === "speaking"
                ? "🔊 Voice output active"
                : "Advanced Voice Assistant · Click to speak"
              : "⚡ Initializing..."}
          </p>
        </motion.div>

        {/* JARVIS Avatar */}
        <motion.div
          initial={{ opacity: 0, scale: 0.7 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, type: "spring", bounce: 0.25 }}
        >
          <JarvisAvatar
            state={currentState}
            audioLevel={audioLevel}
            onClick={handleAvatarClick}
            size="lg"
          />
        </motion.div>

        {/* Waveform */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="w-64 mt-1"
        >
          <WaveformBars audioLevel={audioLevel} state={currentState} />
        </motion.div>

        {/* Status badges */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
          className="flex items-center gap-5 mt-2"
        >
          <div className="flex items-center gap-1.5">
            <motion.div
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: isConnected ? "#10b981" : "#ef4444" }}
              animate={{ scale: isConnected ? [1, 1.5, 1] : 1, opacity: isConnected ? [0.6, 1, 0.6] : 0.5 }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <span className="text-[9px] text-white/20 uppercase tracking-[0.15em] font-bold">
              {isConnected ? "Connected" : "Reconnecting"}
            </span>
          </div>
          {ttsEnabled && (
            <div className="flex items-center gap-1.5">
              <Volume2 className="w-3 h-3 text-white/15" />
              <span className="text-[9px] text-white/15 uppercase tracking-[0.15em] font-bold">Voice</span>
            </div>
          )}
        </motion.div>
      </div>

      {/* ══ RIGHT: Conversation Panel ══ */}
      <motion.div
        initial={{ opacity: 0, x: 30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="w-[400px] flex flex-col gap-3 p-6 justify-center relative z-10"
        style={{ borderLeft: "1px solid rgba(0,240,255,0.04)" }}
      >
        {/* Section header */}
        <div className="flex items-center gap-2 mb-1">
          <Zap className="w-3.5 h-3.5 text-[#00f0ff]" />
          <span className="text-[9px] font-bold uppercase tracking-[0.25em] text-white/30">
            Live Conversation
          </span>
          {currentLang && (
            <span className="ml-auto text-[9px] text-white/20 font-medium">
              {currentLang.flag} {currentLang.name}
            </span>
          )}
        </div>

        {/* User transcript */}
        <AnimatePresence>
          {transcript && (
            <motion.div
              initial={{ opacity: 0, y: 14, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10 }}
              className="w-full rounded-2xl p-4 relative overflow-hidden"
              style={{
                background: "linear-gradient(135deg, rgba(129,140,248,0.08), rgba(99,102,241,0.05))",
                border: "1px solid rgba(129,140,248,0.15)",
              }}
            >
              <div className="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-gradient-to-b from-[#818cf8] to-[#6366f1]" />
              <p className="text-[9px] text-[#a5b4fc] font-bold uppercase tracking-[0.2em] mb-1.5 pl-2 flex items-center gap-1.5">
                <Mic className="w-3 h-3" /> You said
              </p>
              <p className="text-white/85 font-medium pl-2 text-sm leading-relaxed">"{transcript}"</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Thinking dots */}
        <AnimatePresence>
          {(isProcessing || isStreaming) && !response && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-3 p-4 rounded-2xl"
              style={{ background: "rgba(245,158,11,0.05)", border: "1px solid rgba(245,158,11,0.12)" }}
            >
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ background: "#f59e0b" }}
                    animate={{ y: [0, -6, 0], opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 0.5, repeat: Infinity, delay: i * 0.12 }}
                  />
                ))}
              </div>
              <span className="text-[10px] text-[#f59e0b] font-bold uppercase tracking-[0.2em]">
                Ava is thinking...
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Response */}
        <AnimatePresence>
          {response && (
            <motion.div
              initial={{ opacity: 0, y: 14, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0 }}
              className="w-full rounded-2xl p-5 max-h-64 overflow-y-auto"
              style={{
                background: "linear-gradient(135deg, rgba(0,240,255,0.05), rgba(6,182,212,0.03))",
                border: "1px solid rgba(0,240,255,0.12)",
              }}
            >
              <p className="text-[9px] text-[#00f0ff] font-bold uppercase tracking-[0.2em] mb-2 flex items-center gap-1.5">
                <Sparkles className="w-3 h-3" /> Ava
                {latency && (
                  <span className="ml-auto text-[#00f0ff]/40 font-mono text-[8px]">{latency}ms</span>
                )}
              </p>
              <p className="text-white/80 text-sm leading-relaxed whitespace-pre-wrap">{response}</p>
              {voiceState === "speaking" && (
                <div
                  className="flex items-center gap-2 mt-3 pt-3"
                  style={{ borderTop: "1px solid rgba(0,240,255,0.08)" }}
                >
                  <Volume2 className="w-3 h-3 text-[#00f0ff]" />
                  <span className="text-[9px] text-[#00f0ff] font-bold uppercase tracking-[0.2em] animate-pulse">
                    Speaking...
                  </span>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-rose-400 text-xs rounded-xl px-4 py-3 text-center font-semibold"
            style={{ background: "rgba(239,68,68,0.05)", border: "1px solid rgba(239,68,68,0.12)" }}
          >
            {error}
          </motion.div>
        )}

        {/* Quick suggestions */}
        {voiceState === "idle" && !transcript && !response && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="space-y-1.5"
          >
            <p className="text-[9px] text-white/15 font-bold uppercase tracking-[0.25em] mb-2">
              Try asking Ava:
            </p>
            {suggestions.map((s, i) => (
              <motion.button
                key={i}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.9 + i * 0.08 }}
                onClick={() => {
                  setTranscript(s);
                  setResponse("");
                  sendTimeRef.current = Date.now();
                  setLatency(null);
                  sendMessage(s, "voice", selectedLang);
                }}
                className="w-full text-left text-[11px] text-white/30 hover:text-white/60 px-3 py-2.5 rounded-xl transition-all duration-200 font-medium"
                style={{
                  background: "rgba(255,255,255,0.015)",
                  border: "1px solid rgba(255,255,255,0.03)",
                }}
                whileHover={{ x: 4, backgroundColor: "rgba(0,240,255,0.03)" }}
              >
                "{s}"
              </motion.button>
            ))}
          </motion.div>
        )}

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.3 }}
          className="mt-auto pt-3 flex items-center gap-1.5 text-[9px] text-white/10 font-medium tracking-wider"
          style={{ borderTop: "1px solid rgba(255,255,255,0.02)" }}
        >
          <Volume2 className="w-3 h-3" />
          <span>Streaming TTS · ~200ms latency · {Object.keys(LANGUAGE_MAP).length} languages</span>
        </motion.div>
      </motion.div>

      {/* Agent activity footer */}
      <div className="absolute bottom-0 left-0 right-0 z-10">
        <AgentActivityPanel />
      </div>
    </div>
  );
}
