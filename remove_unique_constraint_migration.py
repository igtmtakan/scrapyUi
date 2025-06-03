#!/usr/bin/env python3
"""
データベースマイグレーション: ResultsテーブルのUNIQUE制約を削除

このスクリプトは以下の変更を行います:
1. results テーブルの (task_id, data_hash) UNIQUE制約を削除
2. パフォーマンス向上のためのインデックスは維持
"""

import sqlite3
import os
from pathlib import Path

def remove_unique_constraint():
    """ResultsテーブルのUNIQUE制約を削除"""
    
    # データベースファイルのパス
    db_path = Path("backend/database/scrapy_ui.db")
    
    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False
    
    # バックアップを作成
    backup_path = db_path.with_suffix('.db.backup_unique_constraint')
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"📁 バックアップを作成しました: {backup_path}")
    
    try:
        # データベースに接続
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("🔍 現在のresultsテーブル構造を確認中...")
        
        # 現在のテーブル構造を確認
        cursor.execute("PRAGMA table_info(results)")
        columns = cursor.fetchall()
        
        print("📋 現在のカラム:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
        
        # インデックス情報を確認
        cursor.execute("PRAGMA index_list(results)")
        indexes = cursor.fetchall()
        
        print("\n📋 現在のインデックス:")
        for index in indexes:
            print(f"  - {index[1]} (unique: {index[2]})")
            
            # インデックスの詳細を確認
            cursor.execute(f"PRAGMA index_info({index[1]})")
            index_info = cursor.fetchall()
            for info in index_info:
                cursor.execute("PRAGMA table_info(results)")
                table_columns = cursor.fetchall()
                column_name = table_columns[info[1]][1]
                print(f"    - カラム: {column_name}")
        
        print("\n🔧 新しいテーブルを作成中...")
        
        # 新しいテーブルを作成（UNIQUE制約なし）
        cursor.execute("""
            CREATE TABLE results_new (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                crawl_start_datetime TIMESTAMP,
                item_acquired_datetime TIMESTAMP,
                data_hash TEXT,
                task_id TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)
        print("✅ 新しいテーブル results_new を作成しました")
        
        # 通常のインデックスを作成（UNIQUE制約なし）
        cursor.execute("""
            CREATE INDEX idx_task_data_hash_new ON results_new (task_id, data_hash)
        """)
        print("✅ 新しいインデックス idx_task_data_hash_new を作成しました")
        
        # data_hashのインデックスも作成
        cursor.execute("""
            CREATE INDEX idx_data_hash_new ON results_new (data_hash)
        """)
        print("✅ 新しいインデックス idx_data_hash_new を作成しました")
        
        # データを新しいテーブルにコピー
        print("\n📊 データをコピー中...")
        cursor.execute("""
            INSERT INTO results_new 
            SELECT id, data, url, created_at, crawl_start_datetime, 
                   item_acquired_datetime, data_hash, task_id 
            FROM results
        """)
        
        # コピーされたレコード数を確認
        cursor.execute("SELECT COUNT(*) FROM results_new")
        new_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM results")
        old_count = cursor.fetchone()[0]
        
        print(f"📊 コピー完了: {old_count} → {new_count} レコード")
        
        if new_count != old_count:
            print("❌ レコード数が一致しません。マイグレーションを中止します。")
            conn.rollback()
            return False
        
        # 古いテーブルを削除
        cursor.execute("DROP TABLE results")
        print("🗑️ 古いテーブルを削除しました")
        
        # 新しいテーブルの名前を変更
        cursor.execute("ALTER TABLE results_new RENAME TO results")
        print("✅ 新しいテーブルの名前を results に変更しました")
        
        # 変更をコミット
        conn.commit()
        
        # 最終確認
        print("\n🔍 マイグレーション後の確認...")
        cursor.execute("PRAGMA table_info(results)")
        final_columns = cursor.fetchall()
        
        print("📋 最終的なカラム:")
        for column in final_columns:
            print(f"  - {column[1]} ({column[2]})")
        
        cursor.execute("PRAGMA index_list(results)")
        final_indexes = cursor.fetchall()
        
        print("\n📋 最終的なインデックス:")
        for index in final_indexes:
            print(f"  - {index[1]} (unique: {index[2]})")
        
        cursor.execute("SELECT COUNT(*) FROM results")
        final_count = cursor.fetchone()[0]
        print(f"\n📊 最終レコード数: {final_count}")
        
        print("\n✅ UNIQUE制約の削除が完了しました！")
        print("💡 これで重複データのインサートが可能になります。")
        
        return True
        
    except Exception as e:
        print(f"❌ マイグレーションエラー: {e}")
        conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 UNIQUE制約削除マイグレーションを開始します...")
    print("⚠️  このマイグレーションは results テーブルの UNIQUE制約を削除します。")
    
    confirm = input("続行しますか？ (y/N): ")
    if confirm.lower() != 'y':
        print("❌ マイグレーションをキャンセルしました。")
        exit(1)
    
    success = remove_unique_constraint()
    
    if success:
        print("\n🎉 マイグレーション完了！")
        print("💡 バルクインサート処理で重複エラーが発生しなくなります。")
    else:
        print("\n❌ マイグレーション失敗")
        print("💡 バックアップファイルから復元してください。")
