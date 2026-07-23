"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useAppStore } from "@/store/useAppStore";
import {
  MessageSquare, Mic, Brain, CheckSquare, Activity,
  Settings, LogOut, ChevronLeft, ChevronRight, Sparkles
} from "lucide-react";

const navItems = [
  { href: "/chat",     icon: MessageSquare, label: "Chat" },
  { href: "/voice",    icon: Mic,           label: "Voice Mode" },
  { href: "/memory",   icon: Brain,         label: "Memory" },
  { href: "/tasks",    icon: CheckSquare,   label: "Tasks" },
  { href: "/agents",   icon: Activity,      label: "Agents" },
  { href: "/settings", icon: Settings,      label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, setSidebarOpen, logout, user } = useAppStore();

  return (
    <motion.aside
      animate={{ width: sidebarOpen ? 245 : 72 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="relative flex flex-col h-screen bg-[#09090e]/80 backdrop-blur-md border-r border-white/[0.04] overflow-hidden flex-shrink-0 z-20"
    >
      {/* Header Logo */}
      <div className="flex items-center gap-3 px-4.5 h-16 border-b border-white/[0.04]">
        <motion.div
          whileHover={{ rotate: 360, scale: 1.05 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0 shadow-lg shadow-indigo-500/20"
        >
          <Sparkles className="w-4.5 h-4.5 text-white" />
        </motion.div>
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
            >
              <p className="text-sm font-bold text-white tracking-wide">Voice Agent</p>
              <p className="text-[10px] text-white/40 font-semibold tracking-wider uppercase">Neural Network</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Nav Section */}
      <nav className="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto no-scrollbar">
        {navItems.map(({ href, icon: Icon, label }) => {
          const isActive = pathname === href;
          return (
            <Link key={href} href={href}>
              <motion.div
                whileHover={{ x: 2 }}
                transition={{ duration: 0.2 }}
                className={`flex items-center gap-3.5 px-3.5 py-3 rounded-xl cursor-pointer transition-all duration-200 relative group
                  ${isActive
                    ? "bg-gradient-to-r from-brand-600/15 to-purple-600/5 text-brand-300 border border-brand-500/20 shadow-sm"
                    : "text-white/45 hover:text-white hover:bg-white/[0.02]"
                  }`}
              >
                <Icon className={`w-5 h-5 flex-shrink-0 transition-transform group-hover:scale-105 ${isActive ? "text-brand-400" : ""}`} />
                
                <AnimatePresence>
                  {sidebarOpen && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="text-sm font-semibold tracking-wide whitespace-nowrap"
                    >
                      {label}
                    </motion.span>
                  )}
                </AnimatePresence>

                {isActive && (
                  <motion.div
                    layoutId="active-indicator"
                    className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-400 shadow-md shadow-brand-500/50"
                  />
                )}
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* User Info + Logout Panel */}
      <div className="p-3 border-t border-white/[0.04] bg-[#07070a]/40 space-y-1.5">
        {/* User Card */}
        <div className="flex items-center gap-3 px-3 py-3 rounded-2xl bg-white/[0.01] border border-white/[0.03]">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0 shadow-md">
            {user?.username?.[0]?.toUpperCase() || "U"}
          </div>
          <AnimatePresence>
            {sidebarOpen && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="min-w-0 flex-1"
              >
                <p className="text-xs font-bold text-white truncate leading-tight">{user?.full_name || user?.username}</p>
                <p className="text-[10px] text-white/35 truncate mt-0.5">{user?.email}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Logout Button */}
        <button
          onClick={logout}
          className="flex items-center gap-3.5 px-3.5 py-3 rounded-xl text-white/40 hover:text-rose-400 hover:bg-rose-500/10 transition-all duration-200 w-full"
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          <AnimatePresence>
            {sidebarOpen && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-sm font-semibold tracking-wide"
              >
                Terminate Session
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>

      {/* Collapse Toggle Button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="absolute top-1/2 -right-3 transform -translate-y-1/2 w-6 h-6 bg-[#161622] border border-white/[0.05] rounded-full flex items-center justify-center text-white/50 hover:text-white hover:bg-[#20202e] hover:scale-105 transition-all duration-200 z-10"
      >
        {sidebarOpen ? (
          <ChevronLeft className="w-3.5 h-3.5" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5" />
        )}
      </button>
    </motion.aside>
  );
}
