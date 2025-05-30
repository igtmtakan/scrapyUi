"""
RealtimeWebSocketManager - リアルタイム進捗のWebSocket通知管理

このモジュールはScrapyのリアルタイム進捗をWebSocketを通じて
フロントエンドに送信する機能を提供します。

機能:
- リアルタイム進捗通知
- ダウンロード状況の即座通知
- アイテム処理状況の通知
- エラー・例外の即座通知
- 統計情報のリアルタイム更新
"""

import asyncio
import json
from typing import Dict, Any, Set, Optional
from datetime import datetime, timezone
import threading
import queue


class RealtimeWebSocketManager:
    """リアルタイムWebSocket通知管理クラス"""
    
    def __init__(self):
        self.connections: Set = set()
        self.message_queue = queue.Queue()
        self.is_running = False
        self.worker_thread = None
        
    def add_connection(self, websocket):
        """WebSocket接続を追加"""
        self.connections.add(websocket)
        print(f"📡 WebSocket connection added. Total: {len(self.connections)}")
        
    def remove_connection(self, websocket):
        """WebSocket接続を削除"""
        self.connections.discard(websocket)
        print(f"📡 WebSocket connection removed. Total: {len(self.connections)}")
        
    def start(self):
        """WebSocket通知サービスを開始"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            print("🚀 Realtime WebSocket Manager started")
            
    def stop(self):
        """WebSocket通知サービスを停止"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        print("🛑 Realtime WebSocket Manager stopped")
        
    def notify_progress(self, task_id: str, progress_data: Dict[str, Any]):
        """進捗通知をキューに追加"""
        try:
            message = {
                'type': 'task_progress',
                'task_id': task_id,
                'data': progress_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.message_queue.put(message, block=False)
            
        except queue.Full:
            print("⚠️ WebSocket message queue is full, dropping message")
        except Exception as e:
            print(f"❌ Error queuing progress notification: {e}")
            
    def notify_download_progress(self, task_id: str, download_data: Dict[str, Any]):
        """ダウンロード進捗通知"""
        try:
            message = {
                'type': 'download_progress',
                'task_id': task_id,
                'data': download_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.message_queue.put(message, block=False)
            
        except Exception as e:
            print(f"❌ Error queuing download notification: {e}")
            
    def notify_item_processed(self, task_id: str, item_data: Dict[str, Any]):
        """アイテム処理通知"""
        try:
            message = {
                'type': 'item_processed',
                'task_id': task_id,
                'data': item_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.message_queue.put(message, block=False)
            
        except Exception as e:
            print(f"❌ Error queuing item notification: {e}")
            
    def notify_error(self, task_id: str, error_data: Dict[str, Any]):
        """エラー通知"""
        try:
            message = {
                'type': 'task_error',
                'task_id': task_id,
                'data': error_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.message_queue.put(message, block=False)
            
        except Exception as e:
            print(f"❌ Error queuing error notification: {e}")
            
    def notify_completion(self, task_id: str, completion_data: Dict[str, Any]):
        """完了通知"""
        try:
            message = {
                'type': 'task_completion',
                'task_id': task_id,
                'data': completion_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.message_queue.put(message, block=False)
            
        except Exception as e:
            print(f"❌ Error queuing completion notification: {e}")
            
    def _worker_loop(self):
        """WebSocket通知ワーカーループ"""
        print("🔄 WebSocket notification worker started")
        
        while self.is_running:
            try:
                # メッセージを取得（タイムアウト付き）
                try:
                    message = self.message_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # 接続されているクライアントに送信
                if self.connections:
                    self._broadcast_message(message)
                    
                # タスク完了
                self.message_queue.task_done()
                
            except Exception as e:
                print(f"❌ Error in WebSocket worker loop: {e}")
                
        print("🛑 WebSocket notification worker stopped")
        
    def _broadcast_message(self, message: Dict[str, Any]):
        """メッセージを全接続にブロードキャスト"""
        if not self.connections:
            return
            
        # 非同期でメッセージを送信
        try:
            # 新しいイベントループで実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self._send_to_all_connections(message))
            finally:
                loop.close()
                
        except Exception as e:
            print(f"❌ Error broadcasting message: {e}")
            
    async def _send_to_all_connections(self, message: Dict[str, Any]):
        """全接続にメッセージを送信"""
        if not self.connections:
            return
            
        # JSON文字列に変換
        message_str = json.dumps(message, ensure_ascii=False)
        
        # 切断された接続を追跡
        disconnected = set()
        
        # 全接続に送信
        for websocket in self.connections.copy():
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                print(f"❌ Failed to send to WebSocket: {e}")
                disconnected.add(websocket)
                
        # 切断された接続を削除
        for websocket in disconnected:
            self.connections.discard(websocket)
            
        if disconnected:
            print(f"🔌 Removed {len(disconnected)} disconnected WebSocket connections")


class RealtimeProgressFormatter:
    """リアルタイム進捗データのフォーマッター"""
    
    @staticmethod
    def format_task_progress(progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """タスク進捗データをフォーマット"""
        return {
            'items_count': progress_data.get('items_count', 0),
            'requests_count': progress_data.get('requests_count', 0),
            'responses_count': progress_data.get('responses_count', 0),
            'errors_count': progress_data.get('errors_count', 0),
            'bytes_downloaded': progress_data.get('bytes_downloaded', 0),
            'elapsed_time': progress_data.get('elapsed_time', 0),
            'items_per_minute': progress_data.get('items_per_minute', 0),
            'requests_per_minute': progress_data.get('requests_per_minute', 0),
            'progress_percentage': RealtimeProgressFormatter._calculate_progress_percentage(progress_data),
            'estimated_completion': RealtimeProgressFormatter._estimate_completion_time(progress_data)
        }
        
    @staticmethod
    def format_download_progress(download_data: Dict[str, Any]) -> Dict[str, Any]:
        """ダウンロード進捗データをフォーマット"""
        return {
            'url': download_data.get('url', ''),
            'status': download_data.get('status', 0),
            'size': download_data.get('size', 0),
            'download_count': download_data.get('download_count', 0),
            'method': download_data.get('method', 'GET'),
            'timestamp': download_data.get('timestamp', '')
        }
        
    @staticmethod
    def format_item_progress(item_data: Dict[str, Any]) -> Dict[str, Any]:
        """アイテム進捗データをフォーマット"""
        return {
            'item_count': item_data.get('item_count', 0),
            'url': item_data.get('url', ''),
            'item_fields': item_data.get('item_fields', 0),
            'timestamp': item_data.get('timestamp', '')
        }
        
    @staticmethod
    def _calculate_progress_percentage(progress_data: Dict[str, Any]) -> float:
        """進捗率を計算"""
        items_count = progress_data.get('items_count', 0)
        estimated_total = progress_data.get('estimated_total', 100)  # デフォルト100件
        
        if estimated_total > 0:
            return min(95.0, (items_count / estimated_total) * 100)
        return 0.0
        
    @staticmethod
    def _estimate_completion_time(progress_data: Dict[str, Any]) -> Optional[str]:
        """完了予定時刻を推定"""
        try:
            items_count = progress_data.get('items_count', 0)
            items_per_minute = progress_data.get('items_per_minute', 0)
            estimated_total = progress_data.get('estimated_total', 100)
            
            if items_per_minute > 0 and items_count < estimated_total:
                remaining_items = estimated_total - items_count
                remaining_minutes = remaining_items / items_per_minute
                
                completion_time = datetime.now(timezone.utc).timestamp() + (remaining_minutes * 60)
                return datetime.fromtimestamp(completion_time, timezone.utc).isoformat()
                
        except Exception:
            pass
            
        return None


# グローバルインスタンス
realtime_websocket_manager = RealtimeWebSocketManager()
