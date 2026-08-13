"use client";
import { useCallback, useRef, useEffect, useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import type { WSMessage, AgentActivity } from "@/types";
import { voiceApi } from "@/lib/api";

// ── WebSocket URL: connect directly to backend port 8000
const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  (typeof window !== "undefined"
    ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.hostname}:8000`
    : "ws://localhost:8000");

// ── All supported Indian languages + English
interface LangConfig { lang: string; name: string; flag: string; keywords: string[] }

export const LANGUAGE_MAP: Record<string, LangConfig> = {
  "hi-IN": { lang: "hi-IN", name: "Hindi",     flag: "🇮🇳", keywords: ["hindi", "google hi", "india"] },
  "mr-IN": { lang: "mr-IN", name: "Marathi",   flag: "🇮🇳", keywords: ["marathi", "google mr"] },
  "bn-IN": { lang: "bn-IN", name: "Bengali",   flag: "🇮🇳", keywords: ["bengali", "bangla", "bn"] },
  "gu-IN": { lang: "gu-IN", name: "Gujarati",  flag: "🇮🇳", keywords: ["gujarati", "gu"] },
  "or-IN": { lang: "or-IN", name: "Odia",      flag: "🇮🇳", keywords: ["odia", "oriya", "or"] },
  "ta-IN": { lang: "ta-IN", name: "Tamil",     flag: "🇮🇳", keywords: ["tamil", "ta"] },
  "te-IN": { lang: "te-IN", name: "Telugu",    flag: "🇮🇳", keywords: ["telugu", "te"] },
  "kn-IN": { lang: "kn-IN", name: "Kannada",   flag: "🇮🇳", keywords: ["kannada", "kn"] },
  "ml-IN": { lang: "ml-IN", name: "Malayalam", flag: "🇮🇳", keywords: ["malayalam", "ml"] },
  "pa-IN": { lang: "pa-IN", name: "Punjabi",   flag: "🇮🇳", keywords: ["punjabi", "pa"] },
  "bho-IN": { lang: "bho-IN", name: "Bhojpuri", flag: "🇮🇳", keywords: ["bhojpuri", "hindi", "india", "google hi"] },
  "bgc-IN": { lang: "bgc-IN", name: "Haryanvi", flag: "🇮🇳", keywords: ["haryanvi", "hindi", "india", "google hi"] },
  "awa-IN": { lang: "awa-IN", name: "Awadhi",   flag: "🇮🇳", keywords: ["awadhi", "hindi", "india", "google hi"] },
  "bra-IN": { lang: "bra-IN", name: "Braj Bhasha", flag: "🇮🇳", keywords: ["braj", "hindi", "india", "google hi"] },
  "mwr-IN": { lang: "mwr-IN", name: "Marwari",  flag: "🇮🇳", keywords: ["marwari", "hindi", "india", "google hi"] },
  "en-US": { lang: "en-US", name: "English",   flag: "🇺🇸", keywords: ["google", "natural", "english", "en"] },
};

// Detect language from Unicode script ranges
function detectLang(text: string): LangConfig {
  if (/[\u0900-\u097F]/.test(text)) {
    if (/अहै|अही|अहैन|तोहार|करब|अउर|तौन|जौन|कहेउ|भवा|नीक|परसानी|कतहुँ|कइसन|नाहीं|समुझत|पाँव/.test(text)) return LANGUAGE_MAP["awa-IN"];
    if (/बा|बानी|रउरा|राउर|काहे|हमरा|हमार|इहाँ|उहाँ|बटे|भइल|खातिर/.test(text)) return LANGUAGE_MAP["bho-IN"];
    if (/मन्ने|तन्ने|क्यूकर|सैं|थारे|सै/.test(text)) return LANGUAGE_MAP["bgc-IN"];
    if (/मेरो|करीजै|नयौ|कह्यौ|दियौ|तिहारे/.test(text)) return LANGUAGE_MAP["bra-IN"];
    if (/कांई|कठै|अठै|म्हारो|थारो|थाने|म्हाने|घणी/.test(text)) return LANGUAGE_MAP["mwr-IN"];
    if (/नमस्कार|आहे|करू|झाले|माझा|कसे|आहात/.test(text)) return LANGUAGE_MAP["mr-IN"];
    return LANGUAGE_MAP["hi-IN"];

  }
  if (/[\u0980-\u09FF]/.test(text)) return LANGUAGE_MAP["bn-IN"];
  if (/[\u0A00-\u0A7F]/.test(text)) return LANGUAGE_MAP["pa-IN"];
  if (/[\u0A80-\u0AFF]/.test(text)) return LANGUAGE_MAP["gu-IN"];
  if (/[\u0B00-\u0B7F]/.test(text)) return LANGUAGE_MAP["or-IN"];
  if (/[\u0B80-\u0BFF]/.test(text)) return LANGUAGE_MAP["ta-IN"];
  if (/[\u0C00-\u0C7F]/.test(text)) return LANGUAGE_MAP["te-IN"];
  if (/[\u0C80-\u0CFF]/.test(text)) return LANGUAGE_MAP["kn-IN"];
  if (/[\u0D00-\u0D7F]/.test(text)) return LANGUAGE_MAP["ml-IN"];
  return LANGUAGE_MAP["en-US"];
}

// Clean markdown/formatting for TTS
function cleanForTTS(text: string): string {
  return text
    .replace(/#{1,6}\s+/g, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/`{1,3}[\s\S]*?`{1,3}/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/^\s*[-•*]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/\n{2,}/g, ". ")
    .replace(/\n/g, " ")
    .trim();
}

// Split text into sentences for streaming TTS
function splitSentences(text: string): string[] {
  const raw = text.match(/[^.!?।॥\n]+[.!?।॥]*/g) || [text];
  return raw.map((s) => s.trim()).filter((s) => s.length > 3);
}

interface UseWebSocketReturn {
  sendMessage: (message: string, mode?: string, language?: string) => void;
  isConnected: boolean;
  isStreaming: boolean;
  connect: (conversationId: string) => void;
  disconnect: () => void;
  currentLang: LangConfig;
  setCurrentLang: (lang: LangConfig) => void;
  cancelTTS: () => void;
}


export function useWebSocket(): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentLang, setCurrentLang] = useState<LangConfig>(LANGUAGE_MAP["en-US"]);
  const conversationIdRef = useRef<string | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const onMessageRef = useRef<((event: MessageEvent) => void) | null>(null);

  // Streaming TTS state
  const ttsQueueRef = useRef<string[]>([]);
  const ttsSpeakingRef = useRef(false);
  const streamBufferRef = useRef("");
  const voicesReadyRef = useRef<SpeechSynthesisVoice[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  const {
    addMessage,
    updateLastMessage,
    addAgentActivity,
    clearAgentActivities,
    setVoiceState,
    ttsEnabled,
    selectedVoice,
    setAvatarAction,
    setAvatarEmotion,
  } = useAppStore();

  // ── Pre-load voices immediately on mount (eliminates async delay)
  useEffect(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    const load = () => {
      voicesReadyRef.current = window.speechSynthesis.getVoices();
    };
    load();
    window.speechSynthesis.addEventListener("voiceschanged", load);
    return () => window.speechSynthesis.removeEventListener("voiceschanged", load);
  }, []);

  // ── Pick the best voice for a given language (instant, no async needed)
  const pickVoice = useCallback((langCode: string): SpeechSynthesisVoice | null => {
    const voices = voicesReadyRef.current.length
      ? voicesReadyRef.current
      : (typeof window !== "undefined" ? window.speechSynthesis.getVoices() : []);

    const lc = langCode.toLowerCase();
    const prefix = lc.split("-")[0];
    const config = LANGUAGE_MAP[langCode];

    // Priority keywords to find a soft, natural lady/female voice for Ava
    const femaleKeywords = ["zira", "hazel", "samantha", "susan", "natural", "female", "google us english", "microsoft zira", "microsoft hazel", "victoria", "karen", "moira", "tessa", "ava"];

    // 1. Exact language match + female voice
    const exactLangFemale = voices.find((v) => 
      v.lang.toLowerCase() === lc && 
      femaleKeywords.some((kw) => v.name.toLowerCase().includes(kw))
    );
    if (exactLangFemale) return exactLangFemale;

    // 2. Exact language match
    const exactLang = voices.find((v) => v.lang.toLowerCase() === lc);
    if (exactLang) return exactLang;

    // 3. Prefix language match + female voice
    const prefixLangFemale = voices.find((v) => 
      v.lang.toLowerCase().startsWith(prefix) && 
      femaleKeywords.some((kw) => v.name.toLowerCase().includes(kw))
    );
    if (prefixLangFemale) return prefixLangFemale;

    // 4. Prefix language match
    const prefixLang = voices.find((v) => v.lang.toLowerCase().startsWith(prefix));
    if (prefixLang) return prefixLang;

    // 5. Config keywords
    if (config) {
      const configMatch = voices.find((v) => config.keywords.some((kw) => v.name.toLowerCase().includes(kw)));
      if (configMatch) return configMatch;
    }

    // 6. English female voice fallback
    const enFemale = voices.find((v) => 
      v.lang.toLowerCase().startsWith("en") && 
      femaleKeywords.some((kw) => v.name.toLowerCase().includes(kw))
    );
    if (enFemale) return enFemale;

    // 7. English fallback
    const enFallback = voices.find((v) => v.lang.toLowerCase().startsWith("en"));
    if (enFallback) return enFallback;

    return voices[0] || null;
  }, []);

  // ── Ultra-low latency: speak ONE utterance immediately
  const speakOne = useCallback((text: string, langCode: string, onDone: () => void) => {
    if (typeof window === "undefined" || !window.speechSynthesis) { onDone(); return; }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langCode;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    const voice = pickVoice(langCode);
    if (voice) utterance.voice = voice;

    utterance.onstart = () => setVoiceState("speaking");
    utterance.onend = () => onDone();
    utterance.onerror = () => onDone();

    window.speechSynthesis.speak(utterance);
  }, [pickVoice, setVoiceState]);

  // Check if browser has a native voice for a given language
  const hasNativeVoice = useCallback((langCode: string): boolean => {
    if (typeof window === "undefined" || !window.speechSynthesis) return false;
    const voices = voicesReadyRef.current.length
      ? voicesReadyRef.current
      : window.speechSynthesis.getVoices();
    const lc = langCode.toLowerCase();
    const prefix = lc.split("-")[0];
    return voices.some((v) => v.lang.toLowerCase() === lc || v.lang.toLowerCase().startsWith(prefix));
  }, []);

  // Fallback cloud-based TTS (synthesize via backend API and play via HTML5 Audio)
  const speakOneCloud = useCallback(async (text: string, langCode: string, onDone: () => void) => {
    try {
      setVoiceState("speaking");
      const storeVoice = useAppStore.getState().selectedVoice || "nova";
      const res = await voiceApi.synthesize(text, storeVoice);
      const audioB64 = res.data.audio_base64;
      if (!audioB64) {
        onDone();
        return;
      }
      const audioUrl = "data:audio/mpeg;base64," + audioB64;
      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;

      audio.onended = () => {
        currentAudioRef.current = null;
        onDone();
      };

      audio.onerror = () => {
        currentAudioRef.current = null;
        onDone();
      };

      await audio.play();
    } catch (e) {
      console.error("Cloud TTS failed, proceeding", e);
      onDone();
    }
  }, [setVoiceState]);

  // ── Drain the TTS queue sentence-by-sentence (instant start)
  const drainQueue = useCallback(() => {
    if (ttsSpeakingRef.current) return;
    const next = ttsQueueRef.current.shift();
    if (!next) {
      setVoiceState("idle");
      return;
    }
    ttsSpeakingRef.current = true;
    setVoiceState("speaking");

    // Use High-Definition Cloud TTS Voice Synthesis for rich, natural human audio playback
    speakOneCloud(next, currentLang.lang, () => {
      ttsSpeakingRef.current = false;
      drainQueue();
    });
  }, [speakOneCloud, setVoiceState, currentLang]);

  // ── Enqueue sentences and start speaking immediately (≈ 0.2s latency)
  const enqueueTTS = useCallback((text: string) => {
    if (!ttsEnabled || !text.trim()) return;
    const sentences = splitSentences(cleanForTTS(text));
    if (!sentences.length) return;
    ttsQueueRef.current.push(...sentences);
    drainQueue();
  }, [ttsEnabled, drainQueue]);

  // ── Cancel all TTS (called when user starts recording)
  const cancelTTS = useCallback(() => {
    ttsQueueRef.current = [];
    ttsSpeakingRef.current = false;
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    if (currentAudioRef.current) {
      try {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      } catch {}
    }
  }, []);

  // ── Streaming TTS: as text chunks arrive, extract complete sentences immediately
  const handleStreamChunk = useCallback((chunk: string) => {
    if (!ttsEnabled) return;
    streamBufferRef.current += chunk;

    // Extract any complete sentences from the buffer
    const sentenceEnd = /[.!?।॥]/;
    const parts = streamBufferRef.current.split(/(?<=[.!?।॥])\s+/);
    if (parts.length > 1) {
      const ready = parts.slice(0, -1).join(" ");
      streamBufferRef.current = parts[parts.length - 1];
      const sentences = splitSentences(cleanForTTS(ready));
      if (sentences.length) {
        ttsQueueRef.current.push(...sentences);
        drainQueue();
      }
    }
  }, [ttsEnabled, drainQueue]);

  // ── Flush remaining buffer when stream ends
  const flushStreamBuffer = useCallback(() => {
    const leftover = cleanForTTS(streamBufferRef.current.trim());
    streamBufferRef.current = "";
    if (leftover.length > 2) {
      ttsQueueRef.current.push(leftover);
      drainQueue();
    }
  }, [drainQueue]);

  // ── WebSocket message handler (receives text chunks, agent activities, done, and status updates)
  const handleMessage = useCallback(async (event: MessageEvent) => {
    try {
      const data: WSMessage = JSON.parse(event.data);

      switch (data.type) {
        case "connected":
          // Server confirmed auth — connection is live
          setIsConnected(true);
          break;

        case "status":
          setIsStreaming(true);
          clearAgentActivities();
          streamBufferRef.current = "";
          ttsQueueRef.current = [];
          ttsSpeakingRef.current = false;
          break;

        case "agent_activity":
          if (data.agent_activity) {
            addAgentActivity(data.agent_activity as AgentActivity);
          }
          break;

        case "text":
          if (data.content) {
            setIsStreaming(true);
            const store = useAppStore.getState();
            const lastMsg = store.messages[store.messages.length - 1];

            if (!lastMsg || lastMsg.role !== "assistant" || !lastMsg.isStreaming) {
              addMessage({ role: "assistant", content: data.content, isStreaming: true });
            } else {
              updateLastMessage(data.content, false);
            }

            // ── STREAMING TTS: speak sentences as they arrive ──
            handleStreamChunk(data.content);
          }
          break;

        case "done":
          setIsStreaming(false);
          updateLastMessage("", true);
          // Flush any leftover buffer and speak it immediately
          flushStreamBuffer();

          // Extract actions and emotions from metadata
          if (data.metadata) {
            const metadata = data.metadata as Record<string, any>;
            const actions = (metadata.actions || []) as string[];
            const emotions = (metadata.emotions || []) as string[];
            
            if (actions.length > 0) {
              setAvatarAction(actions[0]);
              // Reset action back to idle after 6 seconds
              setTimeout(() => setAvatarAction("idle"), 6000);
            }
            if (emotions.length > 0) {
              setAvatarEmotion(emotions[0]);
              // Reset emotion back to calm after 10 seconds
              setTimeout(() => setAvatarEmotion("calm"), 10000);
            }
          }

          // If TTS queue is empty (no streaming TTS happened), play full response
          if (!ttsSpeakingRef.current && ttsQueueRef.current.length === 0) {
            const finalStore = useAppStore.getState();
            const finalMsg = finalStore.messages[finalStore.messages.length - 1];
            if (finalMsg?.role === "assistant") {
              enqueueTTS(finalMsg.content);
            } else {
              setVoiceState("idle");
            }
          }
          break;

        case "error":
          setIsStreaming(false);
          cancelTTS();
          // Auth error: stale token — force logout and redirect to login
          if (data.code === "auth_error") {
            conversationIdRef.current = null; // stop reconnect
            useAppStore.getState().logout();
            if (typeof window !== "undefined") {
              window.location.href = "/";
            }
            return;
          }
          setVoiceState("error");
          addMessage({
            role: "assistant",
            content: `Error: ${data.content || "Something went wrong"}`,
            isStreaming: false,
          });
          break;
      }
    } catch {
      // Invalid JSON — ignore
    }
  }, [
    addMessage, updateLastMessage, addAgentActivity, clearAgentActivities,
    setVoiceState, handleStreamChunk, flushStreamBuffer, enqueueTTS, cancelTTS,
    setAvatarAction, setAvatarEmotion, setIsConnected, setIsStreaming,
  ]);

  // Keep ref synchronized with the latest handler
  useEffect(() => {
    onMessageRef.current = handleMessage;
  }, [handleMessage]);

  const connect = useCallback((conversationId: string) => {
    conversationIdRef.current = conversationId;
    const storeToken = useAppStore.getState().token;
    const token =
      storeToken ||
      (typeof window !== "undefined" ? localStorage.getItem("access_token") : "");
    if (!token) return;

    const url = `${WS_URL}/api/chat/ws/${conversationId}?token=${token}`;

    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
    }

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);

    ws.onclose = (event) => {
      if (wsRef.current !== ws) return;
      setIsConnected(false);
      setIsStreaming(false);
      // Auto-reconnect after 2 seconds
      if (conversationIdRef.current) {
        reconnectTimerRef.current = setTimeout(() => {
          if (conversationIdRef.current) connect(conversationIdRef.current);
        }, 2000);
      }
    };

    ws.onerror = () => setIsConnected(false);

    ws.onmessage = (event) => {
      if (onMessageRef.current) {
        onMessageRef.current(event);
      }
    };
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    cancelTTS();
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
    }
    wsRef.current = null;
    conversationIdRef.current = null;
    setIsConnected(false);
  }, [cancelTTS]);

  const sendMessage = useCallback((message: string, mode = "chat", language?: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    // Determine the language: use the explicitly passed language if available, or fall back to auto-detect
    let finalLang = currentLang;
    if (language) {
      finalLang = LANGUAGE_MAP[language] || LANGUAGE_MAP["en-US"];
    } else {
      const detected = detectLang(message);
      // Auto-detect only if the current language is English, or if we detected a non-English language
      if (currentLang.lang === "en-US" || detected.lang !== "en-US") {
        finalLang = detected;
      }
    }
    setCurrentLang(finalLang);

    // Cancel any ongoing TTS immediately
    cancelTTS();

    addMessage({ role: "user", content: message });
    clearAgentActivities();
    wsRef.current.send(JSON.stringify({ message, mode, language: finalLang.lang }));
    setVoiceState("processing");
    setAvatarAction("think");
  }, [addMessage, clearAgentActivities, setVoiceState, cancelTTS, setAvatarAction, currentLang]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, []);

  return { sendMessage, isConnected, isStreaming, connect, disconnect, currentLang, setCurrentLang, cancelTTS };
}

