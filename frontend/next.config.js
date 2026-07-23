/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  images: { unoptimized: true },
  reactStrictMode: true,

  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "",
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || "",
  },
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    return [
      // Proxy all /api/* REST calls to backend
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      // Proxy /health to backend root-level health check
      {
        source: "/health",
        destination: `${backendUrl}/health`,
      },
      // Proxy WebSocket upgrade path (for Next.js HTTP upgrade passthrough)
      {
        source: "/ws/:path*",
        destination: `${backendUrl}/ws/:path*`,
      },
    ];
  },
  // Allow Next.js dev server to proxy WebSocket connections
  experimental: {},
};

module.exports = nextConfig;
