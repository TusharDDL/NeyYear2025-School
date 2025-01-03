/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ["localhost"],
  },
  swcMinify: true,
  experimental: {
    forceSwcTransforms: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*/",
        destination: "http://localhost:8000/api/:path*/",
      },
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*/",
      },
    ];
  },
};

module.exports = nextConfig;
