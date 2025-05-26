#!/usr/bin/env python3
"""
ScrapyUIデータベースのスパイダーコードを最新ファイルで更新するスクリプト
"""

import sqlite3
import os
import sys
from pathlib import Path

def update_spider_code_in_database():
    """データベースのスパイダーコードを最新ファイルで更新"""

    # データベースファイルのパス
    db_path = Path("backend/scrapy_ui.db")

    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False

    # 最新のスパイダーファイルのパス
    spider_file = Path("user_scripts/admin-user-id/optimized_puppeteer_scraper.py")

    if not spider_file.exists():
        print(f"❌ スパイダーファイルが見つかりません: {spider_file}")
        return False

    try:
        # 最新のスパイダーコードを読み取り
        with open(spider_file, 'r', encoding='utf-8') as f:
            latest_code = f.read()

        print(f"✅ 最新のスパイダーコードを読み取りました ({len(latest_code)} 文字)")

        # データベースに接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 既存のスパイダーを検索
        cursor.execute("""
            SELECT id, name, code FROM spiders
            WHERE name = 'optimized_puppeteer_scraper'
        """)

        spiders = cursor.fetchall()

        if not spiders:
            print("⚠️ データベースにoptimized_puppeteer_scraperが見つかりません")
            print("新しいスパイダーとして追加します...")

            # 新しいスパイダーとして追加
            import uuid
            spider_id = str(uuid.uuid4())

            cursor.execute("""
                INSERT INTO spiders (id, name, code, template, settings, project_id, user_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                spider_id,
                'optimized_puppeteer_scraper',
                latest_code,
                'advanced',
                '{}',
                'default-project',
                'admin-user-id'
            ))

            print(f"✅ 新しいスパイダーを追加しました (ID: {spider_id})")
        else:
            # 既存のスパイダーを強制更新
            for spider_id, spider_name, old_code in spiders:
                print(f"🔄 スパイダーを強制更新中: {spider_name} (ID: {spider_id})")
                print(f"   古いコード: {len(old_code)} 文字")
                print(f"   新しいコード: {len(latest_code)} 文字")

                # 古いコードに問題のあるインポートが含まれているかチェック
                if "from scrapy_ui.nodejs_client import NodeJSClient" in old_code:
                    print("   ⚠️ 古いコードに問題のあるインポートが検出されました")

                cursor.execute("""
                    UPDATE spiders
                    SET code = ?, updated_at = datetime('now')
                    WHERE id = ?
                """, (latest_code, spider_id))

                print(f"✅ スパイダーコードを強制更新しました: {spider_name}")

                # 更新後の確認
                cursor.execute("SELECT code FROM spiders WHERE id = ?", (spider_id,))
                updated_code = cursor.fetchone()[0]
                if "from scrapy_ui.nodejs_client import NodeJSClient" not in updated_code:
                    print("   ✅ 問題のあるインポートが除去されました")
                else:
                    print("   ❌ まだ問題のあるインポートが残っています")

        # 変更をコミット
        conn.commit()

        # 更新後の確認
        cursor.execute("""
            SELECT id, name, LENGTH(code) as code_length
            FROM spiders
            WHERE name = 'optimized_puppeteer_scraper'
        """)

        updated_spiders = cursor.fetchall()
        print(f"\n📊 更新後の状態:")
        for spider_id, spider_name, code_length in updated_spiders:
            print(f"   ID: {spider_id}")
            print(f"   名前: {spider_name}")
            print(f"   コード長: {code_length} 文字")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 ScrapyUIデータベース更新スクリプト開始")
    print("=" * 50)

    # 現在のディレクトリを確認
    current_dir = Path.cwd()
    print(f"📁 現在のディレクトリ: {current_dir}")

    # ScrapyUIのルートディレクトリに移動
    if current_dir.name != "scrapyUI":
        scrapy_ui_dir = current_dir / "scrapyUI"
        if scrapy_ui_dir.exists():
            os.chdir(scrapy_ui_dir)
            print(f"📁 ScrapyUIディレクトリに移動: {scrapy_ui_dir}")
        else:
            print("⚠️ ScrapyUIディレクトリが見つかりません")

    # データベース更新を実行
    success = update_spider_code_in_database()

    if success:
        print("\n🎉 データベースの更新が完了しました！")
        print("💡 これで、WebUIから最新のスパイダーコードが実行されます")
    else:
        print("\n❌ データベースの更新に失敗しました")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
