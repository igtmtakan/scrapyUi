"""
ファイル検証ユーティリティ
"""
import os
import re
from pathlib import Path
from typing import List, Optional


class FileValidator:
    """ファイル操作の検証を行うクラス"""
    
    # 許可されるファイル拡張子
    ALLOWED_EXTENSIONS = [
        '.py', '.cfg', '.txt', '.md', '.json', '.yaml', '.yml',
        '.xml', '.csv', '.log', '.conf', '.ini'
    ]
    
    # 危険なファイル名パターン
    DANGEROUS_PATTERNS = [
        r'\.\./',  # ディレクトリトラバーサル
        r'^/',     # 絶対パス
        r'\\',     # Windowsパス区切り文字
        r'[<>:"|?*]',  # 無効な文字
    ]
    
    @classmethod
    def validate_file_path(cls, file_path: str) -> bool:
        """ファイルパスの安全性を検証"""
        if not file_path:
            return False
        
        # 危険なパターンをチェック
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, file_path):
                return False
        
        # 拡張子をチェック
        if not any(file_path.endswith(ext) for ext in cls.ALLOWED_EXTENSIONS):
            return False
        
        # ファイル名の長さをチェック
        if len(file_path) > 255:
            return False
        
        return True
    
    @classmethod
    def validate_file_content(cls, content: str, file_path: str) -> tuple[bool, Optional[str]]:
        """ファイル内容の検証"""
        if not content:
            return True, None
        
        # ファイルサイズ制限（10MB）
        if len(content.encode('utf-8')) > 10 * 1024 * 1024:
            return False, "File size exceeds 10MB limit"
        
        # Python ファイルの基本的な構文チェック
        if file_path.endswith('.py'):
            try:
                compile(content, file_path, 'exec')
            except SyntaxError as e:
                return False, f"Python syntax error: {str(e)}"
        
        # JSON ファイルの構文チェック
        if file_path.endswith('.json'):
            try:
                import json
                json.loads(content)
            except json.JSONDecodeError as e:
                return False, f"JSON syntax error: {str(e)}"
        
        return True, None
    
    @classmethod
    def get_file_type(cls, file_path: str) -> str:
        """ファイルタイプを取得"""
        if file_path.endswith('.py'):
            return 'python'
        elif file_path.endswith(('.cfg', '.ini', '.conf')):
            return 'config'
        elif file_path.endswith(('.json', '.yaml', '.yml')):
            return 'data'
        elif file_path.endswith(('.md', '.txt')):
            return 'text'
        elif file_path.endswith(('.log',)):
            return 'log'
        else:
            return 'unknown'
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """ファイル名をサニタイズ"""
        # 危険な文字を除去
        sanitized = re.sub(r'[<>:"|?*\\]', '_', filename)
        
        # 先頭・末尾の空白とドットを除去
        sanitized = sanitized.strip(' .')
        
        # 長すぎる場合は切り詰め
        if len(sanitized) > 200:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:200-len(ext)] + ext
        
        return sanitized


class ProjectFileManager:
    """プロジェクトファイル管理クラス"""
    
    def __init__(self, base_dir: str = "projects"):
        self.base_dir = Path(base_dir)
        self.validator = FileValidator()
    
    def get_project_dir(self, project_id: str) -> Path:
        """プロジェクトディレクトリを取得"""
        return self.base_dir / project_id / "files"
    
    def ensure_project_dir(self, project_id: str) -> Path:
        """プロジェクトディレクトリを作成"""
        project_dir = self.get_project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
    
    def list_files(self, project_id: str) -> List[dict]:
        """プロジェクトファイル一覧を取得"""
        project_dir = self.get_project_dir(project_id)
        files = []
        
        if project_dir.exists():
            for file_path in project_dir.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(project_dir)
                    files.append({
                        'name': file_path.name,
                        'path': str(relative_path),
                        'size': file_path.stat().st_size,
                        'modified_at': file_path.stat().st_mtime,
                        'type': self.validator.get_file_type(str(relative_path))
                    })
        
        return files
    
    def read_file(self, project_id: str, file_path: str) -> tuple[bool, str, Optional[str]]:
        """ファイルを読み込み"""
        if not self.validator.validate_file_path(file_path):
            return False, "", "Invalid file path"
        
        project_dir = self.get_project_dir(project_id)
        full_path = project_dir / file_path
        
        try:
            if full_path.exists():
                content = full_path.read_text(encoding='utf-8')
                return True, content, None
            else:
                return False, "", "File not found"
        except Exception as e:
            return False, "", f"Error reading file: {str(e)}"
    
    def write_file(self, project_id: str, file_path: str, content: str) -> tuple[bool, Optional[str]]:
        """ファイルを書き込み"""
        if not self.validator.validate_file_path(file_path):
            return False, "Invalid file path"
        
        is_valid, error_msg = self.validator.validate_file_content(content, file_path)
        if not is_valid:
            return False, error_msg
        
        project_dir = self.ensure_project_dir(project_id)
        full_path = project_dir / file_path
        
        try:
            # ディレクトリを作成
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # ファイルを書き込み
            full_path.write_text(content, encoding='utf-8')
            return True, None
        except Exception as e:
            return False, f"Error writing file: {str(e)}"
    
    def delete_file(self, project_id: str, file_path: str) -> tuple[bool, Optional[str]]:
        """ファイルを削除"""
        if not self.validator.validate_file_path(file_path):
            return False, "Invalid file path"
        
        project_dir = self.get_project_dir(project_id)
        full_path = project_dir / file_path
        
        try:
            if full_path.exists():
                full_path.unlink()
                return True, None
            else:
                return False, "File not found"
        except Exception as e:
            return False, f"Error deleting file: {str(e)}"
    
    def backup_file(self, project_id: str, file_path: str) -> tuple[bool, Optional[str]]:
        """ファイルをバックアップ"""
        project_dir = self.get_project_dir(project_id)
        source_path = project_dir / file_path
        
        if not source_path.exists():
            return False, "Source file not found"
        
        # バックアップディレクトリを作成
        backup_dir = project_dir / ".backups"
        backup_dir.mkdir(exist_ok=True)
        
        # タイムスタンプ付きのバックアップファイル名
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path}.{timestamp}.bak"
        backup_path = backup_dir / backup_name
        
        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_text(source_path.read_text(encoding='utf-8'), encoding='utf-8')
            return True, str(backup_path)
        except Exception as e:
            return False, f"Error creating backup: {str(e)}"
