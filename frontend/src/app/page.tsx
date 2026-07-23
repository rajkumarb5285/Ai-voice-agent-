"use client";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Sparkles, Mic, Brain, Zap, User, Mail, Lock } from "lucide-react";
import { authApi } from "@/lib/api";
import { useAppStore } from "@/store/useAppStore";
import { signInWithEmail, signUpWithEmail, signInWithGoogle } from "@/lib/firebase";


const features = [
  { icon: Mic, title: "Voice-First Interaction", desc: "Ultra-low latency natural voice conversations" },
  { icon: Brain, title: "Long-Term Memory", desc: "Remembers your preferences, context, and goals" },
  { icon: Zap, title: "10 Specialist Agents", desc: "Orchestrated collaborative experts for deep tasks" },
  { icon: Sparkles, title: "Autonomous Actions", desc: "Plans, designs, and executes task lists" },
];

export default function LandingPage() {
  const router = useRouter();
  const { setAuth, token, user } = useAppStore();
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [isHydrated, setIsHydrated] = useState(false);

  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
    full_name: "",
  });

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Hydration guard - redirect to chat if already logged in
  useEffect(() => {
    if (isHydrated && token && user) {
      router.push("/chat");
    }
  }, [isHydrated, token, user, router]);

  const handleGoogleSignIn = async () => {

    setIsLoading(true);
    setError("");
    try {
      const userCred = await signInWithGoogle();
      const idToken = await userCred.user.getIdToken();
      const res = await authApi.firebaseLogin(idToken);
      const { access_token, user: userData } = res.data;
      setAuth(userData, access_token);
      router.push("/chat");
    } catch (err: any) {
      setError(err?.message || "Google Sign-In failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      let userCred;
      if (isLogin) {
        userCred = await signInWithEmail(form.email, form.password);
      } else {
        userCred = await signUpWithEmail(form.email, form.password, form.full_name, form.username);
      }
      const idToken = await userCred.user.getIdToken();
      const res = await authApi.firebaseLogin(idToken);
      const { access_token, user: userData } = res.data;
      setAuth(userData, access_token);
      router.push("/chat");
    } catch (err: any) {
      // Fallback to local authentication if Firebase Auth or Backend API is offline
      try {
        let res;
        if (isLogin) {
          res = await authApi.login({ email: form.email, password: form.password });
        } else {
          res = await authApi.register({
            email: form.email,
            username: form.username,
            password: form.password,
            full_name: form.full_name,
          });
        }
        const { access_token, user: userData } = res.data;
        setAuth(userData, access_token);
        router.push("/chat");
      } catch (fallbackErr: any) {
        const msg = fallbackErr?.response?.data?.detail || err?.message || "Authentication failed";
        setError(Array.isArray(msg) ? msg[0]?.msg || "Error" : msg);
      }
    } finally {
      setIsLoading(false);
    }
  };


  if (!isHydrated) {
    return (
      <div className="min-h-screen bg-[#07070a] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-600 to-purple-600 flex items-center justify-center animate-pulse">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <span className="text-white/40 text-sm">Synchronizing neural link...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen mesh-bg flex overflow-hidden">
      {/* Left: Premium Branding Section */}
      <div className="hidden lg:flex flex-col justify-between p-16 w-1/2 relative overflow-hidden border-r border-white/[0.03]">
        {/* Abstract background grids/orbs */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none" />
        <div className="absolute top-[20%] right-[10%] w-[350px] h-[350px] rounded-full bg-brand-500/10 blur-[100px] animate-pulse-slow" />
        <div className="absolute bottom-[10%] left-[20%] w-[250px] h-[250px] rounded-full bg-purple-500/10 blur-[80px]" />

        {/* Top Logo */}
        <div className="flex items-center gap-3 relative z-10">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-wide">VOICE AI COMPANION</h1>
            <p className="text-[10px] text-white/40 uppercase tracking-widest font-semibold">Autonomous Intelligence</p>
          </div>
        </div>

        {/* Hero message */}
        <div className="relative z-10 max-w-lg my-auto space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-5xl font-extrabold leading-[1.15] text-white tracking-tight mb-4">
              Step into the future of <br />
              <span className="gradient-text bg-gradient-to-r from-brand-400 via-purple-400 to-pink-400">conversational AI.</span>
            </h2>
            <p className="text-white/50 text-base leading-relaxed">
              An ecosystem of collaborative expert agents at your commands. Speak naturally, manage memories semantically, and delegate complex tasks seamlessly.
            </p>
          </motion.div>

          {/* Features cards */}
          <div className="grid grid-cols-2 gap-4 pt-4">
            {features.map(({ icon: Icon, title, desc }, idx) => (
              <motion.div
                key={title}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                className="glass rounded-2xl p-4 hover:border-brand-500/30 transition-all duration-300 group hover:translate-y-[-2px] relative overflow-hidden"
              >
                <div className="w-9 h-9 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center mb-3 group-hover:bg-brand-500/20 transition-all">
                  <Icon className="w-4 h-4 text-brand-400" />
                </div>
                <h3 className="text-sm font-semibold text-white/90 mb-1">{title}</h3>
                <p className="text-xs text-white/40 leading-snug">{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Footer info */}
        <div className="text-xs text-white/30 relative z-10 flex justify-between items-center">
          <span>Enterprise grade security & privacy built-in</span>
          <span>v1.2.0</span>
        </div>
      </div>

      {/* Right: Auth form */}
      <div className="flex-1 flex items-center justify-center px-6 lg:px-16 relative">
        {/* Mobile top decorations */}
        <div className="absolute top-[-10%] right-[-10%] w-[300px] h-[300px] rounded-full bg-pink-500/5 blur-[80px] pointer-events-none lg:hidden" />
        
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-[440px]"
        >
          <div className="glass rounded-[32px] p-8 lg:p-10 shadow-3xl border border-white/[0.05] relative overflow-hidden">
            {/* Top decorative gradient glow */}
            <div className="absolute top-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-brand-500 to-transparent opacity-60" />

            {/* Mobile Header Logo */}
            <div className="flex lg:hidden items-center gap-3 mb-8">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Sparkles className="w-4.5 h-4.5 text-white" />
              </div>
              <div>
                <span className="font-bold text-white text-sm">Voice AI Agent</span>
                <p className="text-[9px] text-white/40 uppercase tracking-wider">Personal Companion</p>
              </div>
            </div>

            <h2 className="text-2xl font-bold text-white tracking-tight mb-1">
              {isLogin ? "Welcome Back" : "Begin Your Journey"}
            </h2>
            <p className="text-white/40 text-xs mb-8">
              {isLogin ? "Re-connect to your autonomous companion" : "Create an account to deploy your voice assistant"}
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <AnimatePresence mode="popLayout">
                {!isLogin && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-4 overflow-hidden"
                    key="signup-fields"
                  >
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-white/50 tracking-wide uppercase">Full Name</label>
                      <div className="relative">
                        <User className="w-4 h-4 text-white/30 absolute left-3.5 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          placeholder="John Doe"
                          value={form.full_name}
                          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                          className="w-full bg-[#12121c]/80 border border-white/[0.05] rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none transition-all"
                        />
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-white/50 tracking-wide uppercase">Username</label>
                      <div className="relative">
                        <User className="w-4 h-4 text-white/30 absolute left-3.5 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          placeholder="johndoe"
                          value={form.username}
                          onChange={(e) => setForm({ ...form, username: e.target.value })}
                          required={!isLogin}
                          className="w-full bg-[#12121c]/80 border border-white/[0.05] rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none transition-all"
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-white/50 tracking-wide uppercase">Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-white/30 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    placeholder="name@domain.com"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    required
                    className="w-full bg-[#12121c]/80 border border-white/[0.05] rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none transition-all"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-white/50 tracking-wide uppercase">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-white/30 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    required
                    className="w-full bg-[#12121c]/80 border border-white/[0.05] rounded-xl pl-10 pr-10 py-3 text-sm text-white placeholder-white/20 focus:outline-none transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {error && (
                <motion.p
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-rose-400 text-xs bg-rose-500/10 border border-rose-500/15 rounded-xl px-4 py-2.5 leading-relaxed"
                >
                  {error}
                </motion.p>
              )}

              <motion.button
                type="submit"
                disabled={isLoading}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-brand-600 via-indigo-600 to-purple-600 text-white text-sm font-semibold hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-xl shadow-brand-900/20"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Executing Authentication...
                  </span>
                ) : isLogin ? (
                  "Unlock Workspace"
                ) : (
                  "Initialize Account"
                )}
              </motion.button>
            </form>

            <p className="mt-8 text-center text-xs text-white/40">
              {isLogin ? "First time using Voice AI? " : "Already initialized? "}
              <button
                onClick={() => { setIsLogin(!isLogin); setError(""); }}
                className="text-brand-400 hover:text-brand-300 font-semibold transition-colors focus:outline-none"
              >
                {isLogin ? "Deploy Profile" : "Authenticate Profile"}
              </button>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
