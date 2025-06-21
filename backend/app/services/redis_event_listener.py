"""
Redis Event Listener Service
spider-managerからのRedisイベントを受信してタスクステータスを更新
"""

import asyncio
import json
import redis.asyncio as redis
from datetime import datetime, timezone
from typing import Dict, Any
import logging

from ..database import SessionLocal, Task, TaskStatus
from ..config.database_config import get_database_config

logger = logging.getLogger(__name__)


class RedisEventListener:
    """Redisイベントリスナーサービス"""
    
    def __init__(self):
        self.redis_client = None
        self.running = False
        self.subscriptions = [
            "events:spider_started",
            "events:spider_finished", 
            "events:spider_completed",
            "events:spider_progress",
            "events:results_processed"
        ]
    
    async def start(self):
        """イベントリスナーを開始"""
        if self.running:
            logger.warning("Redis event listener is already running")
            return
            
        try:
            # Redis接続を確立
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True
            )
            
            # 接続テスト
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")
            
            self.running = True
            
            # イベント購読を開始
            await self._subscribe_to_events()
            
        except Exception as e:
            logger.error(f"❌ Failed to start Redis event listener: {e}")
            raise
    
    async def stop(self):
        """イベントリスナーを停止"""
        self.running = False
        if self.redis_client:
            await self.redis_client.close()
        logger.info("🛑 Redis event listener stopped")
    
    async def _subscribe_to_events(self):
        """イベント購読処理"""
        try:
            pubsub = self.redis_client.pubsub()
            
            # チャンネルを購読
            for channel in self.subscriptions:
                await pubsub.subscribe(channel)
                logger.info(f"📡 Subscribed to channel: {channel}")
            
            logger.info("🔄 Redis event listener started")
            
            # メッセージ受信ループ
            async for message in pubsub.listen():
                if not self.running:
                    break
                    
                if message['type'] == 'message':
                    await self._handle_message(message['channel'], message['data'])
                    
        except Exception as e:
            logger.error(f"❌ Error in event subscription: {e}")
        finally:
            if pubsub:
                await pubsub.close()
    
    async def _handle_message(self, channel: str, data: str):
        """メッセージ処理"""
        try:
            event_data = json.loads(data)
            task_id = event_data.get('task_id')
            
            if not task_id:
                logger.warning(f"⚠️ No task_id in event: {channel}")
                return
            
            logger.info(f"📥 Received event: {channel} for task {task_id[:8]}...")
            
            # チャンネル別処理
            if channel == "events:spider_started":
                await self._handle_spider_started(event_data)
            elif channel == "events:spider_finished":
                await self._handle_spider_finished(event_data)
            elif channel == "events:spider_completed":
                await self._handle_spider_completed(event_data)
            elif channel == "events:spider_progress":
                await self._handle_spider_progress(event_data)
            elif channel == "events:results_processed":
                await self._handle_results_processed(event_data)
                
        except Exception as e:
            logger.error(f"❌ Error handling message from {channel}: {e}")
    
    async def _handle_spider_started(self, event_data: Dict[str, Any]):
        """スパイダー開始イベント処理"""
        task_id = event_data['task_id']
        
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task and task.status != TaskStatus.RUNNING:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now(timezone.utc)
                db.commit()
                logger.info(f"✅ Task {task_id[:8]}... status updated to RUNNING")
        except Exception as e:
            logger.error(f"❌ Error updating task start status: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _handle_spider_finished(self, event_data: Dict[str, Any]):
        """スパイダー完了イベント処理（重要）"""
        task_id = event_data['task_id']
        status = event_data.get('status', 'UNKNOWN')
        items_count = event_data.get('items_count', 0)
        return_code = event_data.get('return_code', 0)
        
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                # ステータス判定（lightprogressロジックと統一）
                if return_code == 0 and items_count > 0:
                    # 正常終了かつアイテム取得済み
                    task.status = TaskStatus.FINISHED
                    logger.info(f"✅ Task {task_id[:8]}... completed successfully ({items_count} items)")
                elif return_code == 0 and items_count == 0:
                    # 正常終了だがアイテムなし → lightprogressと同じくFAILEDに設定
                    task.status = TaskStatus.FAILED
                    task.error_count = (task.error_count or 0) + 1
                    task.error_message = "Process completed but no items were collected - marked as FAILED (redis event fix)"
                    logger.warning(f"⚠️ Task {task_id[:8]}... completed with no items - marked as FAILED")
                else:
                    # 異常終了
                    task.status = TaskStatus.FAILED
                    logger.warning(f"❌ Task {task_id[:8]}... failed (return_code: {return_code})")
                
                # 統計情報を更新
                task.items_count = items_count
                task.finished_at = datetime.now(timezone.utc)
                
                db.commit()
                logger.info(f"🔧 Task {task_id[:8]}... status updated to {task.status.value}")
                
        except Exception as e:
            logger.error(f"❌ Error updating task finish status: {e}")
            db.rollback()
        finally:
            db.close()

    async def _handle_spider_progress(self, event_data: Dict[str, Any]):
        """スパイダー進捗イベント処理"""
        task_id = event_data['task_id']
        items_processed = event_data.get('items_processed', 0)

        # 進捗更新は頻繁なのでログレベルを下げる
        if items_processed > 0:
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.items_count = items_processed
                    db.commit()
            except Exception as e:
                logger.debug(f"Progress update error for {task_id}: {e}")
                db.rollback()
            finally:
                db.close()

    async def _handle_results_processed(self, event_data: Dict[str, Any]):
        """結果処理完了イベント処理"""
        task_id = event_data['task_id']
        statistics = event_data.get('statistics', {})

        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                # 統計情報を反映
                items_count = statistics.get('items_count', task.items_count or 0)
                task.items_count = items_count

                # 重複削除数があれば記録
                duplicates_removed = statistics.get('duplicates_removed', 0)
                if duplicates_removed > 0:
                    logger.info(f"🧹 Task {task_id[:8]}... removed {duplicates_removed} duplicates")

                db.commit()
                logger.info(f"📊 Task {task_id[:8]}... statistics updated")
        except Exception as e:
            logger.error(f"❌ Error updating task statistics: {e}")
            db.rollback()
        finally:
            db.close()


# グローバルインスタンス
redis_event_listener = RedisEventListener()
