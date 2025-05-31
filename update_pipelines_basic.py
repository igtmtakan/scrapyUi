#!/usr/bin/env python3
"""
全プロジェクトのpipelines.pyを基本フォーマットに更新
"""
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

def update_all_pipelines_to_basic():
    """全プロジェクトのpipelines.pyを基本フォーマットに更新"""
    
    print("🔄 全プロジェクトのpipelines.py基本フォーマット更新開始\n")
    
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
        
        success_count = 0
        error_count = 0
        
        for project_id, project_name, project_path, user_id in projects:
            print(f"\n🔄 プロジェクト更新中: {project_name}")
            print(f"   ID: {project_id}")
            print(f"   パス: {project_path}")
            
            try:
                success = update_single_project_pipeline(cursor, project_id, project_name, project_path, user_id)
                if success:
                    success_count += 1
                    print(f"   ✅ 更新成功")
                else:
                    error_count += 1
                    print(f"   ❌ 更新失敗")
            except Exception as e:
                error_count += 1
                print(f"   ❌ 更新エラー: {e}")
        
        conn.commit()
        
        print(f"\n🎉 更新完了!")
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

def update_single_project_pipeline(cursor, project_id: str, project_name: str, project_path: str, user_id: str):
    """単一プロジェクトのpipelines.pyを基本フォーマットに更新"""
    
    try:
        # プロジェクト名からクラス名を生成（最初の文字を大文字に）
        class_name = project_name.replace('_', ' ').title().replace(' ', '')
        if not class_name.endswith('Pipeline'):
            class_name += 'Pipeline'
        
        # 基本フォーマットのpipelines.py内容を生成
        basic_pipelines_content = f'''# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class {class_name}:
    def process_item(self, item, spider):
        return item
'''
        
        print(f"     📝 基本フォーマット生成: {len(basic_pipelines_content)}文字")
        print(f"     📝 クラス名: {class_name}")
        
        # ファイルシステムも更新
        update_filesystem_pipeline(project_path, basic_pipelines_content)
        
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
            basic_pipelines_content,
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
            print(f"     ✅ データベース検証: {len(db_content)}文字")
            
            # 基本フォーマットかチェック
            is_basic = 'ScrapyUIDatabasePipeline' not in db_content and 'def process_item' in db_content
            print(f"     ✅ 基本フォーマット: {'はい' if is_basic else 'いいえ'}")
            
            return is_basic
        else:
            print(f"     ❌ データベース検証失敗")
            return False
        
    except Exception as e:
        print(f"     ❌ ファイル処理エラー: {e}")
        return False

def update_filesystem_pipeline(project_path: str, pipelines_content: str):
    """ファイルシステムのpipelines.pyも更新"""
    
    try:
        scrapy_projects_dir = Path("scrapy_projects")
        
        # 可能なパスパターンを試す
        possible_paths = [
            scrapy_projects_dir / project_path / project_path / "pipelines.py",
            scrapy_projects_dir / project_path / "pipelines.py",
        ]
        
        updated_files = []
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(pipelines_content)
                    updated_files.append(str(path))
                    print(f"     📄 ファイルシステム更新: {path}")
                except Exception as e:
                    print(f"     ⚠️ ファイルシステム更新失敗: {path} - {e}")
        
        if not updated_files:
            print(f"     ⚠️ ファイルシステムにpipelines.pyが見つかりません")
        
    except Exception as e:
        print(f"     ⚠️ ファイルシステム更新エラー: {e}")

def verify_basic_format_results():
    """基本フォーマット更新結果を検証"""
    
    print("\n🔍 基本フォーマット更新結果検証")
    
    db_path = Path("backend/database/scrapy_ui.db")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # pipelines.pyファイルの統計
        cursor.execute("""
            SELECT 
                p.name as project_name,
                CASE WHEN pf.content LIKE '%ScrapyUIDatabasePipeline%' THEN 1 ELSE 0 END as has_scrapy_ui,
                CASE WHEN pf.content LIKE '%def process_item%' THEN 1 ELSE 0 END as has_process_item,
                length(pf.content) as content_length
            FROM projects p
            LEFT JOIN project_files pf ON p.id = pf.project_id AND pf.name = 'pipelines.py'
            ORDER BY p.name
        """)
        
        results = cursor.fetchall()
        
        print(f"\n📊 pipelines.py基本フォーマット結果:")
        print(f"{'プロジェクト名':<30} {'ScrapyUI':<10} {'process_item':<12} {'サイズ':<8} {'状態':<6}")
        print("-" * 75)
        
        basic_count = 0
        total_count = 0
        
        for project_name, has_scrapy_ui, has_process_item, content_length in results:
            scrapy_ui_status = "あり" if has_scrapy_ui else "なし"
            process_item_status = "あり" if has_process_item else "なし"
            size_str = f"{content_length}文字" if content_length else "なし"
            
            # 基本フォーマットかチェック
            is_basic = not has_scrapy_ui and has_process_item
            status = "✅" if is_basic else "❌"
            
            if is_basic:
                basic_count += 1
            total_count += 1
            
            print(f"{project_name:<30} {scrapy_ui_status:<10} {process_item_status:<12} {size_str:<8} {status:<6}")
        
        print("-" * 75)
        print(f"基本フォーマット: {basic_count}/{total_count}件 ({basic_count/total_count*100:.1f}%)")
        
        conn.close()
        
        return basic_count == total_count
        
    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        return False

def main():
    """メイン実行関数"""
    print("🎯 全プロジェクトのpipelines.py基本フォーマット更新ツール")
    
    # 基本フォーマット更新実行
    success = update_all_pipelines_to_basic()
    
    if success:
        # 結果検証
        all_basic = verify_basic_format_results()
        
        print("\n🎉 基本フォーマット更新完了！")
        
        if all_basic:
            print("\n✅ 全プロジェクトが基本フォーマットです")
        else:
            print("\n⚠️ 一部のプロジェクトに問題があります")
        
        print("\n🔧 実行内容:")
        print("  ✅ ScrapyUIパイプライン関連コードを削除")
        print("  ✅ 基本的なprocess_itemメソッドのみに簡素化")
        print("  ✅ ファイルシステムとデータベースの両方を更新")
        print("  ✅ クラス名をプロジェクト名に基づいて生成")
        
        print("\n🌐 WebUI確認:")
        print("  1. http://localhost:4000 にアクセス")
        print("  2. 任意のプロジェクトを選択")
        print("  3. pipelines.pyファイルを開く")
        print("  4. シンプルな基本フォーマットが表示されることを確認")
        
        print("\n📝 期待される結果:")
        print("  - ScrapyUIパイプライン関連コードなし")
        print("  - 基本的なprocess_itemメソッドのみ")
        print("  - シンプルで理解しやすい構造")
    else:
        print("\n❌ 基本フォーマット更新失敗")

if __name__ == "__main__":
    main()
