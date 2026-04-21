/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/api-proxy/:path*',
          destination: 'http://backend:8000/:path*',
        },
      ],
    };
  },
};

export default nextConfig;
