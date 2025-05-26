"""
Git統合サービス
プロジェクトファイルのバージョン管理を提供
"""
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json


class GitService:
    """Git操作を管理するサービス"""
    
    def __init__(self, base_projects_dir: str = "projects"):
        self.base_projects_dir = Path(base_projects_dir)
    
    def get_project_git_dir(self, project_id: str) -> Path:
        """プロジェクトのGitディレクトリを取得"""
        return self.base_projects_dir / project_id
    
    def init_repository(self, project_id: str) -> Tuple[bool, Optional[str]]:
        """プロジェクトでGitリポジトリを初期化"""
        project_dir = self.get_project_git_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Gitリポジトリを初期化
            result = subprocess.run(
                ["git", "init"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            # .gitignoreファイルを作成
            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Scrapy
.scrapy/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
"""
            gitignore_path = project_dir / ".gitignore"
            gitignore_path.write_text(gitignore_content, encoding='utf-8')
            
            # 初期コミット
            self._configure_git_user(project_dir)
            self.add_all_files(project_id)
            self.commit(project_id, "Initial commit - ScrapyUI project setup")
            
            return True, None
            
        except subprocess.CalledProcessError as e:
            return False, f"Git initialization failed: {e.stderr}"
        except Exception as e:
            return False, f"Error initializing Git: {str(e)}"
    
    def _configure_git_user(self, project_dir: Path):
        """Git ユーザー設定"""
        try:
            subprocess.run(
                ["git", "config", "user.name", "ScrapyUI"],
                cwd=project_dir,
                check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "scrapyui@localhost"],
                cwd=project_dir,
                check=True
            )
        except subprocess.CalledProcessError:
            pass  # 設定に失敗しても続行
    
    def add_file(self, project_id: str, file_path: str) -> Tuple[bool, Optional[str]]:
        """ファイルをGitに追加"""
        project_dir = self.get_project_git_dir(project_id)
        
        try:
            subprocess.run(
                ["git", "add", file_path],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return True, None
        except subprocess.CalledProcessError as e:
            return False, f"Failed to add file: {e.stderr}"
    
    def add_all_files(self, project_id: str) -> Tuple[bool, Optional[str]]:
        """全ファイルをGitに追加"""
        project_dir = self.get_project_git_dir(project_id)
        
        try:
            subprocess.run(
                ["git", "add", "."],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return True, None
        except subprocess.CalledProcessError as e:
            return False, f"Failed to add files: {e.stderr}"
    
    def commit(self, project_id: str, message: str, author: str = None) -> Tuple[bool, Optional[str]]:
        """変更をコミット"""
        project_dir = self.get_project_git_dir(project_id)
        
        try:
            cmd = ["git", "commit", "-m", message]
            if author:
                cmd.extend(["--author", f"{author} <{author}@scrapyui.local>"])
            
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in e.stdout:
                return True, "No changes to commit"
            return False, f"Commit failed: {e.stderr}"
    
    def get_commit_history(self, project_id: str, limit: int = 50) -> List[Dict]:
        """コミット履歴を取得"""
        project_dir = self.get_project_git_dir(project_id)
        
        try:
            result = subprocess.run(
                ["git", "log", f"--max-count={limit}", "--pretty=format:%H|%an|%ae|%ad|%s", "--date=iso"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 4)
                    if len(parts) == 5:
                        commits.append({
                            'hash': parts[0],
                            'author_name': parts[1],
                            'author_email': parts[2],
                            'date': parts[3],
                            'message': parts[4]
                        })
            
            return commits
        except subprocess.CalledProcessError:
            return []
    
    def get_file_diff(self, project_id: str, file_path: str, commit_hash: str = None) -> Tuple[bool, str]:
        """ファイルの差分を取得"""
        project_dir = self.get_project_git_dir(project_id)
        
        try:
            if commit_hash:
                cmd = ["git", "show", f"{commit_hash}:{file_path}"]
            else:
                cmd = ["git", "diff", "HEAD", file_path]
            
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"Failed to get diff: {e.stderr}"
    
    def checkout_file(self, project_id: str, file_path: str, commit_hash: str) -> Tuple[bool, Optional[str]]:
        """特定のコミットからファイルを復元"""
        project_dir = self.get_project_git_dir(project_id)
        
        try:
            subprocess.run(
                ["git", "checkout", commit_hash, "--", file_path],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return True, None
        except subprocess.CalledProcessError as e:
            return False, f"Failed to checkout file: {e.stderr}"
    
    def create_branch(self, project_id: str, branch_name: str) -> Tuple[bool, Optional[str]]:
        """新しいブランチを作成"""
        project_dir = self.get_project_git_dir(project_id)
        
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return True, None
        except subprocess.CalledProcessError as e:
            return False, f"Failed to create branch: {e.stderr}"
    
    def list_branches(self, project_id: str) -> List[str]:
        """ブランチ一覧を取得"""
        project_dir = self.get_project_git_dir(project_id)
        
        try:
            result = subprocess.run(
                ["git", "branch"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            branches = []
            for line in result.stdout.strip().split('\n'):
                branch = line.strip().lstrip('* ')
                if branch:
                    branches.append(branch)
            
            return branches
        except subprocess.CalledProcessError:
            return []
    
    def switch_branch(self, project_id: str, branch_name: str) -> Tuple[bool, Optional[str]]:
        """ブランチを切り替え"""
        project_dir = self.get_project_git_dir(project_id)
        
        try:
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return True, None
        except subprocess.CalledProcessError as e:
            return False, f"Failed to switch branch: {e.stderr}"
    
    def get_status(self, project_id: str) -> Dict:
        """Git ステータスを取得"""
        project_dir = self.get_project_git_dir(project_id)
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            status = {
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': []
            }
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    status_code = line[:2]
                    file_path = line[3:]
                    
                    if status_code.startswith('M'):
                        status['modified'].append(file_path)
                    elif status_code.startswith('A'):
                        status['added'].append(file_path)
                    elif status_code.startswith('D'):
                        status['deleted'].append(file_path)
                    elif status_code.startswith('??'):
                        status['untracked'].append(file_path)
            
            return status
        except subprocess.CalledProcessError:
            return {'modified': [], 'added': [], 'deleted': [], 'untracked': []}
    
    def is_git_repository(self, project_id: str) -> bool:
        """Gitリポジトリかどうかを確認"""
        project_dir = self.get_project_git_dir(project_id)
        git_dir = project_dir / ".git"
        return git_dir.exists()


class VersionManager:
    """バージョン管理マネージャー"""
    
    def __init__(self):
        self.git_service = GitService()
    
    def auto_commit_on_save(self, project_id: str, file_path: str, author: str = "ScrapyUI") -> Tuple[bool, Optional[str]]:
        """ファイル保存時の自動コミット"""
        if not self.git_service.is_git_repository(project_id):
            success, error = self.git_service.init_repository(project_id)
            if not success:
                return False, error
        
        # ファイルを追加
        success, error = self.git_service.add_file(project_id, file_path)
        if not success:
            return False, error
        
        # 自動コミット
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Auto-save: {file_path} at {timestamp}"
        
        return self.git_service.commit(project_id, message, author)
    
    def create_snapshot(self, project_id: str, description: str, author: str = "ScrapyUI") -> Tuple[bool, Optional[str]]:
        """プロジェクトスナップショットを作成"""
        if not self.git_service.is_git_repository(project_id):
            success, error = self.git_service.init_repository(project_id)
            if not success:
                return False, error
        
        # 全ファイルを追加
        success, error = self.git_service.add_all_files(project_id)
        if not success:
            return False, error
        
        # スナップショットコミット
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Snapshot: {description} ({timestamp})"
        
        return self.git_service.commit(project_id, message, author)
