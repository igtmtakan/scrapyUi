# AmazonRanking60テンプレート - ScrapyUI使用ガイド

## 🎉 テンプレート反映完了

AmazonRanking60テンプレートがScrapyUIに正常に反映されました！

### 📊 テンプレート情報
- **ID**: `b3c8f054-68c4-47b3-ba36-47f157f1635a`
- **名前**: `AmazonRanking60`
- **フレームワーク**: `Scrapy`
- **コード行数**: `301行`
- **実績**: `61件取得、96.7%評価抽出成功率`

## 📍 ScrapyUIでの使用方法

### 1. スパイダー作成ページにアクセス
```
http://localhost:4000/projects/8560dd2f-ab6f-433c-b0da-c51c9219a94c/spiders/new
```

### 2. テンプレート選択
1. 「スパイダーテンプレート」ドロップダウンを開く
2. `AmazonRanking60` を選択
3. テンプレートコードが自動的に読み込まれる

### 3. スパイダー設定
- **スパイダー名**: 任意の名前を入力（例: `amazon_software_ranking`）
- **説明**: スパイダーの目的を記述
- **開始URL**: デフォルトで設定済み
- **設定**: 最適化済みの設定が自動適用

### 4. 実行
1. 「保存」ボタンでスパイダーを作成
2. 「実行」ボタンでスクレイピング開始
3. リアルタイムでログと進捗を監視

## 🚀 テンプレートの主な機能

### 高い安定性
- ✅ **HTTPリクエストベース**: Playwrightの複雑さを避けた安定動作
- ✅ **複数セレクター**: 8種類の商品リンクセレクターで取得漏れを防止
- ✅ **エラーハンドリング**: セレクター失敗時の自動フォールバック

### 高精度データ抽出
- ✅ **商品タイトル**: 6種類のセレクターで確実に取得
- ✅ **評価**: "5つ星のうち4.2"形式から数値を正確に抽出
- ✅ **レビュー数**: カンマ区切り数値も正確に処理
- ✅ **価格**: 税込価格を確実に取得
- ✅ **画像URL**: 高解像度画像URLを取得

### ページネーション対応
- ✅ **2ページまで自動処理**: ベストセラーの1〜2ページを完全処理
- ✅ **重複除去**: 重複リンクの自動除去
- ✅ **URL変換**: 相対URLの絶対URL変換

## 📊 実績データ

### 取得成功率
```
総取得件数: 61件
評価抽出成功率: 96.7% (59/61件)
タイトル取得成功率: 95.1% (58/61件)
レビュー数取得成功率: 96.7% (59/61件)
価格取得成功率: 95.1% (58/61件)
```

### 取得データ例
```json
{
  "title": "Windows版 | Minecraft (マインクラフト): Java & Bedrock Edition | オンラインコード版",
  "rating": "5",
  "price": "￥3,564",
  "reviews": "3416",
  "image_url": "https://m.media-amazon.com/images/I/81FnyvKZ8qL.__AC_SX300_SY300_QL70_ML2_.jpg",
  "product_url": "https://www.amazon.co.jp/dp/B0B3R5PL2Y/...",
  "scraped_at": "2025-05-31T22:27:26.340966"
}
```

## ⚙️ カスタマイズ方法

### 1. 対象カテゴリの変更
```python
# start_requests メソッド内で変更
start_url = "https://www.amazon.co.jp/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0"
```

### 2. 取得件数の調整
```python
# parse メソッド内で変更
for link in unique_links[:100]:  # 50件から100件に変更
```

### 3. ページネーション範囲の拡大
```python
# parse メソッド内で変更
if next_page_links and not re.search(r'pg=[2-5]', response.url):  # 5ページまで
```

### 4. 出力形式の変更
ScrapyUIの設定画面で以下の形式を選択可能:
- JSONL形式（デフォルト）
- JSON形式
- CSV形式
- XML形式

## 🔧 設定項目

### パフォーマンス設定
```python
custom_settings = {
    "DOWNLOAD_DELAY": 2,  # リクエスト間隔（秒）
    "RANDOMIZE_DOWNLOAD_DELAY": True,  # ランダム遅延
    "CONCURRENT_REQUESTS": 1,  # 同時リクエスト数
    "CONCURRENT_REQUESTS_PER_DOMAIN": 1,  # ドメイン別同時リクエスト数
}
```

### User-Agent設定
```python
"USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
```

## 📋 使用上の注意

### 利用規約の遵守
- ✅ Amazonの利用規約を必ず確認
- ✅ 過度なリクエストは避ける
- ✅ 商用利用時は特に注意

### レート制限
- ✅ DOWNLOAD_DELAY: 2秒（推奨）
- ✅ CONCURRENT_REQUESTS: 1（推奨）
- ✅ 大量データ取得時は間隔を長めに設定

### エラーハンドリング
- ✅ ネットワークエラー時の自動リトライ
- ✅ セレクター失敗時のフォールバック
- ✅ 不正なデータの除外

## 🎯 期待される結果

### 標準的な実行結果
- **実行時間**: 約1.5〜2分
- **取得件数**: 50〜70件
- **成功率**: 95%以上
- **データ品質**: 高品質な商品情報

### 出力ファイル
- **results.jsonl**: メイン出力ファイル
- **results.json**: JSON形式
- **results.csv**: CSV形式（Excel対応）
- **results.xml**: XML形式

## 🔄 継続的な改善

### 定期的なメンテナンス
- ✅ セレクターの有効性確認
- ✅ Amazonサイト変更への対応
- ✅ パフォーマンスの最適化

### 拡張可能性
- ✅ 他のAmazonカテゴリへの対応
- ✅ 複数国のAmazonサイト対応
- ✅ リアルタイム価格監視機能

## 📞 サポート

### トラブルシューティング
1. **データが取得できない場合**
   - セレクターの確認
   - ネットワーク接続の確認
   - レート制限の調整

2. **エラーが発生する場合**
   - ログの確認
   - 設定の見直し
   - テンプレートの再読み込み

### 更新情報
- テンプレートの更新は随時実施
- 新機能の追加予定
- パフォーマンス改善の継続

---

**AmazonRanking60テンプレートを使用して、効率的で高品質なAmazonデータ収集を実現してください！** 🚀
