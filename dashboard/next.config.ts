import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  turbopack: {
    // Keep workspace detection inside this app even when a root lockfile exists.
    root: process.cwd(),
  },
};

export default nextConfig;
