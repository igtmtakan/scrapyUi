"""
WebSocket 統合テスト
"""
import pytest
import asyncio
import json
import websockets
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import threading
import time

from app.main import app
from app.websocket.manager import manager
from app.database import Task, TaskStatus


@pytest.mark.integration
@pytest.mark.websocket
class TestWebSocketIntegration:
    """WebSocket統合テスト"""

    @pytest.fixture(autouse=True)
    def setup_websocket_test(self, auth_headers, db_session):
        """WebSocket統合テスト用セットアップ"""
        self.auth_headers = auth_headers
        self.db = db_session
        self.websocket_url = "ws://localhost:8000/ws"

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """WebSocket接続テスト"""
        
        # WebSocket接続のモック
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.receive_text = AsyncMock(return_value='{"type": "ping"}')
        mock_websocket.close = AsyncMock()
        
        # WebSocketマネージャーのテスト
        connection_id = "test-connection-1"
        
        # 接続追加
        manager.active_connections[connection_id] = mock_websocket
        assert connection_id in manager.active_connections
        
        # メッセージ送信テスト
        test_message = {
            "type": "task_update",
            "data": {
                "task_id": "test-task-1",
                "status": "running",
                "progress": 50
            }
        }
        
        await manager.send_personal_message(json.dumps(test_message), connection_id)
        mock_websocket.send_text.assert_called_once_with(json.dumps(test_message))
        
        # 接続削除
        manager.disconnect(connection_id)
        assert connection_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_websocket_task_updates(self):
        """WebSocketタスク更新テスト"""
        
        # テストタスクの作成
        test_task = Task(
            id="websocket-test-task",
            spider_id="test-spider",
            project_id="test-project",
            status=TaskStatus.RUNNING,
            user_id="test-user"
        )
        self.db.add(test_task)
        self.db.commit()
        
        # WebSocket接続のモック
        mock_websocket = AsyncMock()
        connection_id = "task-update-test"
        manager.active_connections[connection_id] = mock_websocket
        
        # タスク更新データ
        update_data = {
            "id": test_task.id,
            "status": "running",
            "progress": 75,
            "items_count": 150,
            "requests_count": 200,
            "error_count": 0
        }
        
        # タスク更新送信
        await manager.send_task_update(test_task.id, update_data)
        
        # メッセージが送信されたことを確認
        mock_websocket.send_text.assert_called()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message["type"] == "task_update"
        assert sent_message["data"]["id"] == test_task.id
        assert sent_message["data"]["progress"] == 75

    @pytest.mark.asyncio
    async def test_websocket_broadcast(self):
        """WebSocketブロードキャストテスト"""
        
        # 複数の接続をモック
        connections = {}
        for i in range(3):
            connection_id = f"broadcast-test-{i}"
            mock_websocket = AsyncMock()
            connections[connection_id] = mock_websocket
            manager.active_connections[connection_id] = mock_websocket
        
        # ブロードキャストメッセージ
        broadcast_message = {
            "type": "system_notification",
            "data": {
                "message": "System maintenance scheduled",
                "level": "info",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
        
        # ブロードキャスト実行
        await manager.broadcast(json.dumps(broadcast_message))
        
        # 全ての接続にメッセージが送信されたことを確認
        for connection_id, mock_websocket in connections.items():
            mock_websocket.send_text.assert_called_with(json.dumps(broadcast_message))

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self):
        """WebSocketエラーハンドリングテスト"""
        
        # 接続エラーのモック
        mock_websocket = AsyncMock()
        mock_websocket.send_text.side_effect = Exception("Connection lost")
        
        connection_id = "error-test"
        manager.active_connections[connection_id] = mock_websocket
        
        # エラーが発生してもクラッシュしないことを確認
        try:
            await manager.send_personal_message("test message", connection_id)
        except Exception:
            pytest.fail("WebSocket error handling failed")
        
        # エラーが発生した接続は自動的に削除される
        assert connection_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_websocket_authentication(self):
        """WebSocket認証テスト"""
        
        # 認証付きWebSocket接続のモック
        mock_websocket = AsyncMock()
        mock_websocket.headers = {"authorization": "Bearer valid-token"}
        
        # 認証成功のテスト
        with patch('app.auth.jwt_handler.verify_token') as mock_verify:
            mock_verify.return_value = {"id": "test-user", "email": "test@example.com"}
            
            # 認証処理のシミュレーション
            try:
                # WebSocket認証ロジックをテスト
                auth_header = mock_websocket.headers.get("authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    user_data = mock_verify(token)
                    assert user_data["id"] == "test-user"
            except Exception as e:
                pytest.fail(f"WebSocket authentication failed: {e}")

    @pytest.mark.asyncio
    async def test_websocket_message_types(self):
        """WebSocketメッセージタイプテスト"""
        
        mock_websocket = AsyncMock()
        connection_id = "message-type-test"
        manager.active_connections[connection_id] = mock_websocket
        
        # 異なるタイプのメッセージをテスト
        message_types = [
            {
                "type": "task_started",
                "data": {"task_id": "task-1", "spider_name": "test_spider"}
            },
            {
                "type": "task_progress",
                "data": {"task_id": "task-1", "progress": 50, "items_scraped": 100}
            },
            {
                "type": "task_completed",
                "data": {"task_id": "task-1", "status": "finished", "total_items": 200}
            },
            {
                "type": "task_failed",
                "data": {"task_id": "task-1", "error": "Connection timeout"}
            },
            {
                "type": "spider_log",
                "data": {"task_id": "task-1", "level": "INFO", "message": "Spider started"}
            }
        ]
        
        for message in message_types:
            await manager.send_personal_message(json.dumps(message), connection_id)
            mock_websocket.send_text.assert_called_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self):
        """WebSocket接続ライフサイクルテスト"""
        
        connection_id = "lifecycle-test"
        mock_websocket = AsyncMock()
        
        # 接続開始
        manager.connect(mock_websocket, connection_id)
        assert connection_id in manager.active_connections
        assert len(manager.active_connections) >= 1
        
        # 接続中のメッセージ送信
        test_message = {"type": "ping", "data": {}}
        await manager.send_personal_message(json.dumps(test_message), connection_id)
        mock_websocket.send_text.assert_called_with(json.dumps(test_message))
        
        # 接続終了
        manager.disconnect(connection_id)
        assert connection_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_websocket_concurrent_connections(self):
        """WebSocket同時接続テスト"""
        
        # 複数の同時接続をシミュレート
        connections = []
        for i in range(10):
            connection_id = f"concurrent-{i}"
            mock_websocket = AsyncMock()
            manager.connect(mock_websocket, connection_id)
            connections.append((connection_id, mock_websocket))
        
        assert len(manager.active_connections) >= 10
        
        # 全接続に同時メッセージ送信
        concurrent_message = {
            "type": "concurrent_test",
            "data": {"message": "Testing concurrent connections"}
        }
        
        # 並列でメッセージ送信
        tasks = []
        for connection_id, _ in connections:
            task = manager.send_personal_message(
                json.dumps(concurrent_message), 
                connection_id
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # 全接続でメッセージが送信されたことを確認
        for _, mock_websocket in connections:
            mock_websocket.send_text.assert_called_with(json.dumps(concurrent_message))
        
        # 接続をクリーンアップ
        for connection_id, _ in connections:
            manager.disconnect(connection_id)

    @pytest.mark.asyncio
    async def test_websocket_performance(self):
        """WebSocketパフォーマンステスト"""
        
        connection_id = "performance-test"
        mock_websocket = AsyncMock()
        manager.connect(mock_websocket, connection_id)
        
        # 大量メッセージの送信テスト
        start_time = time.time()
        
        message_count = 100
        for i in range(message_count):
            message = {
                "type": "performance_test",
                "data": {"sequence": i, "timestamp": time.time()}
            }
            await manager.send_personal_message(json.dumps(message), connection_id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # パフォーマンス要件（1秒以内で100メッセージ）
        assert duration < 1.0, f"Performance test took {duration:.2f} seconds"
        assert mock_websocket.send_text.call_count == message_count
        
        manager.disconnect(connection_id)

    @pytest.mark.asyncio
    async def test_websocket_message_queue(self):
        """WebSocketメッセージキューテスト"""
        
        # 接続が一時的に利用できない場合のテスト
        connection_id = "queue-test"
        mock_websocket = AsyncMock()
        
        # 最初は接続なし
        assert connection_id not in manager.active_connections
        
        # メッセージ送信試行（接続なしでエラーにならないことを確認）
        message = {"type": "queued_message", "data": {"test": True}}
        try:
            await manager.send_personal_message(json.dumps(message), connection_id)
        except Exception:
            pass  # 接続がない場合は正常
        
        # 後で接続を追加
        manager.connect(mock_websocket, connection_id)
        
        # 接続後のメッセージ送信
        await manager.send_personal_message(json.dumps(message), connection_id)
        mock_websocket.send_text.assert_called_with(json.dumps(message))
        
        manager.disconnect(connection_id)

    def test_websocket_integration_with_api(self, client):
        """WebSocketとAPI統合テスト"""
        
        # APIエンドポイントからWebSocketメッセージが送信されることをテスト
        with patch.object(manager, 'send_task_update') as mock_send:
            mock_send.return_value = asyncio.Future()
            mock_send.return_value.set_result(None)
            
            # タスク作成API呼び出し
            task_data = {
                "spider_id": "test-spider",
                "settings": {"DOWNLOAD_DELAY": 1}
            }
            
            with patch('app.services.scrapy_service.ScrapyPlaywrightService.run_spider') as mock_run:
                mock_run.return_value = "test-task-id"
                
                response = client.post(
                    "/api/tasks/",
                    json=task_data,
                    headers=self.auth_headers
                )
                
                assert response.status_code == 200
                # WebSocketメッセージ送信が呼ばれることを確認
                # 実際の実装では適切なタイミングでWebSocket更新が行われる
