#!/usr/bin/env python3
"""
データベースマイグレーション: プロジェクト名の一意制約をユーザー別に変更

このスクリプトは以下の変更を行います:
1. projects.name の UNIQUE 制約を削除
2. (name, user_id) の複合 UNIQUE 制約を追加
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """データベースマイグレーションを実行"""
    
    # データベースファイルのパス
    db_path = Path("database/scrapyui.db")
    
    if not db_path.exists():
        print(f"データベースファイルが見つかりません: {db_path}")
        return False
    
    # バックアップを作成
    backup_path = db_path.with_suffix('.db.backup')
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"バックアップを作成しました: {backup_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("マイグレーション開始...")
        
        # 1. 現在のテーブル構造を確認
        cursor.execute("PRAGMA table_info(projects)")
        columns = cursor.fetchall()
        print("現在のprojectsテーブル構造:")
        for col in columns:
            print(f"  {col}")
        
        # 2. 現在のインデックスを確認
        cursor.execute("PRAGMA index_list(projects)")
        indexes = cursor.fetchall()
        print("現在のインデックス:")
        for idx in indexes:
            print(f"  {idx}")
        
        # 3. 新しいテーブルを作成（一時的）
        cursor.execute("""
            CREATE TABLE projects_new (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                path TEXT UNIQUE NOT NULL,
                scrapy_version TEXT DEFAULT '2.11.0',
                settings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                user_id TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(name, user_id)
            )
        """)
        print("新しいテーブル projects_new を作成しました")
        
        # 4. データを新しいテーブルにコピー
        cursor.execute("""
            INSERT INTO projects_new 
            SELECT id, name, description, path, scrapy_version, settings, 
                   created_at, updated_at, user_id 
            FROM projects
        """)
        print("データを新しいテーブルにコピーしました")
        
        # 5. 古いテーブルを削除
        cursor.execute("DROP TABLE projects")
        print("古いテーブルを削除しました")
        
        # 6. 新しいテーブルの名前を変更
        cursor.execute("ALTER TABLE projects_new RENAME TO projects")
        print("新しいテーブルの名前を変更しました")
        
        # 7. インデックスを再作成
        cursor.execute("CREATE INDEX ix_projects_id ON projects (id)")
        cursor.execute("CREATE INDEX ix_projects_name ON projects (name)")
        print("インデックスを再作成しました")
        
        # 8. 変更をコミット
        conn.commit()
        print("マイグレーション完了!")
        
        # 9. 新しいテーブル構造を確認
        cursor.execute("PRAGMA table_info(projects)")
        columns = cursor.fetchall()
        print("新しいprojectsテーブル構造:")
        for col in columns:
            print(f"  {col}")
            
        cursor.execute("PRAGMA index_list(projects)")
        indexes = cursor.fetchall()
        print("新しいインデックス:")
        for idx in indexes:
            print(f"  {idx}")
        
        return True
        
    except Exception as e:
        print(f"マイグレーションエラー: {e}")
        # エラーが発生した場合はバックアップから復元
        if backup_path.exists():
            shutil.copy2(backup_path, db_path)
            print("バックアップから復元しました")
        return False
        
    finally:
        conn.close()

def test_migration():
    """マイグレーション後のテストを実行"""
    db_path = Path("database/scrapyui.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\nマイグレーションテスト開始...")
        
        # テスト1: 同じユーザーで同じプロジェクト名は作成できない
        try:
            cursor.execute("""
                INSERT INTO projects (id, name, path, user_id) 
                VALUES ('test1', 'test_project', 'test_path1', 'user1')
            """)
            cursor.execute("""
                INSERT INTO projects (id, name, path, user_id) 
                VALUES ('test2', 'test_project', 'test_path2', 'user1')
            """)
            print("❌ テスト1失敗: 同じユーザーで同じプロジェクト名が作成できてしまいました")
        except sqlite3.IntegrityError:
            print("✅ テスト1成功: 同じユーザーで同じプロジェクト名は作成できません")
        
        # ロールバック
        conn.rollback()
        
        # テスト2: 異なるユーザーで同じプロジェクト名は作成できる
        try:
            cursor.execute("""
                INSERT INTO projects (id, name, path, user_id) 
                VALUES ('test3', 'test_project', 'test_path3', 'user1')
            """)
            cursor.execute("""
                INSERT INTO projects (id, name, path, user_id) 
                VALUES ('test4', 'test_project', 'test_path4', 'user2')
            """)
            print("✅ テスト2成功: 異なるユーザーで同じプロジェクト名が作成できます")
        except sqlite3.IntegrityError as e:
            print(f"❌ テスト2失敗: 異なるユーザーで同じプロジェクト名が作成できませんでした: {e}")
        
        # ロールバック
        conn.rollback()
        
        print("テスト完了!")
        
    except Exception as e:
        print(f"テストエラー: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("プロジェクト名制約マイグレーション")
    print("=" * 50)
    
    if migrate_database():
        test_migration()
        print("\n✅ マイグレーションが正常に完了しました!")
    else:
        print("\n❌ マイグレーションに失敗しました")
