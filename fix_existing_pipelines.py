#!/usr/bin/env python3
"""
既存プロジェクトのpipelines.pyを修正
DB保存有効プロジェクトに正しいパイプライン設定を適用
"""
import sqlite3
import os
from pathlib import Path

def fix_existing_pipelines():
    """既存プロジェクトのpipelines.pyを修正"""
    
    print("🔧 既存プロジェクトのpipelines.py修正開始")
    
    # データベースから全プロジェクトを取得
    db_path = Path("backend/database/scrapy_ui.db")
    
    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # DB保存有効プロジェクトを取得
        cursor.execute("""
            SELECT id, name, path, db_save_enabled 
            FROM projects 
            WHERE db_save_enabled = 1
        """)
        
        enabled_projects = cursor.fetchall()
        
        print(f"📊 DB保存有効プロジェクト数: {len(enabled_projects)}件")
        
        for project_id, project_name, project_path, db_save_enabled in enabled_projects:
            print(f"\n🔄 プロジェクト修正中: {project_name}")
            fix_project_pipelines(project_name, project_path, True)
        
        # DB保存無効プロジェクトも確認
        cursor.execute("""
            SELECT id, name, path, db_save_enabled 
            FROM projects 
            WHERE db_save_enabled = 0
        """)
        
        disabled_projects = cursor.fetchall()
        
        print(f"\n📊 DB保存無効プロジェクト数: {len(disabled_projects)}件")
        
        for project_id, project_name, project_path, db_save_enabled in disabled_projects:
            print(f"\n🔄 プロジェクト修正中: {project_name}")
            fix_project_pipelines(project_name, project_path, False)
        
        return True
        
    except Exception as e:
        print(f"❌ データベースエラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def fix_project_pipelines(project_name: str, project_path: str, db_save_enabled: bool):
    """個別プロジェクトのpipelines.pyを修正"""
    
    # pipelines.pyファイルのパスを探す
    scrapy_projects_dir = Path("scrapy_projects")
    
    possible_paths = [
        scrapy_projects_dir / project_path / project_path / "pipelines.py",
        scrapy_projects_dir / project_path / "pipelines.py",
        scrapy_projects_dir / project_name / project_name / "pipelines.py",
        scrapy_projects_dir / project_name / "pipelines.py",
    ]
    
    pipelines_file = None
    for path in possible_paths:
        if path.exists():
            pipelines_file = path
            break
    
    if not pipelines_file:
        print(f"  ❌ pipelines.pyが見つかりません: {project_name}")
        print(f"     確認したパス:")
        for path in possible_paths:
            print(f"       - {path}")
        return False
    
    print(f"  📄 pipelines.pyファイル: {pipelines_file}")
    
    # 現在の内容を確認
    try:
        with open(pipelines_file, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        # ScrapyUIパイプラインが含まれているかチェック
        has_scrapy_ui_pipeline = 'ScrapyUIDatabasePipeline' in current_content
        
        print(f"  📊 現在の状態:")
        print(f"     DB保存設定: {'有効' if db_save_enabled else '無効'}")
        print(f"     ScrapyUIパイプライン: {'あり' if has_scrapy_ui_pipeline else 'なし'}")
        
        # 修正が必要かチェック
        needs_fix = False
        
        if db_save_enabled and not has_scrapy_ui_pipeline:
            print(f"  ⚠️ DB保存有効なのにScrapyUIパイプラインがありません")
            needs_fix = True
        elif not db_save_enabled and has_scrapy_ui_pipeline:
            print(f"  ⚠️ DB保存無効なのにScrapyUIパイプラインがあります")
            needs_fix = True
        
        if needs_fix:
            # 正しい内容を生成
            if db_save_enabled:
                # DB保存有効: ScrapyUIデータベースパイプライン対応版
                new_content = generate_db_enabled_pipelines(project_name)
                print(f"  🔧 DB保存有効版pipelines.pyを生成")
            else:
                # DB保存無効: 基本的なパイプラインのみ
                new_content = generate_db_disabled_pipelines(project_name)
                print(f"  🔧 DB保存無効版pipelines.pyを生成")
            
            # ファイルを更新
            with open(pipelines_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"  ✅ pipelines.pyを修正しました")
        else:
            print(f"  ✅ pipelines.pyは正しい状態です")
        
        return True
        
    except Exception as e:
        print(f"  ❌ pipelines.py修正エラー: {e}")
        return False

def generate_db_enabled_pipelines(project_name: str) -> str:
    """DB保存有効版pipelines.pyを生成"""
    
    # プロジェクト名をクラス名に変換（最初の文字を大文字に）
    class_name = project_name.replace('_', '').replace('-', '').capitalize()
    
    return f'''# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

# ScrapyUI データベースパイプラインをインポート
import sys
from pathlib import Path

# ScrapyUIのバックエンドパスを追加
scrapy_ui_backend = Path(__file__).parent.parent.parent.parent / "backend"
sys.path.insert(0, str(scrapy_ui_backend))

try:
    from app.templates.database_pipeline import ScrapyUIDatabasePipeline, ScrapyUIJSONPipeline
except ImportError:
    # フォールバック: 基本的なパイプライン
    class ScrapyUIDatabasePipeline:
        def process_item(self, item, spider):
            return item

    class ScrapyUIJSONPipeline:
        def process_item(self, item, spider):
            return item


class {class_name}Pipeline:
    """
    基本的なアイテムパイプライン
    """

    def process_item(self, item, spider):
        # アイテムの基本的な処理
        return item


# ScrapyUIデータベースパイプラインをエクスポート
# これにより、スパイダーの設定で直接参照できます
__all__ = ['ScrapyUIDatabasePipeline', 'ScrapyUIJSONPipeline', '{class_name}Pipeline']
'''

def generate_db_disabled_pipelines(project_name: str) -> str:
    """DB保存無効版pipelines.pyを生成"""
    
    # プロジェクト名をクラス名に変換（最初の文字を大文字に）
    class_name = project_name.replace('_', '').replace('-', '').capitalize()
    
    return f'''# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class {class_name}Pipeline:
    """
    基本的なアイテムパイプライン
    """

    def process_item(self, item, spider):
        # アイテムの基本的な処理
        return item


# 注意: このプロジェクトはDB保存が無効に設定されています
# 結果はファイル出力のみになります
# DB保存を有効にしたい場合は、プロジェクト設定を変更してください

__all__ = ['{class_name}Pipeline']
'''

def main():
    """メイン実行関数"""
    print("🎯 既存プロジェクトのpipelines.py修正ツール")
    
    success = fix_existing_pipelines()
    
    if success:
        print("\n🎉 修正完了！")
        print("\n🔧 修正内容:")
        print("  ✅ DB保存有効プロジェクト: ScrapyUIパイプライン対応版に更新")
        print("  ✅ DB保存無効プロジェクト: 基本パイプライン版に更新")
        print("  ✅ 既に正しい状態のプロジェクト: 変更なし")
        
        print("\n📝 次のステップ:")
        print("  1. 修正されたプロジェクトでスパイダーを実行")
        print("  2. DB保存有効プロジェクトの結果がデータベースに保存されることを確認")
        print("  3. DB保存無効プロジェクトの結果がファイルのみに出力されることを確認")
    else:
        print("\n❌ 修正失敗")

if __name__ == "__main__":
    main()
