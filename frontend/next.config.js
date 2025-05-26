/** @type {import('next').NextConfig} */
const nextConfig = {
  // フロントエンドを4000番ポートで固定
  // Puppeteerが3001番ポートを使用するため
  experimental: {
    // 必要に応じて実験的機能を有効化
  },
  
  // 開発サーバーの設定
  async rewrites() {
    return []
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
