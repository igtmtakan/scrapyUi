"""
ストリーミング処理サービス
大容量データ処理とリアルタイム進捗表示に対応
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
from pathlib import Path
from datetime import datetime
import uuid
from dataclasses import dataclass, asdict
from enum import Enum


class StreamingStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StreamingProgress:
    task_id: str
    status: StreamingStatus
    total_items: int
    processed_items: int
    current_item: Optional[Dict[str, Any]]
    start_time: datetime
    last_update: datetime
    error_count: int
    errors: List[str]
    estimated_completion: Optional[datetime]
    
    @property
    def progress_percentage(self) -> float:
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100
    
    @property
    def items_per_second(self) -> float:
        elapsed = (self.last_update - self.start_time).total_seconds()
        if elapsed == 0:
            return 0.0
        return self.processed_items / elapsed


class StreamingService:
    """ストリーミング処理サービス"""
    
    def __init__(self):
        self.active_streams: Dict[str, StreamingProgress] = {}
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        self.batch_size = 1000
        self.max_memory_items = 10000
    
    def create_stream(self, task_id: str, total_items: int = 0) -> StreamingProgress:
        """新しいストリームを作成"""
        progress = StreamingProgress(
            task_id=task_id,
            status=StreamingStatus.PENDING,
            total_items=total_items,
            processed_items=0,
            current_item=None,
            start_time=datetime.now(),
            last_update=datetime.now(),
            error_count=0,
            errors=[],
            estimated_completion=None
        )
        
        self.active_streams[task_id] = progress
        self.progress_callbacks[task_id] = []
        return progress
    
    def start_stream(self, task_id: str):
        """ストリームを開始"""
        if task_id in self.active_streams:
            self.active_streams[task_id].status = StreamingStatus.RUNNING
            self.active_streams[task_id].start_time = datetime.now()
            self._notify_progress(task_id)
    
    def update_progress(self, task_id: str, processed_items: int, current_item: Optional[Dict[str, Any]] = None):
        """進捗を更新"""
        if task_id not in self.active_streams:
            return
        
        progress = self.active_streams[task_id]
        progress.processed_items = processed_items
        progress.current_item = current_item
        progress.last_update = datetime.now()
        
        # 完了予測時間を計算
        if progress.processed_items > 0 and progress.total_items > 0:
            elapsed = (progress.last_update - progress.start_time).total_seconds()
            items_per_second = progress.processed_items / elapsed
            remaining_items = progress.total_items - progress.processed_items
            if items_per_second > 0:
                remaining_seconds = remaining_items / items_per_second
                progress.estimated_completion = progress.last_update + timedelta(seconds=remaining_seconds)
        
        self._notify_progress(task_id)
    
    def add_error(self, task_id: str, error: str):
        """エラーを追加"""
        if task_id not in self.active_streams:
            return
        
        progress = self.active_streams[task_id]
        progress.error_count += 1
        progress.errors.append(f"{datetime.now().isoformat()}: {error}")
        
        # エラーリストが長くなりすぎないように制限
        if len(progress.errors) > 100:
            progress.errors = progress.errors[-50:]
        
        self._notify_progress(task_id)
    
    def complete_stream(self, task_id: str, success: bool = True):
        """ストリームを完了"""
        if task_id not in self.active_streams:
            return
        
        progress = self.active_streams[task_id]
        progress.status = StreamingStatus.COMPLETED if success else StreamingStatus.FAILED
        progress.last_update = datetime.now()
        self._notify_progress(task_id)
    
    def cancel_stream(self, task_id: str):
        """ストリームをキャンセル"""
        if task_id not in self.active_streams:
            return
        
        progress = self.active_streams[task_id]
        progress.status = StreamingStatus.CANCELLED
        progress.last_update = datetime.now()
        self._notify_progress(task_id)
    
    def get_progress(self, task_id: str) -> Optional[StreamingProgress]:
        """進捗情報を取得"""
        return self.active_streams.get(task_id)
    
    def get_all_active_streams(self) -> Dict[str, StreamingProgress]:
        """すべてのアクティブストリームを取得"""
        return {
            task_id: progress 
            for task_id, progress in self.active_streams.items()
            if progress.status in [StreamingStatus.PENDING, StreamingStatus.RUNNING]
        }
    
    def register_progress_callback(self, task_id: str, callback: Callable):
        """進捗コールバックを登録"""
        if task_id not in self.progress_callbacks:
            self.progress_callbacks[task_id] = []
        self.progress_callbacks[task_id].append(callback)
    
    def _notify_progress(self, task_id: str):
        """進捗通知を送信"""
        if task_id not in self.progress_callbacks:
            return
        
        progress = self.active_streams[task_id]
        for callback in self.progress_callbacks[task_id]:
            try:
                callback(progress)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    async def stream_jsonl_file(self, file_path: Path, task_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """JSONLファイルをストリーミング読み込み"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # ファイルサイズから推定アイテム数を計算
        file_size = file_path.stat().st_size
        estimated_items = max(1, file_size // 100)  # 1アイテム約100バイトと仮定
        
        progress = self.create_stream(task_id, estimated_items)
        self.start_stream(task_id)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                processed_count = 0
                batch = []
                
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        item = json.loads(line)
                        batch.append(item)
                        processed_count += 1
                        
                        # バッチサイズに達したら yield
                        if len(batch) >= self.batch_size:
                            for batch_item in batch:
                                yield batch_item
                            
                            self.update_progress(task_id, processed_count, item)
                            batch = []
                            
                            # メモリ使用量制御のための小休止
                            await asyncio.sleep(0.01)
                    
                    except json.JSONDecodeError as e:
                        error_msg = f"Line {line_num}: JSON decode error - {e}"
                        self.add_error(task_id, error_msg)
                        continue
                
                # 残りのバッチを処理
                for batch_item in batch:
                    yield batch_item
                
                self.complete_stream(task_id, True)
                
        except Exception as e:
            self.add_error(task_id, str(e))
            self.complete_stream(task_id, False)
            raise
    
    async def stream_json_file(self, file_path: Path, task_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """JSONファイルをストリーミング読み込み"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        progress = self.create_stream(task_id)
        self.start_stream(task_id)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                progress.total_items = len(data)
                
                for i, item in enumerate(data):
                    yield item
                    self.update_progress(task_id, i + 1, item)
                    
                    # メモリ使用量制御のための小休止
                    if i % self.batch_size == 0:
                        await asyncio.sleep(0.01)
            else:
                progress.total_items = 1
                yield data
                self.update_progress(task_id, 1, data)
            
            self.complete_stream(task_id, True)
            
        except Exception as e:
            self.add_error(task_id, str(e))
            self.complete_stream(task_id, False)
            raise
    
    def cleanup_completed_streams(self, max_age_hours: int = 24):
        """完了したストリームをクリーンアップ"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for task_id, progress in self.active_streams.items():
            if (progress.status in [StreamingStatus.COMPLETED, StreamingStatus.FAILED, StreamingStatus.CANCELLED] 
                and progress.last_update < cutoff_time):
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.active_streams[task_id]
            if task_id in self.progress_callbacks:
                del self.progress_callbacks[task_id]
    
    def get_stream_statistics(self) -> Dict[str, Any]:
        """ストリーム統計を取得"""
        total_streams = len(self.active_streams)
        active_streams = len(self.get_all_active_streams())
        
        status_counts = {}
        for progress in self.active_streams.values():
            status = progress.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_streams": total_streams,
            "active_streams": active_streams,
            "status_distribution": status_counts,
            "batch_size": self.batch_size,
            "max_memory_items": self.max_memory_items
        }


# サービスインスタンス
streaming_service = StreamingService()
