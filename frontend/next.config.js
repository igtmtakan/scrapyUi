/** @type {import('next').NextConfig} */
const nextConfig = {
  // フロントエンドを4000番ポートで固定
  // Puppeteerが3001番ポートを使用するため
  experimental: {
    // Next.js 15.3.2の安定性向上
  },

  // TypeScript設定
  typescript: {
    ignoreBuildErrors: false,
  },

  // ESLint設定
  eslint: {
    ignoreDuringBuilds: false,
  },

  // 開発サーバーの設定 - バックエンドAPIプロキシ
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*'
      }
    ]
  },

  // 環境変数の設定
  env: {
    CUSTOM_PORT: '4000',
    NEXT_PUBLIC_API_URL: process.env.NODE_ENV === 'production'
      ? 'https://your-production-api.com'
      : 'http://localhost:8000'
  },

  // CORS設定とセキュリティヘッダー
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization' },
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Max-Age', value: '86400' },
        ],
      },
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'origin-when-cross-origin' },
        ],
      },
    ]
  },

  // エラーハンドリングの改善
  onDemandEntries: {
    // ページがメモリに保持される時間（ミリ秒）
    maxInactiveAge: 25 * 1000,
    // 同時にメモリに保持されるページ数
    pagesBufferLength: 2,
  },

  // パフォーマンス最適化
  compress: true,
  poweredByHeader: false,

  // 開発時のログレベル
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
}

module.exports = nextConfig
