import asyncio
import json
import os
import subprocess
import shlex
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TerminalManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.base_directory = "/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects"
        self.allowed_commands = ["scrapy", "crontab", "pwd", "less", "cd", "ls", "clear"]

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Terminal client {client_id} connected")

        # 初期ディレクトリの確認
        if not os.path.exists(self.base_directory):
            os.makedirs(self.base_directory, exist_ok=True)

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Terminal client {client_id} disconnected")

    async def send_message(self, websocket: WebSocket, message_type: str, content: str):
        try:
            # WebSocket接続状態をチェック
            if websocket.client_state.name != "CONNECTED":
                logger.warning(f"WebSocket not connected, state: {websocket.client_state.name}")
                return

            await websocket.send_text(json.dumps({
                "type": message_type,
                "content": content
            }))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def send_directory_change(self, websocket: WebSocket, directory: str):
        try:
            # WebSocket接続状態をチェック
            if websocket.client_state.name != "CONNECTED":
                logger.warning(f"WebSocket not connected for directory change, state: {websocket.client_state.name}")
                return

            await websocket.send_text(json.dumps({
                "type": "directory_changed",
                "directory": directory
            }))
        except Exception as e:
            logger.error(f"Failed to send directory change: {e}")

    def validate_command(self, command: str) -> bool:
        """コマンドが許可されているかチェック"""
        if not command.strip():
            return False

        command_parts = shlex.split(command)
        base_command = command_parts[0]

        return base_command in self.allowed_commands

    def get_safe_directory(self, current_dir: str, target_dir: str) -> str:
        """安全なディレクトリパスを取得"""
        if target_dir.startswith('/'):
            # 絶対パス
            new_path = os.path.abspath(target_dir)
        else:
            # 相対パス
            new_path = os.path.abspath(os.path.join(current_dir, target_dir))

        # ベースディレクトリ内に制限
        base_abs = os.path.abspath(self.base_directory)
        if not new_path.startswith(base_abs):
            return current_dir

        if os.path.exists(new_path) and os.path.isdir(new_path):
            return new_path
        else:
            return current_dir

    async def execute_command(self, websocket: WebSocket, command: str, current_directory: str):
        """コマンドを実行"""
        try:
            if not self.validate_command(command):
                await self.send_message(websocket, "error", f"Command not allowed: {command}")
                return current_directory

            command_parts = shlex.split(command)
            base_command = command_parts[0]

            # cdコマンドの特別処理
            if base_command == "cd":
                if len(command_parts) == 1:
                    # cd without arguments - go to base directory
                    new_dir = self.base_directory
                else:
                    target_dir = command_parts[1]
                    new_dir = self.get_safe_directory(current_directory, target_dir)

                if new_dir != current_directory:
                    await self.send_directory_change(websocket, new_dir)
                    await self.send_message(websocket, "output", f"Changed directory to: {new_dir}")
                else:
                    await self.send_message(websocket, "error", f"Cannot change to directory: {command_parts[1] if len(command_parts) > 1 else 'home'}")

                return new_dir

            # pwdコマンドの処理
            elif base_command == "pwd":
                await self.send_message(websocket, "output", current_directory)
                return current_directory

            # その他のコマンド実行
            else:
                # 環境変数の設定
                env = os.environ.copy()
                env['PWD'] = current_directory

                # プロセス実行
                process = await asyncio.create_subprocess_exec(
                    *command_parts,
                    cwd=current_directory,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )

                # ストリーミング出力
                async def read_stream(stream, message_type):
                    buffer = ""
                    while True:
                        try:
                            chunk = await stream.read(1024)  # チャンクサイズを指定
                            if not chunk:
                                # 残りのバッファを送信
                                if buffer.strip():
                                    await self.send_message(websocket, message_type, buffer.rstrip())
                                break

                            try:
                                decoded_chunk = chunk.decode('utf-8')
                                buffer += decoded_chunk

                                # 行ごとに分割して送信
                                while '\n' in buffer:
                                    line, buffer = buffer.split('\n', 1)
                                    if line.strip():
                                        await self.send_message(websocket, message_type, line)

                            except UnicodeDecodeError:
                                # バイナリデータの場合
                                await self.send_message(websocket, message_type, f"[Binary data: {len(chunk)} bytes]")
                                buffer = ""

                        except Exception as e:
                            logger.error(f"Stream reading error: {e}")
                            break

                # 並行してstdoutとstderrを読み取り
                await asyncio.gather(
                    read_stream(process.stdout, "output"),
                    read_stream(process.stderr, "error")
                )

                # プロセス終了を待機
                return_code = await process.wait()

                if return_code != 0:
                    await self.send_message(websocket, "error", f"Command exited with code: {return_code}")

                return current_directory

        except FileNotFoundError:
            await self.send_message(websocket, "error", f"Command not found: {base_command}")
            return current_directory
        except PermissionError:
            await self.send_message(websocket, "error", f"Permission denied: {command}")
            return current_directory
        except Exception as e:
            await self.send_message(websocket, "error", f"Error executing command: {str(e)}")
            return current_directory

