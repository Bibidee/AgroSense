const nextConfig = {
  experimental: { serverActions: { bodySizeLimit: "8mb" } },
  images: { remotePatterns: [{ protocol: "https", hostname: "**" }] },
};
export default nextConfig;
