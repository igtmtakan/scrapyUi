/** @type {import('next').NextConfig} */
const nextConfig = {
  // フロントエンドを4000番ポートで固定
  // Puppeteerが3001番ポートを使用するため
  experimental: {
    // Next.js 15.3.2の安定性向上
  },

  // Server External Packages (Next.js 15.3.2の新しい設定)
  // serverExternalPackages: ['lucide-react'], // transpilePackagesと競合するため無効化

  // TypeScript設定
  typescript: {
    ignoreBuildErrors: false,
  },

  // ESLint設定
  eslint: {
    ignoreDuringBuilds: false,
  },

  // 開発サーバーの設定
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
    CUSTOM_PORT: '4000'
  },

  // WebSocketプロキシ設定（開発時）
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization' },
        ],
      },
    ]
  }
}

module.exports = nextConfig
