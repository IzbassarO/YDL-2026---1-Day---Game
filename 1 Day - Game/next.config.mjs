/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // game owns a single RAF loop; avoid double-mount in dev
};

export default nextConfig;