# グローバルインスタンス
terminal_manager = TerminalManager()

async def websocket_endpoint(websocket: WebSocket):
    client_id = f"terminal_{id(websocket)}"
    current_directory = terminal_manager.base_directory

    logger.info(f"🔌 Terminal WebSocket connection attempt from {client_id}")

    try:
        # WebSocket接続を受け入れる
        await websocket.accept()
        logger.info(f"✅ Terminal WebSocket accepted: {client_id}")

        # TerminalManagerに接続を登録（connectメソッドは使わずに直接登録）
        terminal_manager.active_connections[client_id] = websocket
        logger.info(f"📝 Terminal connection registered: {client_id}")

        # 接続確認メッセージを送信
        await terminal_manager.send_message(websocket, "output", f"Terminal ready. Working directory: {current_directory}")

        while True:
            try:
                # WebSocketからメッセージを受信
                data = await websocket.receive_text()
                logger.info(f"📨 Terminal received message from {client_id}: {data}")

                try:
                    message = json.loads(data)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error from {client_id}: {e}")
                    await terminal_manager.send_message(websocket, "error", "Invalid JSON format")
                    continue

                if message.get("type") == "command":
                    command = message.get("command", "")
                    directory = message.get("directory", current_directory)

                    logger.info(f"🚀 Terminal executing command: '{command}' in {directory}")

                    # ディレクトリの安全性チェック
                    if not directory.startswith(terminal_manager.base_directory):
                        logger.warning(f"⚠️ Directory access denied: {directory}")
                        directory = terminal_manager.base_directory

                    current_directory = await terminal_manager.execute_command(
                        websocket, command, directory
                    )
                elif message.get("type") == "ping":
                    # Pingメッセージに対してpongを返す
                    timestamp = message.get("timestamp", "unknown")
                    is_heartbeat = message.get("heartbeat", False)

                    if is_heartbeat:
                        logger.info(f"💓 Terminal heartbeat received from {client_id}, timestamp: {timestamp}")
                        # ハートビートには簡潔なpongを返す
                        await terminal_manager.send_message(websocket, "pong", f"heartbeat_ack_{timestamp}")
                    else:
                        logger.info(f"🏓 Terminal ping received from {client_id}, timestamp: {timestamp}")
                        await terminal_manager.send_message(websocket, "output", f"pong (timestamp: {timestamp})")
                else:
                    logger.warning(f"⚠️ Unknown message type from {client_id}: {message.get('type')}")

            except WebSocketDisconnect:
                logger.info(f"🔌 Terminal WebSocket disconnected normally: {client_id}")
                break
            except Exception as msg_error:
                logger.error(f"❌ Terminal message error from {client_id}: {msg_error}")
                await terminal_manager.send_message(websocket, "error", f"Message processing error: {str(msg_error)}")
                continue

    except WebSocketDisconnect as e:
        logger.info(f"🔌 Terminal WebSocket disconnected during handshake: {client_id}, code: {getattr(e, 'code', 'unknown')}")
    except Exception as e:
        logger.error(f"❌ Terminal WebSocket error: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(f"❌ Error details: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
    finally:
        terminal_manager.disconnect(client_id)
        logger.info(f"🧹 Terminal WebSocket cleanup completed: {client_id}")
