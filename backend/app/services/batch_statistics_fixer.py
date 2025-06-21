"""
バッチ統計修正サービス

定期的に全プロジェクトの統計を検証し、
不一致があるタスクを一括修正するバッチシステムです。

機能:
- 定期的な全プロジェクト統計検証
- 一括修正処理
- 詳細なレポート生成
- 管理者向けダッシュボード
- 修正履歴の記録
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ..database import SessionLocal, Task, Result, TaskStatus, Project
from .universal_statistics_validator import universal_validator


class BatchStatisticsFixer:
    """バッチ統計修正サービス"""
    
    def __init__(self):
        self.name = "BatchStatisticsFixer"
        self.running = False
        self.thread = None
        self.batch_interval = 3600  # 1時間間隔
        self.last_batch_time = None
        self.fix_history = []
        
    def start_batch_processing(self):
        """バッチ処理を開始"""
        if self.running:
            print("⚠️ Batch statistics fixer is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._batch_loop, daemon=True)
        self.thread.start()
        print("✅ Batch statistics fixer started")
    
    def stop_batch_processing(self):
        """バッチ処理を停止"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🛑 Batch statistics fixer stopped")
    
    def _batch_loop(self):
        """バッチ処理ループ"""
        print("🔄 Batch statistics fixing loop started")
        
        while self.running:
            try:
                current_time = datetime.now()
                print(f"🔧 Starting batch statistics fix at {current_time.strftime('%H:%M:%S')}")
                
                batch_result = self.run_comprehensive_fix()
                self.last_batch_time = current_time
                
                # 修正履歴に記録
                self.fix_history.append({
                    "timestamp": current_time.isoformat(),
                    "result": batch_result
                })
                
                # 履歴は最新100件まで保持
                if len(self.fix_history) > 100:
                    self.fix_history = self.fix_history[-100:]
                
                print(f"✅ Batch fix completed: {batch_result['total_fixed']} tasks fixed")
                
                time.sleep(self.batch_interval)
                
            except Exception as e:
                print(f"❌ Batch fix error: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(300)  # エラー時は5分待機
    
    def run_comprehensive_fix(self) -> Dict[str, Any]:
        """包括的な統計修正を実行"""
        try:
            db = SessionLocal()
            try:
                # 全プロジェクトを取得
                projects = db.query(Project).all()
                
                # 最近7日間のタスクを対象
                cutoff_time = datetime.now() - timedelta(days=7)
                all_tasks = db.query(Task).filter(
                    Task.created_at >= cutoff_time
                ).all()
                
                total_tasks = len(all_tasks)
                total_fixed = 0
                project_stats = {}
                error_count = 0
                
                print(f"🔍 Comprehensive fix: {total_tasks} tasks across {len(projects)} projects")
                
                # プロジェクト別に処理
                for project in projects:
                    project_tasks = [t for t in all_tasks if t.project_id == project.id]
                    project_fixed = 0
                    
                    for task in project_tasks:
                        try:
                            result = universal_validator.validate_task_statistics(task.id)
                            if result.get("success") and result.get("fixed"):
                                project_fixed += 1
                                total_fixed += 1
                        except Exception as e:
                            error_count += 1
                            print(f"❌ Error fixing task {task.id[:8]}... in project {project.name}: {e}")
                    
                    if project_fixed > 0:
                        project_stats[project.name] = {
                            "project_id": project.id,
                            "total_tasks": len(project_tasks),
                            "fixed_tasks": project_fixed
                        }
                        print(f"📊 Project {project.name}: {project_fixed}/{len(project_tasks)} tasks fixed")
                
                return {
                    "total_tasks": total_tasks,
                    "total_fixed": total_fixed,
                    "total_projects": len(projects),
                    "project_stats": project_stats,
                    "error_count": error_count,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Error in comprehensive fix: {e}")
            return {
                "total_tasks": 0,
                "total_fixed": 0,
                "total_projects": 0,
                "project_stats": {},
                "error_count": 1,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def fix_specific_project(self, project_id: str) -> Dict[str, Any]:
        """特定のプロジェクトの統計を修正"""
        try:
            db = SessionLocal()
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    return {"success": False, "error": "Project not found"}
                
                # プロジェクトのタスクを取得（最近30日間）
                cutoff_time = datetime.now() - timedelta(days=30)
                tasks = db.query(Task).filter(
                    Task.project_id == project_id,
                    Task.created_at >= cutoff_time
                ).all()
                
                total_tasks = len(tasks)
                fixed_count = 0
                error_count = 0
                
                print(f"🔧 Fixing project {project.name}: {total_tasks} tasks")
                
                for task in tasks:
                    try:
                        result = universal_validator.validate_task_statistics(task.id)
                        if result.get("success") and result.get("fixed"):
                            fixed_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"❌ Error fixing task {task.id[:8]}...: {e}")
                
                return {
                    "success": True,
                    "project_id": project_id,
                    "project_name": project.name,
                    "total_tasks": total_tasks,
                    "fixed_count": fixed_count,
                    "error_count": error_count,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Error fixing project {project_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_fix_report(self, days: int = 7) -> Dict[str, Any]:
        """修正レポートを生成"""
        try:
            db = SessionLocal()
            try:
                cutoff_time = datetime.now() - timedelta(days=days)
                
                # 期間内のタスク統計
                total_tasks = db.query(Task).filter(
                    Task.created_at >= cutoff_time
                ).count()
                
                finished_tasks = db.query(Task).filter(
                    Task.created_at >= cutoff_time,
                    Task.status == TaskStatus.FINISHED
                ).count()
                
                # プロジェクト別統計
                projects = db.query(Project).all()
                project_stats = {}
                
                for project in projects:
                    project_tasks = db.query(Task).filter(
                        Task.project_id == project.id,
                        Task.created_at >= cutoff_time
                    ).count()
                    
                    if project_tasks > 0:
                        project_stats[project.name] = {
                            "project_id": project.id,
                            "total_tasks": project_tasks
                        }
                
                # 最近の修正履歴
                recent_fixes = [
                    fix for fix in self.fix_history
                    if datetime.fromisoformat(fix["timestamp"]) >= cutoff_time
                ]
                
                total_fixes = sum(fix["result"].get("total_fixed", 0) for fix in recent_fixes)
                
                return {
                    "period_days": days,
                    "total_tasks": total_tasks,
                    "finished_tasks": finished_tasks,
                    "total_fixes": total_fixes,
                    "project_stats": project_stats,
                    "recent_fixes": recent_fixes,
                    "last_batch_time": self.last_batch_time.isoformat() if self.last_batch_time else None,
                    "is_running": self.running,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Error generating fix report: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """バッチ修正サービスの状態を取得"""
        return {
            "running": self.running,
            "batch_interval": self.batch_interval,
            "last_batch_time": self.last_batch_time.isoformat() if self.last_batch_time else None,
            "fix_history_count": len(self.fix_history),
            "next_batch_in": self.batch_interval - (time.time() - self.last_batch_time.timestamp()) if self.last_batch_time else 0
        }


# グローバルインスタンス
batch_fixer = BatchStatisticsFixer()
