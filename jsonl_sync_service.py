#!/usr/bin/env python3
"""
JSONL形式対応のDB同期サービス
"""
import json
import sys
import os
import glob
from pathlib import Path
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')

from app.database import get_db, Result as DBResult, Task as DBTask
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

class JSONLSyncService:
    """JSONL形式の結果ファイルをDBに同期するサービス"""
    
    def __init__(self):
        self.scrapy_projects_dir = Path("/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects")
    
    def read_jsonl_file(self, file_path):
        """JSONLファイルを読み込み"""
        items = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:  # 空行をスキップ
                        try:
                            item = json.loads(line)
                            items.append(item)
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Line {line_num}: JSON decode error - {e}")
                            continue
            print(f"📊 JSONL読み込み完了: {len(items)}件")
            return items
        except Exception as e:
            print(f"❌ JSONLファイル読み込みエラー: {e}")
            return []
    
    def find_result_files(self, task_id=None):
        """結果ファイルを検索"""
        result_files = []
        
        # 全プロジェクトディレクトリを検索
        for project_dir in self.scrapy_projects_dir.iterdir():
            if project_dir.is_dir():
                # JSONLファイルを検索
                jsonl_pattern = str(project_dir / "*.jsonl")
                jsonl_files = glob.glob(jsonl_pattern)
                
                # JSONファイルも検索（後方互換性）
                json_pattern = str(project_dir / "results_*.json")
                json_files = glob.glob(json_pattern)
                
                for file_path in jsonl_files + json_files:
                    file_name = os.path.basename(file_path)
                    
                    # タスクIDが指定されている場合はフィルタリング
                    if task_id and task_id not in file_name:
                        continue
                    
                    result_files.append({
                        'path': file_path,
                        'name': file_name,
                        'project': project_dir.name,
                        'size': os.path.getsize(file_path),
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
                    })
        
        return result_files
    
    def sync_task_results(self, task_id):
        """指定されたタスクの結果をDBに同期"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            print(f"🔄 タスク {task_id} の結果同期開始...")
            
            # 結果ファイルを検索
            result_files = self.find_result_files(task_id)
            
            if not result_files:
                print(f"❌ タスク {task_id} の結果ファイルが見つかりません")
                return False
            
            # 最新のファイルを使用
            latest_file = max(result_files, key=lambda x: x['modified'])
            file_path = latest_file['path']
            
            print(f"📁 結果ファイル: {file_path}")
            print(f"📊 ファイルサイズ: {latest_file['size']} bytes")
            print(f"🕒 更新日時: {latest_file['modified']}")
            
            # ファイル形式に応じて読み込み
            if file_path.endswith('.jsonl'):
                items = self.read_jsonl_file(file_path)
            else:
                # JSONファイルの場合（後方互換性）
                items = self.read_json_file(file_path)
            
            if not items:
                print(f"❌ 有効なデータが見つかりません")
                return False
            
            # 既存の結果を削除
            existing_count = db.query(DBResult).filter(DBResult.task_id == task_id).count()
            if existing_count > 0:
                db.query(DBResult).filter(DBResult.task_id == task_id).delete()
                print(f"🗑️ 既存結果削除: {existing_count}件")
            
            # 新しい結果を追加
            added_count = 0
            for item in items:
                # 必要なフィールドがあることを確認
                if isinstance(item, dict) and ('url' in item or 'title' in item):
                    result = DBResult(
                        id=str(uuid.uuid4()),
                        task_id=task_id,
                        data=item,
                        created_at=datetime.now()
                    )
                    db.add(result)
                    added_count += 1
            
            # タスクの統計を更新
            task = db.query(DBTask).filter(DBTask.id == task_id).first()
            if task:
                task.items_count = added_count
                if task.status in ["RUNNING", "PENDING"]:
                    task.status = "FINISHED"
                if not task.finished_at:
                    task.finished_at = datetime.now()
                print(f"📊 タスク統計更新: {added_count}件")
            
            # コミット
            db.commit()
            print(f"✅ DB同期完了: {added_count}件の結果を追加")
            
            return True
            
        except Exception as e:
            print(f"❌ 同期エラー: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return False
        finally:
            db.close()
    
    def read_json_file(self, file_path):
        """JSONファイルを読み込み（後方互換性）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 正常なJSONとして読み込み試行
            try:
                items = json.loads(content)
                if isinstance(items, list):
                    return items
                else:
                    return [items]
            except json.JSONDecodeError:
                # 不正なJSONの場合は修復を試行
                print("⚠️ 不正なJSON形式を検出、修復を試行...")
                return self.fix_malformed_json(content)
        except Exception as e:
            print(f"❌ JSONファイル読み込みエラー: {e}")
            return []
    
    def fix_malformed_json(self, content):
        """不正なJSONを修復"""
        import re
        
        # JSONオブジェクトを抽出
        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(pattern, content)
        
        items = []
        for match in matches:
            try:
                obj = json.loads(match)
                items.append(obj)
            except json.JSONDecodeError:
                continue
        
        print(f"🔧 JSON修復完了: {len(items)}件のオブジェクトを抽出")
        return items
    
    def sync_all_pending_tasks(self):
        """すべての未同期タスクを同期"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # 実行中または完了したタスクで結果が未同期のものを検索
            tasks = db.query(DBTask).filter(
                DBTask.status.in_(["RUNNING", "FINISHED"]),
                DBTask.items_count > 0
            ).all()
            
            synced_count = 0
            for task in tasks:
                # 既存の結果数を確認
                existing_results = db.query(DBResult).filter(DBResult.task_id == task.id).count()
                
                if existing_results < task.items_count:
                    print(f"🔄 タスク {task.id} を同期中...")
                    if self.sync_task_results(task.id):
                        synced_count += 1
            
            print(f"✅ 一括同期完了: {synced_count}件のタスクを同期")
            return synced_count
            
        except Exception as e:
            print(f"❌ 一括同期エラー: {e}")
            return 0
        finally:
            db.close()

def main():
    """メイン実行関数"""
    import sys
    
    service = JSONLSyncService()
    
    if len(sys.argv) > 1:
        # 特定のタスクIDを同期
        task_id = sys.argv[1]
        print(f"🎯 特定タスク同期: {task_id}")
        success = service.sync_task_results(task_id)
        if success:
            print(f"🎉 タスク {task_id} の同期が完了しました！")
        else:
            print(f"❌ タスク {task_id} の同期に失敗しました")
    else:
        # 全タスクを同期
        print(f"🔄 全タスク同期開始...")
        synced_count = service.sync_all_pending_tasks()
        print(f"🎉 {synced_count}件のタスクを同期しました！")

if __name__ == "__main__":
    main()
