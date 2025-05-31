"""
結果ファイル同期サービス
直接実行されたScrapyの結果をWebUIに反映させる
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from ..database import Task, Spider as DBSpider, Project as DBProject


class ResultSyncService:
    """結果ファイル同期サービス"""

    def __init__(self, base_projects_dir: str = "scrapy_projects"):
        self.base_projects_dir = Path(base_projects_dir)

    def scan_and_sync_results(self, db: Session) -> Dict:
        """全プロジェクトの結果ファイルをスキャンして同期"""
        results = {
            "scanned_projects": 0,
            "synced_tasks": 0,
            "synced_items": 0,
            "errors": []
        }

        try:
            # 全プロジェクトディレクトリをスキャン
            for project_dir in self.base_projects_dir.iterdir():
                if project_dir.is_dir():
                    results["scanned_projects"] += 1

                    # プロジェクトの結果ファイルを処理
                    sync_result = self._sync_project_results(db, project_dir)
                    results["synced_tasks"] += sync_result["synced_tasks"]
                    results["synced_items"] += sync_result["synced_items"]
                    results["errors"].extend(sync_result["errors"])

            print(f"✅ Result sync completed: {results}")
            return results

        except Exception as e:
            error_msg = f"Error in scan_and_sync_results: {str(e)}"
            results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return results

    def _sync_project_results(self, db: Session, project_dir: Path) -> Dict:
        """単一プロジェクトの結果ファイルを同期"""
        results = {
            "synced_tasks": 0,
            "synced_items": 0,
            "errors": []
        }

        try:
            # プロジェクト名からデータベースのプロジェクトを検索
            project_name = project_dir.name
            db_project = db.query(DBProject).filter(DBProject.path == project_name).first()

            if not db_project:
                # プロジェクト名の変換を試行 (admin_aiueo -> aiueo)
                if project_name.startswith('admin_'):
                    clean_name = project_name[6:]  # 'admin_'を除去
                    db_project = db.query(DBProject).filter(DBProject.name == clean_name).first()

                if not db_project:
                    return results

            print(f"🔍 Processing project: {project_name} -> {db_project.name}")

            # 結果ファイルを検索（JSONLとJSONの両方）
            jsonl_files = list(project_dir.glob("*.jsonl"))
            json_files = list(project_dir.glob("*.json"))
            json_files = [f for f in json_files if f.name not in ['scrapy.cfg']]
            result_files = jsonl_files + json_files

            for result_file in result_files:
                try:
                    sync_result = self._sync_result_file(db, db_project, result_file)
                    if sync_result:
                        results["synced_tasks"] += 1
                        results["synced_items"] += sync_result["items_count"]
                        print(f"✅ Synced: {result_file.name} ({sync_result['items_count']} items)")

                except Exception as e:
                    error_msg = f"Error syncing {result_file}: {str(e)}"
                    results["errors"].append(error_msg)
                    print(f"❌ {error_msg}")

            return results

        except Exception as e:
            error_msg = f"Error processing project {project_dir}: {str(e)}"
            results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return results

    def _sync_result_file(self, db: Session, project: DBProject, result_file: Path) -> Optional[Dict]:
        """結果ファイルをタスクとして同期"""
        try:
            # ファイル形式に応じて読み込み
            if result_file.suffix == '.jsonl':
                items = self._read_jsonl_file(result_file)
            else:
                items = self._read_json_file(result_file)

            if not items or len(items) == 0:
                return None

            # スパイダー名を推測
            spider_name = self._extract_spider_name(result_file.name, items)
            if not spider_name:
                return None

            # データベースからスパイダーを検索
            db_spider = db.query(DBSpider).filter(
                DBSpider.project_id == project.id,
                DBSpider.name == spider_name
            ).first()

            if not db_spider:
                print(f"⚠️ Spider not found: {spider_name} in project {project.name}")
                return None

            # 既存のタスクをチェック
            existing_task = db.query(Task).filter(
                Task.spider_id == db_spider.id,
                Task.items_count == len(items)
            ).first()

            if existing_task:
                print(f"📋 Task already exists for {spider_name} with {len(items)} items")
                return None

            # 日時情報を抽出
            start_time, end_time = self._extract_timestamps(items, result_file)

            # 新しいタスクを作成
            new_task = Task(
                id=str(uuid.uuid4()),
                spider_id=db_spider.id,
                project_id=project.id,
                spider_name=spider_name,
                status="COMPLETED",
                items_count=len(items),
                requests_count=len(items) + 2,  # 推定値
                started_at=start_time,
                finished_at=end_time,
                result_file=str(result_file),
                user_id=project.user_id
            )

            db.add(new_task)
            db.commit()

            return {
                "task_id": new_task.id,
                "items_count": len(items),
                "spider_name": spider_name
            }

        except Exception as e:
            db.rollback()
            raise e

    def _extract_spider_name(self, filename: str, items: List[Dict]) -> Optional[str]:
        """ファイル名またはアイテムからスパイダー名を抽出"""
        # ファイル名から推測
        if "omocha20" in filename.lower():
            return "omocha20"
        elif "software20" in filename.lower():
            return "software20"

        # 他のパターンも追加可能
        if "enhanced" in filename.lower() or "improved" in filename.lower():
            return "software20"  # 改善版も software20 として扱う

        # タスクIDが含まれている場合の推測
        if "results_" in filename.lower():
            # 最初のアイテムからスパイダー名を推測
            if items and len(items) > 0:
                first_item = items[0]
                if isinstance(first_item, dict):
                    # URLからスパイダー名を推測
                    url = first_item.get('url', '')
                    if 'amazon.co.jp' in url and 'software' in url:
                        return "omocha20"

        return None

    def _extract_timestamps(self, items: List[Dict], result_file: Path) -> Tuple[datetime, datetime]:
        """アイテムまたはファイルから日時情報を抽出"""
        try:
            # アイテムから日時情報を抽出
            if items and len(items) > 0:
                first_item = items[0]
                last_item = items[-1]

                # crawl_start_datetime を使用
                if "crawl_start_datetime" in first_item:
                    start_time = datetime.fromisoformat(first_item["crawl_start_datetime"])
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)
                else:
                    # ファイルの作成時刻を使用
                    file_time = datetime.fromtimestamp(result_file.stat().st_mtime, tz=timezone.utc)
                    start_time = file_time

                # item_acquired_datetime を使用
                if "item_acquired_datetime" in last_item:
                    end_time = datetime.fromisoformat(last_item["item_acquired_datetime"])
                    if end_time.tzinfo is None:
                        end_time = end_time.replace(tzinfo=timezone.utc)
                else:
                    # 開始時刻から推定
                    end_time = start_time

                return start_time, end_time

        except Exception as e:
            print(f"⚠️ Error extracting timestamps: {e}")

        # フォールバック: ファイルの作成時刻
        file_time = datetime.fromtimestamp(result_file.stat().st_mtime, tz=timezone.utc)
        return file_time, file_time

    def _read_jsonl_file(self, file_path: Path) -> List[Dict]:
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
                            print(f"⚠️ JSONL Line {line_num}: JSON decode error - {e}")
                            continue
            print(f"📊 JSONL読み込み完了: {len(items)}件 from {file_path.name}")
            return items
        except Exception as e:
            print(f"❌ JSONLファイル読み込みエラー: {e}")
            return []

    def _read_json_file(self, file_path: Path) -> List[Dict]:
        """JSONファイルを読み込み（後方互換性）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 正常なJSONとして読み込み試行
            try:
                items = json.loads(content)
                if isinstance(items, list):
                    print(f"📊 JSON読み込み完了: {len(items)}件 from {file_path.name}")
                    return items
                else:
                    print(f"📊 JSON読み込み完了: 1件 from {file_path.name}")
                    return [items]
            except json.JSONDecodeError:
                # 不正なJSONの場合は修復を試行
                print(f"⚠️ 不正なJSON形式を検出、修復を試行: {file_path.name}")
                return self._fix_malformed_json(content, file_path.name)
        except Exception as e:
            print(f"❌ JSONファイル読み込みエラー: {e}")
            return []

    def _fix_malformed_json(self, content: str, filename: str) -> List[Dict]:
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

        print(f"🔧 JSON修復完了: {len(items)}件のオブジェクトを抽出 from {filename}")
        return items


# サービスインスタンス
result_sync_service = ResultSyncService()
