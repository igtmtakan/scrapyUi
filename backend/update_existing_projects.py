#!/usr/bin/env python3
"""
既存プロジェクトのsettings.pyにRich進捗バー設定を一括追加するスクリプト

このスクリプトは、scrapy_projectsディレクトリ内のすべての既存プロジェクトの
settings.pyファイルにRich進捗バー設定を自動的に追加します。
"""

import os
import sys
from pathlib import Path
import re
from typing import List, Tuple


def get_rich_progress_settings() -> str:
    """Rich進捗バー設定のテンプレートを取得"""
    return """
# ===== Rich進捗バー設定 =====
# スパイダーコードを変更せずに美しい進捗バーを表示

# ScrapyUIバックエンドへのパスを追加
import sys
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')

# Rich進捗バー拡張機能を有効化
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
    "scrapy.extensions.corestats.CoreStats": 500,
    "scrapy.extensions.logstats.LogStats": 500,
    # Rich進捗バー拡張機能を追加（スパイダーコードを変更せずに進捗バーを表示）
    "app.scrapy_extensions.rich_progress_extension.RichProgressExtension": 400,
    # 軽量プログレスシステム拡張機能を追加（より軽量で安定）
    "app.scrapy_extensions.lightweight_progress_extension.LightweightProgressExtension": 300,
}

RICH_PROGRESS_ENABLED = True           # 進捗バーを有効化
RICH_PROGRESS_SHOW_STATS = True        # 詳細統計を表示
RICH_PROGRESS_UPDATE_INTERVAL = 0.1    # 更新間隔（秒）
RICH_PROGRESS_WEBSOCKET = False        # WebSocket通知（オプション）

# ===== 軽量プログレスシステム設定 =====
# より軽量で安定したプログレス表示システム
LIGHTWEIGHT_PROGRESS_WEBSOCKET = True  # WebSocket通知を有効化
LIGHTWEIGHT_BULK_INSERT = True         # バルクインサートを有効化

# 自動ファイル管理設定
AUTO_FILE_MANAGEMENT = True           # 自動ファイル管理を有効化
MAX_JSONL_LINES = 500                 # JSONLファイルの最大行数（極めて積極的に）
KEEP_SESSIONS = 1                     # 保持するセッション数（最新のみ）
AUTO_CLEANUP_INTERVAL_HOURS = 1       # 自動クリーンアップ間隔（1時間毎）
"""


def find_scrapy_projects() -> List[Path]:
    """scrapy_projectsディレクトリ内のプロジェクトを検索"""
    projects_dir = Path("../scrapy_projects")
    if not projects_dir.exists():
        projects_dir = Path("scrapy_projects")
    
    if not projects_dir.exists():
        print("❌ scrapy_projectsディレクトリが見つかりません")
        return []
    
    projects = []
    for item in projects_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # settings.pyファイルが存在するかチェック
            settings_files = list(item.glob("*/settings.py"))
            if settings_files:
                projects.append(item)
    
    return projects


def has_rich_progress_settings(content: str) -> bool:
    """既にRich進捗バー設定が含まれているかチェック"""
    patterns = [
        r"RICH_PROGRESS_ENABLED",
        r"RichProgressExtension",
        r"Rich進捗バー設定"
    ]
    
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    
    return False


def update_extensions_setting(content: str) -> str:
    """既存のEXTENSIONS設定を更新"""
    # EXTENSIONS設定を検索
    extensions_pattern = r'EXTENSIONS\s*=\s*\{([^}]*)\}'
    match = re.search(extensions_pattern, content, re.DOTALL)
    
    if match:
        # 既存のEXTENSIONS設定を更新
        existing_extensions = match.group(1)
        
        # RichProgressExtensionが既に含まれているかチェック
        if "RichProgressExtension" not in existing_extensions:
            # 新しい拡張機能を追加
            new_extensions = existing_extensions.rstrip()
            if new_extensions and not new_extensions.endswith(','):
                new_extensions += ','
            
            new_extensions += '''
    # Rich進捗バー拡張機能を追加（スパイダーコードを変更せずに進捗バーを表示）
    "app.scrapy_extensions.rich_progress_extension.RichProgressExtension": 400,
    # 軽量プログレスシステム拡張機能を追加（より軽量で安定）
    "app.scrapy_extensions.lightweight_progress_extension.LightweightProgressExtension": 300,'''
            
            # 既存のEXTENSIONS設定を置換
            new_extensions_block = f"EXTENSIONS = {{{new_extensions}\n}}"
            content = re.sub(extensions_pattern, new_extensions_block, content, flags=re.DOTALL)
    
    return content


