#!/usr/bin/env python3
"""
ScrapyUI 包括的データ修復スクリプト
根本的なデータ整合性問題を解決します
"""

import os
import sys
import json
import mysql.connector
from pathlib import Path
from datetime import datetime, timedelta
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveDataRepair:
    def __init__(self):
        self.base_dir = Path("/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects")
        self.db_config = {
            'host': 'localhost',
            'user': 'scrapy_user',
            'password': 'ScrapyUser@2024#',
            'database': 'scrapy_ui'
        }
        self.stats = {
            'repaired_tasks': 0,
            'cleaned_files': 0,
            'synchronized_data': 0,
            'errors': []
        }

    def connect_db(self):
        """データベース接続"""
        return mysql.connector.connect(**self.db_config)

    def repair_item_counts(self):
        """アイテム数の修復"""
        logger.info("🔧 アイテム数の修復を開始...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            # アイテム数が0のFINISHEDタスクを取得
            cursor.execute("""
                SELECT t.id, t.spider_name, COUNT(r.id) as actual_count
                FROM tasks t
                LEFT JOIN results r ON t.id = r.task_id
                WHERE t.status = 'FINISHED' AND t.items_count = 0
                GROUP BY t.id, t.spider_name
                HAVING actual_count > 0
            """)
            
            tasks_to_repair = cursor.fetchall()
            logger.info(f"📊 修復対象タスク: {len(tasks_to_repair)}件")
            
            for task_id, spider_name, actual_count in tasks_to_repair:
                # タスクのアイテム数を更新
                cursor.execute("""
                    UPDATE tasks 
                    SET items_count = %s 
                    WHERE id = %s
                """, (actual_count, task_id))
                
                self.stats['repaired_tasks'] += 1
                logger.info(f"✅ {task_id}: {actual_count}件に修復")
            
            conn.commit()
            logger.info(f"🎉 アイテム数修復完了: {self.stats['repaired_tasks']}件")
            
        except Exception as e:
            logger.error(f"❌ アイテム数修復エラー: {e}")
            self.stats['errors'].append(f"Item count repair: {e}")
        finally:
            conn.close()

    def synchronize_file_data(self):
        """ファイルとデータベースの同期"""
        logger.info("🔄 ファイル・データベース同期を開始...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            # 結果ファイルを検索
            result_files = list(self.base_dir.glob("**/results_*.jsonl"))
            logger.info(f"📁 検出ファイル: {len(result_files)}件")
            
            for file_path in result_files:
                try:
                    # ファイル名からタスクIDを抽出
                    task_id = file_path.stem.replace("results_", "")
                    
                    # ファイル内のアイテム数をカウント
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_items = sum(1 for line in f if line.strip())
                    
                    # データベース内のアイテム数を確認
                    cursor.execute("SELECT items_count FROM tasks WHERE id = %s", (task_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        db_items = result[0]
                        if db_items != file_items:
                            # 不整合を修正
                            cursor.execute("""
                                UPDATE tasks 
                                SET items_count = %s 
                                WHERE id = %s
                            """, (file_items, task_id))
                            
                            self.stats['synchronized_data'] += 1
                            logger.info(f"🔧 {task_id}: {db_items} → {file_items}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ ファイル処理エラー {file_path}: {e}")
            
            conn.commit()
            logger.info(f"✅ 同期完了: {self.stats['synchronized_data']}件")
            
        except Exception as e:
            logger.error(f"❌ 同期エラー: {e}")
            self.stats['errors'].append(f"File sync: {e}")
        finally:
            conn.close()

    def cleanup_orphaned_files(self):
        """孤立ファイルのクリーンアップ"""
        logger.info("🧹 孤立ファイルのクリーンアップを開始...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            # 全タスクIDを取得
            cursor.execute("SELECT id FROM tasks")
            valid_task_ids = {row[0] for row in cursor.fetchall()}
            
            # 結果ファイルをチェック
            result_files = list(self.base_dir.glob("**/results_*.jsonl"))
            
            for file_path in result_files:
                try:
                    task_id = file_path.stem.replace("results_", "")
                    
                    if task_id not in valid_task_ids:
                        # 孤立ファイルを削除
                        file_path.unlink()
                        self.stats['cleaned_files'] += 1
                        logger.info(f"🗑️ 削除: {file_path.name}")
                
                except Exception as e:
                    logger.warning(f"⚠️ ファイル削除エラー {file_path}: {e}")
            
            logger.info(f"✅ クリーンアップ完了: {self.stats['cleaned_files']}件削除")
            
        except Exception as e:
            logger.error(f"❌ クリーンアップエラー: {e}")
            self.stats['errors'].append(f"File cleanup: {e}")
        finally:
            conn.close()

    def optimize_database(self):
        """データベース最適化"""
        logger.info("⚡ データベース最適化を開始...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            # インデックス最適化
            cursor.execute("OPTIMIZE TABLE tasks")
            cursor.execute("OPTIMIZE TABLE results")
            cursor.execute("OPTIMIZE TABLE projects")
            cursor.execute("OPTIMIZE TABLE spiders")
            
            logger.info("✅ データベース最適化完了")
            
        except Exception as e:
            logger.error(f"❌ 最適化エラー: {e}")
            self.stats['errors'].append(f"DB optimization: {e}")
        finally:
            conn.close()

    def generate_report(self):
        """修復レポート生成"""
        logger.info("📋 修復レポートを生成...")
        
        report = f"""
🔧 ScrapyUI データ修復レポート
{'='*50}
実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 修復結果:
- 修復されたタスク: {self.stats['repaired_tasks']}件
- 同期されたデータ: {self.stats['synchronized_data']}件  
- 削除されたファイル: {self.stats['cleaned_files']}件

❌ エラー: {len(self.stats['errors'])}件
{chr(10).join(f'  - {error}' for error in self.stats['errors'])}

✅ 修復完了
"""
        
        # レポートファイルに保存
        report_file = Path("data_repair_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        logger.info(f"📄 レポート保存: {report_file}")

    def run_comprehensive_repair(self):
        """包括的修復の実行"""
        logger.info("🚀 包括的データ修復を開始...")
        start_time = datetime.now()
        
        try:
            # Phase 1: アイテム数修復
            self.repair_item_counts()
            
            # Phase 2: ファイル・DB同期
            self.synchronize_file_data()
            
            # Phase 3: 孤立ファイル削除
            self.cleanup_orphaned_files()
            
            # Phase 4: DB最適化
            self.optimize_database()
            
            # Phase 5: レポート生成
            self.generate_report()
            
            duration = datetime.now() - start_time
            logger.info(f"🎉 包括的修復完了 (所要時間: {duration})")
            
        except Exception as e:
            logger.error(f"❌ 包括的修復エラー: {e}")
            raise

if __name__ == "__main__":
    repair = ComprehensiveDataRepair()
    repair.run_comprehensive_repair()
