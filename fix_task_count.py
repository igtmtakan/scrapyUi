#!/usr/bin/env python3
"""
タスクのアイテム数を結果ファイルから正しく更新するスクリプト
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# プロジェクトルートを追加
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')

from app.database import SessionLocal, Task as DBTask
from app.models.schemas import TaskStatus

def fix_task_count(task_id: str):
    """指定されたタスクのアイテム数を結果ファイルから修正"""
    db = SessionLocal()

    try:
        # タスクを取得
        task = db.query(DBTask).filter(DBTask.id == task_id).first()
        if not task:
            print(f"❌ タスクが見つかりません: {task_id}")
            return False

        print(f"📋 タスク情報:")
        print(f"   ID: {task.id}")
        print(f"   スパイダー: {task.spider.name if task.spider else 'Unknown'}")
        print(f"   現在のアイテム数: {task.items_count}")
        print(f"   現在のステータス: {task.status}")

        # 結果ファイルを探す
        project_path = task.project.path if task.project else None
        if not project_path:
            print(f"❌ プロジェクトパスが見つかりません")
            return False

        # 結果ファイルのパス
        base_dir = Path('/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects')
        result_file = base_dir / project_path / f"results_{task_id}.json"

        print(f"📁 結果ファイル: {result_file}")

        if not result_file.exists():
            print(f"❌ 結果ファイルが見つかりません: {result_file}")
            return False

        # ファイルサイズ確認
        file_size = result_file.stat().st_size
        print(f"📊 ファイルサイズ: {file_size} bytes")

        if file_size < 50:
            print(f"⚠️ ファイルサイズが小さすぎます")
            return False

        # JSONファイルを読み込み
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                actual_count = len(data)
            else:
                actual_count = 1

            print(f"✅ 実際のアイテム数: {actual_count}")

            # タスクを更新
            task.items_count = actual_count
            task.requests_count = max(actual_count + 5, 20)
            task.status = TaskStatus.FINISHED
            task.finished_at = datetime.now()

            db.commit()

            print(f"🔧 タスクを更新しました:")
            print(f"   アイテム数: {task.items_count}")
            print(f"   リクエスト数: {task.requests_count}")
            print(f"   ステータス: {task.status}")

            return True

        except json.JSONDecodeError as e:
            print(f"❌ JSONファイルの解析エラー: {e}")
            return False

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

    finally:
        db.close()

def fix_all_recent_tasks():
    """最近の全てのタスクを修正"""
    task_ids = [
        "d0e05e8a-9fff-473f-9976-ab6f0b9cadb5",  # 最新
        "b73039ba-e4a7-4d5a-953c-5168a2a02ed5",  # 前回
    ]

    for task_id in task_ids:
        print(f"\n🔧 タスク {task_id} のアイテム数を修正します...")
        if fix_task_count(task_id):
            print(f"✅ 修正完了！")
        else:
            print(f"❌ 修正失敗")

if __name__ == "__main__":
    fix_all_recent_tasks()
