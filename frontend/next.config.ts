import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // Provision's source catalog lives at the repository root.
  turbopack: {
    root: path.join(process.cwd(), ".."),
  },
};

export default nextConfig;
