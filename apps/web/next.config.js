/** @type {import('next').NextConfig} */
const backendBase =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000" // CRG: keep local Next requests wired to the FastAPI server when env vars are missing.
const apiPrefix = process.env.NEXT_PUBLIC_API_PREFIX || "/api/v1"

const nextConfig = {
  output: "standalone",
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    domains: [
      "localhost",
      "i.ytimg.com",
      "yt3.ggpht.com",
      "yt3.googleusercontent.com",
      "picsum.photos",
      "via.placeholder.com",
    ],
    remotePatterns: [
      { protocol: "https", hostname: "i.ytimg.com" },
      { protocol: "https", hostname: "yt3.ggpht.com" },
      { protocol: "https", hostname: "yt3.googleusercontent.com" },
      { protocol: "https", hostname: "picsum.photos" },
      { protocol: "https", hostname: "via.placeholder.com" },
      { protocol: "https", hostname: "img.youtube.com" },
      { protocol: "https", hostname: "**.googleusercontent.com" },
      { protocol: "https", hostname: "**.ggpht.com" },
    ],
  },
  experimental: {
    ppr: false,
    optimizePackageImports: ["lucide-react", "recharts", "framer-motion"],
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || "",
    NEXT_PUBLIC_API_PREFIX: apiPrefix,
  },
  async rewrites() {
    if (!backendBase) return [] // CRG: production/standalone still needs the same API proxy when web and API run on separate ports.
    return [
      {
        source: `${apiPrefix}/:path*`,
        destination: `${backendBase}${apiPrefix}/:path*`,
      },
      {
        source: "/health",
        destination: `${backendBase}/health`,
      },
    ]
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
