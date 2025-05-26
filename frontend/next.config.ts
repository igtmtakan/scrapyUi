import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // プロキシを無効化（直接バックエンドに接続）
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/:path*',
  //       destination: 'http://localhost:8000/api/:path*',
  //     },
  //   ];
  // },
  // 開発環境でのCORS問題を回避
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET, POST, PUT, DELETE, OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: '*' },
        ],
      },
    ];
  },
};

export default nextConfig;
