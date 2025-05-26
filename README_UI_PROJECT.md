# Scrapy-Playwright Web UI プロジェクト

PySpiderのようなWebユーザーインターフェースをScrapy + Playwright統合フレームワークに追加するプロジェクトです。
scrapy-playwrightを使用してJavaScriptが必要なサイトもスクレイピング可能です。

## 主要機能

### 1. プロジェクト管理
- Scrapyプロジェクトの作成、編集、削除
- scrapy-playwright設定の管理
- プロジェクト一覧表示

### 2. スパイダー管理
- スパイダーの一覧表示
- スパイダーコードの編集（コードエディター）
- スパイダーの実行・停止
- Playwrightスパイダーテンプレートの管理
- ブラウザ設定（Chromium、Firefox、WebKit）
- JavaScript対応サイトのスクレイピング

### 3. タスク監視
- クローリングジョブの実行状況監視
- リアルタイムステータス更新
- 実行履歴の表示
- パフォーマンス統計

### 4. 結果表示
- スクレイピング結果の表示
- データのフィルタリング・検索
- 結果のエクスポート（JSON、CSV、XML）
- データの可視化

### 5. 設定管理
- Scrapy設定の管理
- ミドルウェア設定
- パイプライン設定
- 拡張機能設定

### 6. ログ表示
- リアルタイムログ表示
- ログレベルフィルタリング
- ログのダウンロード

## 技術スタック

### フロントエンド
- **Next.js 15**: React フレームワーク
- **React 19**: UIライブラリ
- **Tailwind CSS**: スタイリング
- **TypeScript**: 型安全性
- **Zustand**: 状態管理
- **React Query**: データフェッチング
- **Monaco Editor**: コードエディター
- **Chart.js**: データ可視化

### バックエンド
- **FastAPI**: Python Webフレームワーク
- **Scrapy**: ウェブスクレイピングフレームワーク
- **SQLAlchemy**: ORM
- **Alembic**: データベースマイグレーション
- **WebSocket**: リアルタイム通信
- **Celery**: 非同期タスク処理

### データベース
- **SQLite**: 軽量データベース
- **Prisma**: データベースツールキット

## プロジェクト構造

```
scrapyUI/
├── frontend/                 # Next.js アプリケーション
│   ├── app/                 # App Router
│   │   ├── dashboard/       # ダッシュボード
│   │   ├── projects/        # プロジェクト管理
│   │   ├── spiders/         # スパイダー管理
│   │   ├── tasks/           # タスク監視
│   │   ├── results/         # 結果表示
│   │   └── settings/        # 設定管理
│   ├── components/          # React コンポーネント
│   │   ├── ui/              # 基本UIコンポーネント
│   │   ├── forms/           # フォームコンポーネント
│   │   ├── charts/          # チャートコンポーネント
│   │   └── editors/         # エディターコンポーネント
│   ├── lib/                 # ユーティリティ
│   │   ├── api.ts           # API クライアント
│   │   ├── utils.ts         # ユーティリティ関数
│   │   └── types.ts         # 型定義
│   ├── hooks/               # カスタムフック
│   ├── stores/              # 状態管理
│   └── public/              # 静的ファイル
├── backend/                 # FastAPI バックエンド
│   ├── app/
│   │   ├── api/             # API エンドポイント
│   │   │   ├── projects.py  # プロジェクト API
│   │   │   ├── spiders.py   # スパイダー API
│   │   │   ├── tasks.py     # タスク API
│   │   │   ├── results.py   # 結果 API
│   │   │   └── settings.py  # 設定 API
│   │   ├── models/          # データベースモデル
│   │   ├── services/        # ビジネスロジック
│   │   ├── scrapy_integration/ # Scrapy統合
│   │   └── websocket/       # WebSocket ハンドラー
│   ├── database/            # データベース関連
│   │   ├── migrations/      # マイグレーション
│   │   └── schema.py        # データベーススキーマ
│   └── requirements.txt     # Python依存関係
├── database/
│   ├── schema.prisma        # Prismaスキーマ
│   └── scrapy_ui.db         # SQLiteデータベース
└── scrapy/                  # 既存のScrapyコード
```

## 開発フェーズ

### フェーズ 1: 基盤構築
1. プロジェクト構造の作成
2. データベーススキーマの設計
3. 基本的なAPI構造の構築
4. フロントエンドの基本レイアウト

### フェーズ 2: コア機能実装
1. プロジェクト管理機能
2. スパイダー管理機能
3. 基本的なタスク実行機能

### フェーズ 3: 高度な機能
1. リアルタイム監視
2. 結果表示・可視化
3. ログ表示機能

### フェーズ 4: 最適化・改善
1. パフォーマンス最適化
2. UI/UX改善
3. テスト追加

## 開始手順

1. フロントエンドプロジェクトの初期化
2. バックエンドプロジェクトの初期化
3. データベースの設定
4. 基本的なAPI接続の確立
