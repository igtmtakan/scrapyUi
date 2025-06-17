#!/usr/bin/env python3
"""
FeedExporterエラーの根本対応スクリプト
既存プロジェクトのFEED設定を統一FEED設定管理に基づいて修正
"""

import os
import sys
from pathlib import Path
import re

# ScrapyUIのバックエンドパスを追加
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI/backend')

# 統一FEED設定管理をインポート
from app.core.feed_config import feed_config


def fix_feed_settings_in_file(settings_file: Path, project_name: str) -> bool:
    """settings.pyファイルのFEED設定を修正"""
    try:
        if not settings_file.exists():
            print(f"⚠️ Settings file not found: {settings_file}")
            return False

        # ファイル内容を読み込み
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # バックアップを作成
        backup_file = settings_file.with_suffix('.py.backup')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📋 Backup created: {backup_file}")

        # 既存のFEED設定を削除
        # FEEDS = { ... } の部分を削除
        content = re.sub(
            r'FEEDS\s*=\s*\{[^}]*\}(?:\s*,\s*\{[^}]*\})*',
            '',
            content,
            flags=re.DOTALL
        )

        # 重複するFEED_EXPORT_ENCODINGを削除
        content = re.sub(
            r'FEED_EXPORT_ENCODING\s*=\s*[\'"][^\'"]*[\'"]',
            '',
            content
        )

        # indentパラメータを含む設定を削除
        content = re.sub(
            r"'indent'\s*:\s*\d+,?\s*",
            '',
            content
        )

        # 統一FEED設定を追加
        safe_feed_settings = feed_config.create_project_feed_settings(project_name)
        
        # ファイルの末尾に追加
        if not content.endswith('\n'):
            content += '\n'
        content += safe_feed_settings

        # ファイルに書き戻し
        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Fixed FEED settings in: {settings_file}")
        return True

    except Exception as e:
        print(f"❌ Error fixing {settings_file}: {e}")
        return False


def validate_feed_settings(settings_file: Path) -> tuple[bool, list[str]]:
    """FEED設定の妥当性を検証"""
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        errors = []

        # indentパラメータの存在チェック
        if "'indent'" in content or '"indent"' in content:
            errors.append("Found 'indent' parameter in FEED settings")

        # FEED_EXPORT_ENCODINGの存在チェック
        if 'FEED_EXPORT_ENCODING' not in content:
            errors.append("No FEED_EXPORT_ENCODING declaration found")

        # FEEDS設定の存在チェック
        if 'FEEDS = {' not in content:
            errors.append("No FEEDS configuration found")

        is_valid = len(errors) == 0
        return is_valid, errors

    except Exception as e:
        return False, [f"Error reading file: {e}"]


def main():
    """メイン処理"""
    print("🔧 FeedExporter根本対応スクリプト開始")
    print("=" * 50)

    # scrapy_projectsディレクトリを取得
    script_dir = Path(__file__).parent
    scrapy_projects_dir = script_dir.parent / "scrapy_projects"

    if not scrapy_projects_dir.exists():
        print(f"❌ scrapy_projects directory not found: {scrapy_projects_dir}")
        return

    print(f"📁 Scanning projects in: {scrapy_projects_dir}")

    # 各プロジェクトを処理
    fixed_count = 0
    error_count = 0

    for project_dir in scrapy_projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        project_name = project_dir.name
        print(f"\n🔍 Processing project: {project_name}")

        # settings.pyファイルを探す
        settings_file = None
        for subdir in project_dir.iterdir():
            if subdir.is_dir() and subdir.name == project_name:
                potential_settings = subdir / "settings.py"
                if potential_settings.exists():
                    settings_file = potential_settings
                    break

        if not settings_file:
            print(f"⚠️ No settings.py found for project: {project_name}")
            continue

        # 修正前の検証
        print(f"🔍 Validating current settings...")
        is_valid_before, errors_before = validate_feed_settings(settings_file)
        
        if is_valid_before:
            print(f"✅ Settings already valid for: {project_name}")
            continue

        print(f"❌ Found issues: {', '.join(errors_before)}")

        # FEED設定を修正
        if fix_feed_settings_in_file(settings_file, project_name):
            # 修正後の検証
            is_valid_after, errors_after = validate_feed_settings(settings_file)
            
            if is_valid_after:
                print(f"✅ Successfully fixed: {project_name}")
                fixed_count += 1
            else:
                print(f"❌ Still has issues after fix: {', '.join(errors_after)}")
                error_count += 1
        else:
            error_count += 1

    print("\n" + "=" * 50)
    print(f"🎯 修正完了: {fixed_count}個のプロジェクト")
    print(f"❌ エラー: {error_count}個のプロジェクト")
    
    if fixed_count > 0:
        print("\n✅ FeedExporter根本対応が完了しました！")
        print("📝 バックアップファイル（.py.backup）が作成されています")
    else:
        print("\n⚠️ 修正が必要なプロジェクトはありませんでした")


if __name__ == "__main__":
    main()
