import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  basePath: "/application-testing",
  trailingSlash: true,
};

export default nextConfig;
