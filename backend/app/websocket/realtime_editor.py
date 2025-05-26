"""
リアルタイム編集機能
WebSocketを使用した複数ユーザーでの同時編集
"""
import json
import asyncio
from typing import Dict, List, Set, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from fastapi import WebSocket, WebSocketDisconnect
import uuid


@dataclass
class EditOperation:
    """編集操作を表すクラス"""
    id: str
    user_id: str
    file_path: str
    operation_type: str  # 'insert', 'delete', 'replace'
    position: int
    content: str
    timestamp: str
    
    def to_dict(self):
        return asdict(self)


@dataclass
class User:
    """接続ユーザーを表すクラス"""
    id: str
    name: str
    websocket: WebSocket
    current_file: Optional[str] = None
    cursor_position: int = 0
    selection_start: int = 0
    selection_end: int = 0


@dataclass
class FileSession:
    """ファイル編集セッションを表すクラス"""
    file_path: str
    project_id: str
    users: Dict[str, User]
    operations: List[EditOperation]
    content: str
    last_saved: str
    lock_user: Optional[str] = None
    lock_expires: Optional[str] = None


class RealtimeEditorManager:
    """リアルタイム編集マネージャー"""
    
    def __init__(self):
        self.sessions: Dict[str, FileSession] = {}  # file_key -> FileSession
        self.user_sessions: Dict[str, str] = {}     # user_id -> file_key
        self.operation_queue: asyncio.Queue = asyncio.Queue()
        
    def get_file_key(self, project_id: str, file_path: str) -> str:
        """ファイルキーを生成"""
        return f"{project_id}:{file_path}"
    
    async def connect_user(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        user_name: str, 
        project_id: str, 
        file_path: str
    ) -> bool:
        """ユーザーをファイル編集セッションに接続"""
        await websocket.accept()
        
        file_key = self.get_file_key(project_id, file_path)
        
        # ユーザーオブジェクトを作成
        user = User(
            id=user_id,
            name=user_name,
            websocket=websocket,
            current_file=file_path
        )
        
        # セッションが存在しない場合は作成
        if file_key not in self.sessions:
            self.sessions[file_key] = FileSession(
                file_path=file_path,
                project_id=project_id,
                users={},
                operations=[],
                content="",
                last_saved=datetime.now().isoformat()
            )
        
        # ユーザーをセッションに追加
        session = self.sessions[file_key]
        session.users[user_id] = user
        self.user_sessions[user_id] = file_key
        
        # 他のユーザーに新しいユーザーの参加を通知
        await self._broadcast_user_joined(session, user)
        
        # 新しいユーザーに現在の状態を送信
        await self._send_initial_state(user, session)
        
        return True
    
    async def disconnect_user(self, user_id: str):
        """ユーザーを切断"""
        if user_id in self.user_sessions:
            file_key = self.user_sessions[user_id]
            session = self.sessions.get(file_key)
            
            if session and user_id in session.users:
                user = session.users[user_id]
                
                # ユーザーを削除
                del session.users[user_id]
                del self.user_sessions[user_id]
                
                # 他のユーザーに離脱を通知
                await self._broadcast_user_left(session, user)
                
                # セッションにユーザーがいなくなった場合は削除
                if not session.users:
                    del self.sessions[file_key]
    
    async def handle_edit_operation(self, user_id: str, operation_data: Dict):
        """編集操作を処理"""
        if user_id not in self.user_sessions:
            return False
        
        file_key = self.user_sessions[user_id]
        session = self.sessions.get(file_key)
        
        if not session:
            return False
        
        # 編集操作を作成
        operation = EditOperation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            file_path=session.file_path,
            operation_type=operation_data.get('type'),
            position=operation_data.get('position', 0),
            content=operation_data.get('content', ''),
            timestamp=datetime.now().isoformat()
        )
        
        # 操作を適用
        success = await self._apply_operation(session, operation)
        
        if success:
            # 操作を履歴に追加
            session.operations.append(operation)
            
            # 他のユーザーに操作を配信
            await self._broadcast_operation(session, operation, exclude_user=user_id)
            
            return True
        
        return False
    
    async def handle_cursor_update(self, user_id: str, cursor_data: Dict):
        """カーソル位置の更新を処理"""
        if user_id not in self.user_sessions:
            return
        
        file_key = self.user_sessions[user_id]
        session = self.sessions.get(file_key)
        
        if not session or user_id not in session.users:
            return
        
        user = session.users[user_id]
        user.cursor_position = cursor_data.get('position', 0)
        user.selection_start = cursor_data.get('selection_start', 0)
        user.selection_end = cursor_data.get('selection_end', 0)
        
        # 他のユーザーにカーソル位置を配信
        await self._broadcast_cursor_update(session, user)
    
    async def save_file(self, user_id: str) -> bool:
        """ファイルを保存"""
        if user_id not in self.user_sessions:
            return False
        
        file_key = self.user_sessions[user_id]
        session = self.sessions.get(file_key)
        
        if not session:
            return False
        
        try:
            # ここで実際のファイル保存処理を行う
            # file_manager.write_file(session.project_id, session.file_path, session.content)
            
            session.last_saved = datetime.now().isoformat()
            
            # 保存完了を全ユーザーに通知
            await self._broadcast_file_saved(session, user_id)
            
            return True
        except Exception as e:
            await self._broadcast_error(session, f"保存に失敗しました: {str(e)}")
            return False
    
    async def _apply_operation(self, session: FileSession, operation: EditOperation) -> bool:
        """編集操作をファイル内容に適用"""
        try:
            content = session.content
            position = operation.position
            
            if operation.operation_type == 'insert':
                session.content = content[:position] + operation.content + content[position:]
            elif operation.operation_type == 'delete':
                end_position = position + len(operation.content)
                session.content = content[:position] + content[end_position:]
            elif operation.operation_type == 'replace':
                end_position = position + len(operation.content)
                session.content = content[:position] + operation.content + content[end_position:]
            
            return True
        except Exception:
            return False
    
    async def _send_initial_state(self, user: User, session: FileSession):
        """新しいユーザーに初期状態を送信"""
        message = {
            'type': 'initial_state',
            'content': session.content,
            'users': [
                {
                    'id': u.id,
                    'name': u.name,
                    'cursor_position': u.cursor_position,
                    'selection_start': u.selection_start,
                    'selection_end': u.selection_end
                }
                for u in session.users.values() if u.id != user.id
            ],
            'last_saved': session.last_saved
        }
        
        await user.websocket.send_text(json.dumps(message))
    
    async def _broadcast_user_joined(self, session: FileSession, new_user: User):
        """新しいユーザーの参加を配信"""
        message = {
            'type': 'user_joined',
            'user': {
                'id': new_user.id,
                'name': new_user.name,
                'cursor_position': new_user.cursor_position
            }
        }
        
        await self._broadcast_to_session(session, message, exclude_user=new_user.id)
    
    async def _broadcast_user_left(self, session: FileSession, left_user: User):
        """ユーザーの離脱を配信"""
        message = {
            'type': 'user_left',
            'user_id': left_user.id
        }
        
        await self._broadcast_to_session(session, message)
    
    async def _broadcast_operation(self, session: FileSession, operation: EditOperation, exclude_user: str = None):
        """編集操作を配信"""
        message = {
            'type': 'operation',
            'operation': operation.to_dict()
        }
        
        await self._broadcast_to_session(session, message, exclude_user)
    
    async def _broadcast_cursor_update(self, session: FileSession, user: User):
        """カーソル位置の更新を配信"""
        message = {
            'type': 'cursor_update',
            'user_id': user.id,
            'cursor_position': user.cursor_position,
            'selection_start': user.selection_start,
            'selection_end': user.selection_end
        }
        
        await self._broadcast_to_session(session, message, exclude_user=user.id)
    
    async def _broadcast_file_saved(self, session: FileSession, saved_by: str):
        """ファイル保存完了を配信"""
        message = {
            'type': 'file_saved',
            'saved_by': saved_by,
            'timestamp': session.last_saved
        }
        
        await self._broadcast_to_session(session, message)
    
    async def _broadcast_error(self, session: FileSession, error_message: str):
        """エラーメッセージを配信"""
        message = {
            'type': 'error',
            'message': error_message
        }
        
        await self._broadcast_to_session(session, message)
    
    async def _broadcast_to_session(self, session: FileSession, message: Dict, exclude_user: str = None):
        """セッション内の全ユーザーにメッセージを配信"""
        message_text = json.dumps(message)
        
        for user_id, user in session.users.items():
            if exclude_user and user_id == exclude_user:
                continue
            
            try:
                await user.websocket.send_text(message_text)
            except Exception:
                # 接続が切れている場合は無視
                pass


# グローバルマネージャーインスタンス
realtime_manager = RealtimeEditorManager()
