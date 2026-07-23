"use client";
import { useState, useRef, useCallback, useEffect } from "react";
import { useAppStore } from "@/store/useAppStore";
import { LANGUAGE_MAP } from "@/hooks/useWebSocket";

function detectScriptLang(text: string): string {
  if (/[\u0900-\u097F]/.test(text)) {
    if (/अहै|अही|अहैन|तोहार|करब|अउर|तौन|जौन|कहेउ|भवा|नीक|परसानी|कतहुँ|कइसन|नाहीं|समुझत|पाँव/.test(text)) return "awa-IN";
    if (/बा|बानी|रउरा|राउर|काहे|हमरा|हमार|इहाँ|उहाँ|बटे|भइल|खातिर/.test(text)) return "bho-IN";
    if (/मन्ने|तन्ने|क्यूकर|सैं|थारे|सै/.test(text)) return "bgc-IN";
    if (/मेरो|करीजै|नयौ|कह्यौ|दियौ|तिहारे/.test(text)) return "bra-IN";
    if (/कांई|कठै|अठै|म्हारो|थारो|थाने|म्हाने|घणी/.test(text)) return "mwr-IN";
    if (/नमस्कार|आहे|करू|झाले|माझा|कसे|आहात/.test(text)) return "mr-IN";
    return "hi-IN";

  }
  if (/[\u0D00-\u0D7F]/.test(text)) return "ml-IN";
  if (/[\u0C80-\u0CFF]/.test(text)) return "kn-IN";
  if (/[\u0C00-\u0C7F]/.test(text)) return "te-IN";
  if (/[\u0B80-\u0BFF]/.test(text)) return "ta-IN";
  if (/[\u0B00-\u0B7F]/.test(text)) return "or-IN";
  if (/[\u0A80-\u0AFF]/.test(text)) return "gu-IN";
  if (/[\u0A00-\u0A7F]/.test(text)) return "pa-IN";
  if (/[\u0980-\u09FF]/.test(text)) return "bn-IN";
  return "en-US";
}

interface UseVoiceRecorderReturn {
  isRecording: boolean;
  startRecording: (langCode?: string) => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  error: string | null;
  audioLevel: number;
  transcript: string;
  detectedLang: string;
}

export function useVoiceRecorder(): UseVoiceRecorderReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [transcript, setTranscript] = useState("");
  const [detectedLang, setDetectedLang] = useState("en-US");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const recognitionRef = useRef<any>(null);
  const accTranscriptRef = useRef(""); // accumulated final transcript

  const { setVoiceState } = useAppStore();

  // Monitor audio level for visualizer
  const monitorAudioLevel = useCallback((analyser: AnalyserNode) => {
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      analyser.getByteFrequencyData(dataArray);
      const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      setAudioLevel(Math.min(100, avg * 2.2));
      animFrameRef.current = requestAnimationFrame(tick);
    };
    animFrameRef.current = requestAnimationFrame(tick);
  }, []);

  // Start a SpeechRecognition instance (supports mid-session language switching)
  const startRecognition = useCallback((langCode: string) => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    // Stop previous instance
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch {}
      recognitionRef.current = null;
    }

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;

    const recLangMap: Record<string, string> = {
      "awa-IN": "hi-IN",
      "bho-IN": "hi-IN",
      "bgc-IN": "hi-IN",
      "bra-IN": "hi-IN",
      "mwr-IN": "hi-IN",
    };
    rec.lang = recLangMap[langCode] || langCode || "hi-IN";
    rec.maxAlternatives = 1;



    rec.onresult = (event: any) => {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += t;
          // Auto-detect language from script
          const detected = detectScriptLang(t);
          if (detected !== "en-US" && detected !== langCode) {
            setDetectedLang(detected);
          }
        } else {
          interim += t;
        }
      }

      if (final) accTranscriptRef.current += final;
      const full = accTranscriptRef.current + interim;
      if (full.trim()) setTranscript(full);
    };

    rec.onerror = (e: any) => {
      if (e.error === "no-speech") return; // Ignore silence
      if (e.error === "aborted") return;
      console.warn("SpeechRecognition error:", e.error);
      // Restart on network error
      if (e.error === "network" && isRecording) {
        setTimeout(() => startRecognition(langCode), 300);
      }
    };

    rec.onend = () => {
      // Auto-restart if still recording (handles Chrome's 60s limit)
      if (mediaRecorderRef.current?.state === "recording") {
        setTimeout(() => startRecognition(langCode), 100);
      }
    };

    recognitionRef.current = rec;
    try { rec.start(); } catch (e) { console.warn("Recognition start error:", e); }
  }, [isRecording]);

  const startRecording = useCallback(async (langCode = "en-US") => {
    try {
      setError(null);
      setTranscript("");
      accTranscriptRef.current = "";
      setDetectedLang(langCode);

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
          channelCount: 1,
        },
      });

      streamRef.current = stream;

      // Audio analyser for waveform
      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.7;
      source.connect(analyser);
      analyserRef.current = analyser;
      monitorAudioLevel(analyser);

      // MediaRecorder (for fallback backend transcription)
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.start(100);

      setIsRecording(true);
      setVoiceState("listening");

      // Start Web Speech API immediately
      startRecognition(langCode);

    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Microphone access denied";
      setError(message);
      setVoiceState("error");
    }
  }, [monitorAudioLevel, setVoiceState, startRecognition]);

  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      // Stop SpeechRecognition
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch {}
        recognitionRef.current = null;
      }

      if (!mediaRecorderRef.current || !isRecording) {
        resolve(null);
        return;
      }

      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
      setAudioLevel(0);

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        chunksRef.current = [];
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }
        setIsRecording(false);
        setVoiceState("processing");
        resolve(blob);
      };

      mediaRecorderRef.current.stop();
    });
  }, [isRecording, setVoiceState]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch {}
      }
    };
  }, []);

  return { isRecording, startRecording, stopRecording, error, audioLevel, transcript, detectedLang };
}
