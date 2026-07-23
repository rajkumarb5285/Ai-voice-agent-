import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Voice AI Agent — Your Personal AI Companion",
  description:
    "A production-ready personal AI agent with voice mode, long-term memory, multi-agent orchestration, and autonomous task execution. Like ChatGPT Voice Mode + Jarvis.",
  keywords: ["AI assistant", "voice AI", "personal agent", "LangGraph", "ChatGPT alternative"],
  openGraph: {
    title: "Voice AI Agent",
    description: "Your intelligent personal AI companion",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans bg-surface text-white antialiased`}>
        {children}
      </body>
    </html>
  );
}
