"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { Settings, Volume2, Mic, Brain, Shield, Bell, Palette, User, Sparkles } from "lucide-react";
import { useAppStore } from "@/store/useAppStore";
import { memoryApi } from "@/lib/api";
import toast from "react-hot-toast";
import { JarvisAvatar } from "@/components/voice/JarvisAvatar";
import type { VoiceState } from "@/types";

const VOICE_OPTIONS = [
  { id: "alloy",   name: "Alloy",   desc: "Neutral balance" },
  { id: "nova",    name: "Nova",    desc: "Warm female tone" },
  { id: "shimmer", name: "Shimmer", desc: "Gentle acoustic" },
  { id: "echo",    name: "Echo",    desc: "Deep male resonant" },
  { id: "fable",   name: "Fable",   desc: "Expressive prose" },
  { id: "onyx",    name: "Onyx",    desc: "Authoritative low" },
];

export default function SettingsPage() {
  const {
    user, selectedVoice, setSelectedVoice,
    ttsEnabled, setTtsEnabled,
    autoListen, setAutoListen,
    theme, setTheme,
  } = useAppStore();

  const [profileUpdates, setProfileUpdates] = useState({
    name: user?.full_name || "",
    goals: ((user?.profile?.goals as string[]) || []).join(", "),
    skills: ((user?.profile?.skills as string[]) || []).join(", "),
    timezone: (user?.profile?.timezone as string) || "UTC",
  });

  const [isSaving, setIsSaving] = useState(false);
  const [previewState, setPreviewState] = useState<VoiceState>("idle");

  const handleVoiceSelect = (voiceId: string) => {
    setSelectedVoice(voiceId);
    setPreviewState("speaking");
    setTimeout(() => {
      setPreviewState("idle");
    }, 2000);
  };

  const saveProfile = async () => {
    setIsSaving(true);
    try {
      await memoryApi.updateProfile({
        name: profileUpdates.name,
        goals: profileUpdates.goals.split(",").map((s) => s.trim()).filter(Boolean),
        skills: profileUpdates.skills.split(",").map((s) => s.trim()).filter(Boolean),
        timezone: profileUpdates.timezone,
        voice: selectedVoice,
      });
      toast.success("Profile records updated");
    } catch {
      toast.error("Failed to update profile records");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#07070a] relative overflow-y-auto">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,rgba(99,102,241,0.01)_0%,transparent_60%)] pointer-events-none" />

      {/* Header Panel */}
      <div className="px-6 py-5 border-b border-white/[0.04] bg-[#09090e]/60 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <Settings className="w-4.5 h-4.5 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-wide">Workspace Settings</h1>
            <p className="text-[10px] text-white/35 font-semibold uppercase tracking-wider mt-0.5">Parameters & identity</p>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6 max-w-2xl">
        {/* Profile Details */}
        <Section icon={Brain} title="AI Persona Settings" description="Tune parameters used by the assistant to customize cognitive recall.">
          <div className="space-y-4">
            <Field
              label="Display Identity (Name)"
              value={profileUpdates.name}
              onChange={(v) => setProfileUpdates({ ...profileUpdates, name: v })}
              placeholder="Your name"
            />
            <Field
              label="System Goals (comma-separated)"
              value={profileUpdates.goals}
              onChange={(v) => setProfileUpdates({ ...profileUpdates, goals: v })}
              placeholder="Learn AI coding, Exercise weekly, Read tech logs"
            />
            <Field
              label="Skills & Expertise (comma-separated)"
              value={profileUpdates.skills}
              onChange={(v) => setProfileUpdates({ ...profileUpdates, skills: v })}
              placeholder="Python development, UX Design, Orchestration"
            />
            <Field
              label="Local Timezone"
              value={profileUpdates.timezone}
              onChange={(v) => setProfileUpdates({ ...profileUpdates, timezone: v })}
              placeholder="e.g. UTC, Europe/London, America/Chicago"
            />
            <button
              onClick={saveProfile}
              disabled={isSaving}
              className="w-full mt-2 py-3 bg-gradient-to-r from-brand-600 via-indigo-600 to-purple-600 text-white rounded-xl text-sm font-semibold hover:brightness-110 disabled:opacity-50 transition-all shadow-md"
            >
              {isSaving ? "Saving details..." : "Save Profile Details"}
            </button>
          </div>
        </Section>

        {/* Voice Modulation */}
        <Section icon={Volume2} title="Audio Modulation" description="Toggle text-to-speech feedback parameters and pick synthesis models.">
          <div className="space-y-5">
            <Toggle
              label="Interactive Text-to-Speech"
              description="Deploy AI speech module to speak all textual responses aloud"
              checked={ttsEnabled}
              onChange={setTtsEnabled}
            />
            <Toggle
              label="Continuous Auto-Listening"
              description="Automatically trigger human input voice recorder after AI finishes speaking"
              checked={autoListen}
              onChange={setAutoListen}
            />

            {/* Voice select grid */}
            <div className="pt-3 border-t border-white/[0.03]">
              <div className="flex items-center justify-between mb-3">
                <p className="text-[10px] font-bold text-white/50 tracking-wide uppercase">Synthesis Model Voice</p>
                <div className="w-16 h-16 flex items-center justify-center relative pointer-events-none -my-4 -mr-2">
                  <JarvisAvatar state={previewState} size="sm" />
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {VOICE_OPTIONS.map((v) => (
                  <button
                    key={v.id}
                    onClick={() => handleVoiceSelect(v.id)}
                    className={`p-3.5 rounded-xl border text-left transition-all duration-200 ${
                      selectedVoice === v.id
                        ? "bg-brand-600/15 border-brand-500/25 text-brand-300 shadow-sm"
                        : "bg-[#12121c]/40 border-white/[0.04] text-white/50 hover:text-white hover:border-white/[0.08]"
                    }`}
                  >
                    <p className="text-xs font-bold tracking-wide">{v.name}</p>
                    <p className="text-[10px] opacity-50 mt-1 leading-snug">{v.desc}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Section>

        {/* Theme Preferences */}
        <Section icon={Palette} title="Appearance Settings" description="Modulate the client design interface color modes.">
          <div className="flex gap-3">
            {(["dark", "light"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTheme(t)}
                className={`flex-1 py-3 rounded-xl border capitalize text-xs font-bold tracking-wider transition-all duration-200 ${
                  theme === t
                    ? "bg-brand-600/15 border-brand-500/25 text-brand-300"
                    : "bg-[#12121c]/40 border-white/[0.04] text-white/55"
                }`}
              >
                {t} Interface Mode
              </button>
            ))}
          </div>
        </Section>

        {/* User Account Registry */}
        <Section icon={Shield} title="Account & Identity Registry" description="Identity records verified by the database model.">
          <div className="space-y-1 bg-[#09090e]/40 p-4 border border-white/[0.03] rounded-2xl">
            <InfoRow label="Email Identity" value={user?.email || "—"} />
            <InfoRow label="Database Username" value={user?.username || "—"} />
            <InfoRow label="Deployment Date" value={user?.created_at ? new Date(user.created_at).toLocaleDateString([], { year: "numeric", month: "long", day: "numeric" }) : "—"} />
          </div>
        </Section>
      </div>
    </div>
  );
}

function Section({ icon: Icon, title, description, children }: {
  icon: React.ElementType;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-[#12121c]/40 border border-white/[0.04] rounded-2xl p-5 shadow-sm"
    >
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4 text-brand-400" />
        <h2 className="text-sm font-bold text-white tracking-wide uppercase">{title}</h2>
      </div>
      <p className="text-xs text-white/35 mb-4 leading-relaxed">{description}</p>
      {children}
    </motion.div>
  );
}

function Toggle({ label, description, checked, onChange }: {
  label: string; description: string; checked: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        <p className="text-xs font-bold text-white/80 tracking-wide">{label}</p>
        <p className="text-[11px] text-white/35 leading-relaxed mt-0.5">{description}</p>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`relative w-11 h-6 rounded-full transition-colors ${checked ? "bg-brand-600" : "bg-white/[0.05] border border-white/[0.03]"}`}
      >
        <motion.div
          animate={{ x: checked ? 20 : 2 }}
          className="absolute top-1 w-4 h-4 bg-white rounded-full shadow-md"
        />
      </button>
    </div>
  );
}

function Field({ label, value, onChange, placeholder }: {
  label: string; value: string; onChange: (v: string) => void; placeholder: string;
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-[10px] font-semibold text-white/50 tracking-wide uppercase">{label}</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-[#09090e] border border-white/[0.05] rounded-xl px-4 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none transition-all"
      />
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-2.5 border-b border-white/[0.03] last:border-0">
      <span className="text-xs text-white/40 font-semibold">{label}</span>
      <span className="text-xs text-white/85 font-bold tracking-wide">{value}</span>
    </div>
  );
}
