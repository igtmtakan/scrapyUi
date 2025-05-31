#!/usr/bin/env python3
"""
ファイルシステムからデータベースへの同期ツール
pipelines.pyなどのプロジェクトファイルをファイルシステムからデータベースに同期
"""
import sqlite3
import os
from pathlib import Path
import uuid
from datetime import datetime

def sync_files_to_database():
    """ファイルシステムからデータベースにファイルを同期"""
    
    print("🔄 ファイルシステム → データベース同期開始")
    
    # データベース接続
    db_path = Path("backend/database/scrapy_ui.db")
    
    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 全プロジェクトを取得
        cursor.execute("SELECT id, name, path, user_id FROM projects")
        projects = cursor.fetchall()
        
        print(f"📊 プロジェクト数: {len(projects)}件")
        
        total_synced = 0
        
        for project_id, project_name, project_path, user_id in projects:
            print(f"\n🔄 プロジェクト同期中: {project_name}")
            synced_count = sync_project_files(cursor, project_id, project_name, project_path, user_id)
            total_synced += synced_count
            print(f"  ✅ {synced_count}件のファイルを同期")
        
        conn.commit()
        print(f"\n🎉 同期完了: 合計{total_synced}件のファイルを同期しました")
        
        return True
        
    except Exception as e:
        print(f"❌ データベースエラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def sync_project_files(cursor, project_id: str, project_name: str, project_path: str, user_id: str):
    """個別プロジェクトのファイルを同期"""
    
    # プロジェクトディレクトリを探す
    scrapy_projects_dir = Path("scrapy_projects")
    
    possible_project_dirs = [
        scrapy_projects_dir / project_path,
        scrapy_projects_dir / project_name,
    ]
    
    project_dir = None
    for dir_path in possible_project_dirs:
        if dir_path.exists():
            project_dir = dir_path
            break
    
    if not project_dir:
        print(f"  ❌ プロジェクトディレクトリが見つかりません: {project_name}")
        return 0
    
    print(f"  📁 プロジェクトディレクトリ: {project_dir}")
    
    # 同期対象ファイルを検索
    target_files = [
        "pipelines.py",
        "settings.py", 
        "items.py",
        "middlewares.py",
        "scrapy.cfg"
    ]
    
    synced_count = 0
    
    # プロジェクト内のファイルを再帰的に検索
    for file_pattern in target_files:
        found_files = list(project_dir.rglob(file_pattern))
        
        for file_path in found_files:
            try:
                # ファイル内容を読み込み
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # プロジェクトディレクトリからの相対パス
                relative_path = file_path.relative_to(project_dir)
                relative_path_str = str(relative_path).replace('\\', '/')
                
                # データベースに既存のファイルがあるかチェック
                cursor.execute("""
                    SELECT id, content FROM project_files 
                    WHERE project_id = ? AND path = ?
                """, (project_id, relative_path_str))
                
                existing_file = cursor.fetchone()
                
                if existing_file:
                    existing_id, existing_content = existing_file
                    
                    # 内容が異なる場合のみ更新
                    if existing_content != content:
                        cursor.execute("""
                            UPDATE project_files 
                            SET content = ?, updated_at = ?
                            WHERE id = ?
                        """, (content, datetime.now().isoformat(), existing_id))
                        
                        print(f"    🔄 更新: {relative_path_str}")
                        synced_count += 1
                    else:
                        print(f"    ✅ 同期済み: {relative_path_str}")
                else:
                    # 新しいファイルを追加
                    file_id = str(uuid.uuid4())
                    file_type = "python" if file_path.suffix == '.py' else "config"
                    
                    cursor.execute("""
                        INSERT INTO project_files 
                        (id, name, path, content, file_type, project_id, user_id, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        file_id,
                        file_path.name,
                        relative_path_str,
                        content,
                        file_type,
                        project_id,
                        user_id,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    
                    print(f"    ➕ 追加: {relative_path_str}")
                    synced_count += 1
                
            except Exception as e:
                print(f"    ❌ ファイル同期エラー {file_path}: {e}")
    
    return synced_count

def verify_sync():
    """同期結果を確認"""
    
    print("\n🔍 同期結果確認")
    
    db_path = Path("backend/database/scrapy_ui.db")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # pipelines.pyファイルの確認
        cursor.execute("""
            SELECT p.name as project_name, pf.path, 
                   CASE WHEN pf.content LIKE '%ScrapyUIDatabasePipeline%' THEN 'DB対応' ELSE '基本' END as pipeline_type,
                   p.db_save_enabled
            FROM project_files pf
            JOIN projects p ON pf.project_id = p.id
            WHERE pf.path LIKE '%pipelines.py'
            ORDER BY p.name
        """)
        
        results = cursor.fetchall()
        
        print(f"\n📊 pipelines.pyファイル確認結果:")
        print(f"{'プロジェクト名':<30} {'パイプライン種類':<10} {'DB保存設定':<10} {'一致':<6}")
        print("-" * 70)
        
        for project_name, path, pipeline_type, db_save_enabled in results:
            db_setting = "有効" if db_save_enabled else "無効"
            expected_type = "DB対応" if db_save_enabled else "基本"
            match = "✅" if pipeline_type == expected_type else "❌"
            
            print(f"{project_name:<30} {pipeline_type:<10} {db_setting:<10} {match:<6}")
        
        # 統計情報
        cursor.execute("SELECT COUNT(*) FROM project_files WHERE path LIKE '%pipelines.py'")
        pipelines_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM project_files")
        total_files = cursor.fetchone()[0]
        
        print(f"\n📈 統計:")
        print(f"  pipelines.pyファイル数: {pipelines_count}")
        print(f"  総ファイル数: {total_files}")
        
        return True
        
    except Exception as e:
        print(f"❌ 確認エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """メイン実行関数"""
    print("🎯 ファイルシステム → データベース同期ツール")
    
    # 同期実行
    success = sync_files_to_database()
    
    if success:
        # 結果確認
        verify_sync()
        
        print("\n🎉 同期完了！")
        print("\n🔧 実行内容:")
        print("  ✅ ファイルシステムの最新内容をデータベースに同期")
        print("  ✅ pipelines.pyの内容を正しく反映")
        print("  ✅ WebUIで正しい内容が表示されるようになります")
        
        print("\n📝 次のステップ:")
        print("  1. WebUIでpipelines.pyの内容を確認")
        print("  2. DB保存有効プロジェクトでScrapyUIパイプラインが表示されることを確認")
        print("  3. DB保存無効プロジェクトで基本パイプラインのみが表示されることを確認")
    else:
        print("\n❌ 同期失敗")

if __name__ == "__main__":
    main()
