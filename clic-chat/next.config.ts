import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  webpack(config) {
    config.externals.push({ '@lancedb/lancedb': '@lancedb/lancedb' })
    return config;
  }
};

export default nextConfig;