def add_rich_progress_to_settings(settings_file: Path) -> Tuple[bool, str]:
    """settings.pyファイルにRich進捗バー設定を追加"""
    try:
        # ファイルを読み込み
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 既に設定が含まれているかチェック
        if has_rich_progress_settings(content):
            return False, "既にRich進捗バー設定が含まれています"
        
        # バックアップを作成
        backup_file = settings_file.with_suffix('.py.backup')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # sys.path.append行を追加（まだ存在しない場合）
        if "sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')" not in content:
            # import文の後に追加
            import_pattern = r'(import\s+[^\n]+\n)'
            if re.search(import_pattern, content):
                # 最後のimport文の後に追加
                imports = re.findall(import_pattern, content)
                if imports:
                    last_import = imports[-1]
                    sys_import = "\n# ScrapyUIバックエンドへのパスを追加\nimport sys\nsys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')\n"
                    content = content.replace(last_import, last_import + sys_import)
        
        # 既存のEXTENSIONS設定を更新
        content = update_extensions_setting(content)
        
        # Rich進捗バー設定を追加（ファイルの最後に）
        rich_settings = get_rich_progress_settings()
        
        # EXTENSIONS設定が既に更新されている場合は、EXTENSIONS部分を除外
        if "RichProgressExtension" in content:
            # EXTENSIONS設定を除外したRich設定を作成
            rich_settings_lines = rich_settings.split('\n')
            filtered_lines = []
            skip_extensions = False
            
            for line in rich_settings_lines:
                if 'EXTENSIONS = {' in line:
                    skip_extensions = True
                    continue
                elif skip_extensions and line.strip() == '}':
                    skip_extensions = False
                    continue
                elif not skip_extensions:
                    filtered_lines.append(line)
            
            rich_settings = '\n'.join(filtered_lines)
        
        content += rich_settings
        
        # ファイルに書き込み
        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, f"Rich進捗バー設定を追加しました（バックアップ: {backup_file.name}）"
    
    except Exception as e:
        return False, f"エラー: {str(e)}"


def main():
    """メイン処理"""
    print("🔧 既存プロジェクトのsettings.pyにRich進捗バー設定を一括追加")
    print("=" * 70)
    
    # プロジェクトを検索
    projects = find_scrapy_projects()
    
    if not projects:
        print("❌ Scrapyプロジェクトが見つかりませんでした")
        return
    
    print(f"📁 {len(projects)}個のプロジェクトが見つかりました")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for project in projects:
        print(f"\n📋 プロジェクト: {project.name}")
        
        # settings.pyファイルを検索
        settings_files = list(project.glob("*/settings.py"))
        
        for settings_file in settings_files:
            print(f"   📄 処理中: {settings_file.relative_to(project)}")
            
            success, message = add_rich_progress_to_settings(settings_file)
            
            if success:
                print(f"   ✅ {message}")
                updated_count += 1
            elif "既に" in message:
                print(f"   ⏭️ {message}")
                skipped_count += 1
            else:
                print(f"   ❌ {message}")
                error_count += 1
    
    # 結果サマリー
    print(f"\n📊 処理結果サマリー")
    print("=" * 70)
    print(f"✅ 更新済み: {updated_count}個")
    print(f"⏭️ スキップ: {skipped_count}個")
    print(f"❌ エラー: {error_count}個")
    print(f"📁 総プロジェクト数: {len(projects)}個")
    
    if updated_count > 0:
        print(f"\n🎉 {updated_count}個のプロジェクトにRich進捗バー設定を追加しました！")
        print("💡 今後、これらのプロジェクトでスパイダーを実行すると美しい進捗バーが表示されます")
        print("📝 バックアップファイル（*.py.backup）が作成されています")
    
    if error_count > 0:
        print(f"\n⚠️ {error_count}個のプロジェクトで問題が発生しました")
        print("🔍 エラーメッセージを確認して手動で修正してください")


if __name__ == "__main__":
    main()
