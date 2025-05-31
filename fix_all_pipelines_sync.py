#!/usr/bin/env python3
"""
全プロジェクトのpipelines.pyを強制的にファイルシステムからデータベースに同期
"""
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

def fix_all_pipelines_sync():
    """全プロジェクトのpipelines.pyを強制同期"""
    
    print("🔄 全プロジェクトのpipelines.py強制同期開始\n")
    
    # データベース接続
    db_path = Path("backend/database/scrapy_ui.db")
    
    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 全プロジェクトを取得
        cursor.execute("SELECT id, name, path, user_id, db_save_enabled FROM projects")
        projects = cursor.fetchall()
        
        print(f"📊 プロジェクト数: {len(projects)}件")
        
        success_count = 0
        error_count = 0
        
        for project_id, project_name, project_path, user_id, db_save_enabled in projects:
            print(f"\n🔄 プロジェクト同期中: {project_name}")
            print(f"   ID: {project_id}")
            print(f"   パス: {project_path}")
            print(f"   DB保存設定: {'有効' if db_save_enabled else '無効'}")
            
            try:
                success = force_sync_single_project(cursor, project_id, project_name, project_path, user_id, db_save_enabled)
                if success:
                    success_count += 1
                    print(f"   ✅ 同期成功")
                else:
                    error_count += 1
                    print(f"   ❌ 同期失敗")
            except Exception as e:
                error_count += 1
                print(f"   ❌ 同期エラー: {e}")
        
        conn.commit()
        
        print(f"\n🎉 同期完了!")
        print(f"   成功: {success_count}件")
        print(f"   失敗: {error_count}件")
        print(f"   合計: {len(projects)}件")
        
        return True
        
    except Exception as e:
        print(f"❌ データベースエラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def force_sync_single_project(cursor, project_id: str, project_name: str, project_path: str, user_id: str, db_save_enabled: bool):
    """単一プロジェクトのpipelines.pyを強制同期"""
    
    # ファイルシステムからpipelines.pyを探す
    scrapy_projects_dir = Path("scrapy_projects")
    
    possible_paths = [
        scrapy_projects_dir / project_path / project_path / "pipelines.py",
        scrapy_projects_dir / project_path / "pipelines.py",
    ]
    
    actual_pipelines_file = None
    for path in possible_paths:
        if path.exists():
            actual_pipelines_file = path
            print(f"     📄 ファイル発見: {path}")
            break
    
    if not actual_pipelines_file:
        print(f"     ❌ pipelines.pyファイルが見つかりません")
        return False
    
    try:
        # ファイル内容を読み取り
        with open(actual_pipelines_file, 'r', encoding='utf-8') as f:
            pipelines_content = f.read()
        
        print(f"     📊 ファイルサイズ: {len(pipelines_content)}文字")
        
        # 内容を検証
        has_scrapy_ui_pipeline = 'ScrapyUIDatabasePipeline' in pipelines_content
        expected_has_pipeline = db_save_enabled
        
        print(f"     🔍 ScrapyUIパイプライン: {'あり' if has_scrapy_ui_pipeline else 'なし'}")
        print(f"     🔍 期待値: {'あり' if expected_has_pipeline else 'なし'}")
        
        if has_scrapy_ui_pipeline == expected_has_pipeline:
            print(f"     ✅ 内容が設定と一致")
        else:
            print(f"     ⚠️ 内容が設定と不一致")
        
        # データベースから既存のpipelines.pyを削除
        cursor.execute("""
            DELETE FROM project_files 
            WHERE project_id = ? AND name = 'pipelines.py'
        """, (project_id,))
        
        deleted_count = cursor.rowcount
        if deleted_count > 0:
            print(f"     🗑️ 既存ファイル削除: {deleted_count}件")
        
        # 新しいファイルを作成
        file_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO project_files 
            (id, name, path, content, file_type, project_id, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id,
            "pipelines.py",
            "pipelines.py",
            pipelines_content,
            "python",
            project_id,
            user_id,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        print(f"     ➕ 新しいファイル追加")
        
        # 検証
        cursor.execute("""
            SELECT content FROM project_files 
            WHERE project_id = ? AND name = 'pipelines.py'
        """, (project_id,))
        
        result = cursor.fetchone()
        if result:
            db_content = result[0]
            db_has_scrapy_ui = 'ScrapyUIDatabasePipeline' in db_content
            print(f"     ✅ データベース検証: ScrapyUIパイプライン={'あり' if db_has_scrapy_ui else 'なし'}")
            print(f"     ✅ データベースサイズ: {len(db_content)}文字")
            
            return db_has_scrapy_ui == expected_has_pipeline
        else:
            print(f"     ❌ データベース検証失敗")
            return False
        
    except Exception as e:
        print(f"     ❌ ファイル処理エラー: {e}")
        return False

def verify_sync_results():
    """同期結果を検証"""
    
    print("\n🔍 同期結果検証")
    
    db_path = Path("backend/database/scrapy_ui.db")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # pipelines.pyファイルの統計
        cursor.execute("""
            SELECT 
                p.name as project_name,
                p.db_save_enabled,
                CASE WHEN pf.content LIKE '%ScrapyUIDatabasePipeline%' THEN 1 ELSE 0 END as has_scrapy_ui,
                length(pf.content) as content_length
            FROM projects p
            LEFT JOIN project_files pf ON p.id = pf.project_id AND pf.name = 'pipelines.py'
            ORDER BY p.name
        """)
        
        results = cursor.fetchall()
        
        print(f"\n📊 pipelines.py同期結果:")
        print(f"{'プロジェクト名':<30} {'DB保存':<8} {'ScrapyUI':<10} {'サイズ':<8} {'状態':<6}")
        print("-" * 70)
        
        correct_count = 0
        total_count = 0
        
        for project_name, db_save_enabled, has_scrapy_ui, content_length in results:
            db_setting = "有効" if db_save_enabled else "無効"
            scrapy_ui_status = "あり" if has_scrapy_ui else "なし"
            size_str = f"{content_length}文字" if content_length else "なし"
            
            # 正しい状態かチェック
            is_correct = (db_save_enabled and has_scrapy_ui) or (not db_save_enabled and not has_scrapy_ui)
            status = "✅" if is_correct else "❌"
            
            if is_correct:
                correct_count += 1
            total_count += 1
            
            print(f"{project_name:<30} {db_setting:<8} {scrapy_ui_status:<10} {size_str:<8} {status:<6}")
        
        print("-" * 70)
        print(f"正しい状態: {correct_count}/{total_count}件 ({correct_count/total_count*100:.1f}%)")
        
        conn.close()
        
        return correct_count == total_count
        
    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        return False

def main():
    """メイン実行関数"""
    print("🎯 全プロジェクトのpipelines.py強制同期ツール")
    
    # 強制同期実行
    success = fix_all_pipelines_sync()
    
    if success:
        # 結果検証
        all_correct = verify_sync_results()
        
        print("\n🎉 強制同期完了！")
        
        if all_correct:
            print("\n✅ 全プロジェクトが正しい状態です")
        else:
            print("\n⚠️ 一部のプロジェクトに問題があります")
        
        print("\n🔧 実行内容:")
        print("  ✅ ファイルシステムからpipelines.pyを読み取り")
        print("  ✅ データベースの既存ファイルを削除")
        print("  ✅ 正しい内容でデータベースに新規作成")
        print("  ✅ DB保存設定との一致を検証")
        
        print("\n🌐 WebUI確認:")
        print("  1. http://localhost:4000 にアクセス")
        print("  2. 任意のプロジェクトを選択")
        print("  3. pipelines.pyファイルを開く")
        print("  4. DB保存設定に応じた正しい内容が表示されることを確認")
        
        print("\n📝 期待される結果:")
        print("  - DB保存有効: ScrapyUIDatabasePipeline、ScrapyUIJSONPipelineが含まれる")
        print("  - DB保存無効: 基本的なパイプラインのみが含まれる")
    else:
        print("\n❌ 強制同期失敗")

if __name__ == "__main__":
    main()
