"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { useAppStore } from "@/store/useAppStore";
import { authApi } from "@/lib/api";
import { Toaster } from "react-hot-toast";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { token, user, logout } = useAppStore();
  const [isHydrated, setIsHydrated] = useState(false);
  const [isValidating, setIsValidating] = useState(true);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Validate stored token against backend on every load
  // This catches stale tokens from previous container/DB sessions
  useEffect(() => {
    if (!isHydrated) return;
    if (!token || !user) {
      setIsValidating(false);
      router.push("/");
      return;
    }
    authApi.me()
      .then(() => setIsValidating(false))
      .catch(() => {
        // Token is invalid (user not found, expired secret, etc.) — force re-login
        logout();
        router.push("/");
      });
  }, [isHydrated]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!isHydrated || isValidating || !token || !user) return null;

  return (
    <div className="flex h-screen overflow-hidden mesh-bg">
      <Sidebar />
      <main className="flex-1 overflow-hidden flex flex-col">
        {children}
      </main>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#1c1c26",
            color: "#fff",
            border: "1px solid rgba(255,255,255,0.08)",
            fontSize: "13px",
          },
        }}
      />
    </div>
  );
}
