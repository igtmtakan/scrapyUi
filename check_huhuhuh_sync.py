#!/usr/bin/env python3
"""
「huhuhuh」プロジェクトのpipelines.pyのDB同期状況を確認
"""
import sqlite3
import requests
import json
from pathlib import Path
from datetime import datetime

# APIベースURL
BASE_URL = "http://localhost:8000"

def check_huhuhuh_sync():
    """「huhuhuh」プロジェクトのDB同期状況を確認"""

    print("🔍 「huhuhuh」プロジェクトのDB同期状況確認開始\n")

    # ログイン
    login_data = {'email': 'admin@scrapyui.com', 'password': 'admin123456'}
    response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    print('🔐 ログイン成功')

    # 1. データベースから「huhuhuh」プロジェクトを検索
    print('\n📋 データベースから「huhuhuh」プロジェクト検索')
    project_info = find_huhuhuh_project()

    if not project_info:
        print('❌ 「huhuhuh」プロジェクトが見つかりません')
        return False

    project_id, project_name, project_path, user_id, db_save_enabled = project_info

    print(f'✅ プロジェクト発見:')
    print(f'   ID: {project_id}')
    print(f'   名前: {project_name}')
    print(f'   パス: {project_path}')
    print(f'   DB保存設定: {"有効" if db_save_enabled else "無効"}')

    # 2. ファイルシステムの内容を確認
    print(f'\n📁 ファイルシステムの内容確認')
    filesystem_content = check_filesystem_content(project_path)

    # 3. データベースの内容を確認
    print(f'\n💾 データベースの内容確認')
    database_content = check_database_content(project_id)

    # 4. WebUI APIの内容を確認
    print(f'\n🌐 WebUI APIの内容確認')
    webui_content = check_webui_content(project_id, headers)

    # 5. 同期状況を分析
    print(f'\n📊 同期状況分析')
    analyze_sync_status(filesystem_content, database_content, webui_content, db_save_enabled)

    # 6. 必要に応じて同期を実行
    if filesystem_content and (not database_content or filesystem_content != database_content):
        print(f'\n🔄 同期が必要です。手動同期を実行しますか？')
        print(f'   ファイルシステム: {len(filesystem_content) if filesystem_content else 0}文字')
        print(f'   データベース: {len(database_content) if database_content else 0}文字')

        # 自動で同期実行
        print(f'\n🔄 自動同期実行中...')
        sync_success = manual_sync_huhuhuh(project_id, project_path, user_id, db_save_enabled)

        if sync_success:
            print(f'✅ 同期完了')

            # 同期後の確認
            print(f'\n✅ 同期後の確認')
            webui_content_after = check_webui_content(project_id, headers)

            if webui_content_after and len(webui_content_after) > len(webui_content or ''):
                print(f'🎉 WebUIで正しい内容が表示されるようになりました！')
            else:
                print(f'⚠️ WebUIの内容に変化がありません')
        else:
            print(f'❌ 同期失敗')

    return True

def find_huhuhuh_project():
    """データベースから「huhuhuh」プロジェクトを検索"""

    db_path = Path("backend/database/scrapy_ui.db")

    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return None

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 「huhuhu」を含むプロジェクトを検索
        cursor.execute("""
            SELECT id, name, path, user_id, db_save_enabled
            FROM projects
            WHERE name LIKE '%huhuhu%' OR path LIKE '%huhuhu%'
            ORDER BY created_at DESC
        """)

        results = cursor.fetchall()

        if results:
            print(f'📊 「huhuhu」関連プロジェクト: {len(results)}件')
            for i, (pid, name, path, uid, db_save) in enumerate(results):
                print(f'   {i+1}. {name} (パス: {path}, DB保存: {"有効" if db_save else "無効"})')

            # 最初のプロジェクトを返す
            return results[0]
        else:
            print(f'❌ 「huhuhu」プロジェクトが見つかりません')

            # 全プロジェクトを表示
            cursor.execute("SELECT name, path FROM projects ORDER BY created_at DESC LIMIT 10")
            all_projects = cursor.fetchall()
            print(f'\n📋 最近のプロジェクト一覧:')
            for name, path in all_projects:
                print(f'   - {name} (パス: {path})')

            return None

        conn.close()

    except Exception as e:
        print(f"❌ データベースエラー: {e}")
        return None

def check_filesystem_content(project_path):
    """ファイルシステムの内容を確認"""

    scrapy_projects_dir = Path("scrapy_projects")

    # 可能なパスパターンを確認
    possible_paths = [
        scrapy_projects_dir / project_path / project_path / "pipelines.py",
        scrapy_projects_dir / project_path / "pipelines.py",
    ]

    pipelines_file = None
    for path in possible_paths:
        if path.exists():
            pipelines_file = path
            break

    if pipelines_file:
        print(f'📄 pipelines.pyファイル発見: {pipelines_file}')

        try:
            with open(pipelines_file, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f'📊 ファイル内容分析:')
            print(f'   ファイルサイズ: {len(content)}文字')

            # 重要な要素をチェック
            has_scrapy_ui_pipeline = 'ScrapyUIDatabasePipeline' in content
            has_scrapy_ui_json_pipeline = 'ScrapyUIJSONPipeline' in content
            has_import_statement = 'from app.templates.database_pipeline import' in content

            print(f'   ScrapyUIDatabasePipeline: {"あり" if has_scrapy_ui_pipeline else "なし"}')
            print(f'   ScrapyUIJSONPipeline: {"あり" if has_scrapy_ui_json_pipeline else "なし"}')
            print(f'   インポート文: {"あり" if has_import_statement else "なし"}')

            return content

        except Exception as e:
            print(f'❌ ファイル読み取りエラー: {e}')
            return None
    else:
        print(f'❌ pipelines.pyファイルが見つかりません')
        print(f'   確認したパス:')
        for path in possible_paths:
            print(f'     - {path}')
        return None

def check_database_content(project_id):
    """データベースの内容を確認"""

    db_path = Path("backend/database/scrapy_ui.db")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # プロジェクトファイルを検索
        cursor.execute("""
            SELECT name, path, content, length(content) as content_length
            FROM project_files
            WHERE project_id = ? AND name = 'pipelines.py'
        """, (project_id,))

        result = cursor.fetchone()

        if result:
            name, path, content, content_length = result
            print(f'📄 データベース内pipelines.py発見:')
            print(f'   名前: {name}')
            print(f'   パス: {path}')
            print(f'   サイズ: {content_length}文字')

            # 内容をチェック
            has_scrapy_ui_pipeline = 'ScrapyUIDatabasePipeline' in content
            has_scrapy_ui_json_pipeline = 'ScrapyUIJSONPipeline' in content

            print(f'   ScrapyUIDatabasePipeline: {"あり" if has_scrapy_ui_pipeline else "なし"}')
            print(f'   ScrapyUIJSONPipeline: {"あり" if has_scrapy_ui_json_pipeline else "なし"}')

            return content
        else:
            print(f'❌ データベースにpipelines.pyが見つかりません')
            return None

        conn.close()

    except Exception as e:
        print(f"❌ データベースエラー: {e}")
        return None

def check_webui_content(project_id, headers):
    """WebUI APIの内容を確認"""

    # ファイル内容を取得
    response = requests.get(f'{BASE_URL}/api/projects/{project_id}/files/pipelines.py', headers=headers)

    if response.status_code == 200:
        file_data = response.json()
        content = file_data.get('content', '')

        print(f'📊 WebUI内容分析:')
        print(f'   ファイルサイズ: {len(content)}文字')

        # 重要な要素をチェック
        has_scrapy_ui_pipeline = 'ScrapyUIDatabasePipeline' in content
        has_scrapy_ui_json_pipeline = 'ScrapyUIJSONPipeline' in content

        print(f'   ScrapyUIDatabasePipeline: {"あり" if has_scrapy_ui_pipeline else "なし"}')
        print(f'   ScrapyUIJSONPipeline: {"あり" if has_scrapy_ui_json_pipeline else "なし"}')

        return content
    else:
        print(f'❌ WebUIファイル内容取得失敗: {response.status_code}')
        return None

def analyze_sync_status(filesystem_content, database_content, webui_content, db_save_enabled):
    """同期状況を分析"""

    print(f'📊 同期状況分析結果:')

    # ファイルシステム
    fs_has_scrapy_ui = 'ScrapyUIDatabasePipeline' in (filesystem_content or '')
    fs_size = len(filesystem_content) if filesystem_content else 0
    print(f'   ファイルシステム: {fs_size}文字, ScrapyUI={"あり" if fs_has_scrapy_ui else "なし"}')

    # データベース
    db_has_scrapy_ui = 'ScrapyUIDatabasePipeline' in (database_content or '')
    db_size = len(database_content) if database_content else 0
    print(f'   データベース: {db_size}文字, ScrapyUI={"あり" if db_has_scrapy_ui else "なし"}')

    # WebUI
    webui_has_scrapy_ui = 'ScrapyUIDatabasePipeline' in (webui_content or '')
    webui_size = len(webui_content) if webui_content else 0
    print(f'   WebUI: {webui_size}文字, ScrapyUI={"あり" if webui_has_scrapy_ui else "なし"}')

    # 期待値
    expected_has_scrapy_ui = db_save_enabled
    print(f'   期待値: ScrapyUI={"あり" if expected_has_scrapy_ui else "なし"} (DB保存{"有効" if db_save_enabled else "無効"})')

    # 同期状況
    fs_correct = fs_has_scrapy_ui == expected_has_scrapy_ui
    db_correct = db_has_scrapy_ui == expected_has_scrapy_ui
    webui_correct = webui_has_scrapy_ui == expected_has_scrapy_ui

    print(f'\n📋 正確性チェック:')
    print(f'   ファイルシステム: {"✅ 正しい" if fs_correct else "❌ 不正"}')
    print(f'   データベース: {"✅ 正しい" if db_correct else "❌ 不正"}')
    print(f'   WebUI: {"✅ 正しい" if webui_correct else "❌ 不正"}')

    # 同期チェック
    fs_db_sync = filesystem_content == database_content if filesystem_content and database_content else False
    db_webui_sync = database_content == webui_content if database_content and webui_content else False

    print(f'\n🔄 同期チェック:')
    print(f'   ファイルシステム ↔ データベース: {"✅ 同期" if fs_db_sync else "❌ 非同期"}')
    print(f'   データベース ↔ WebUI: {"✅ 同期" if db_webui_sync else "❌ 非同期"}')

def manual_sync_huhuhuh(project_id, project_path, user_id, db_save_enabled):
    """「huhuhuh」プロジェクトを手動同期"""

    print(f'🔄 手動同期開始: {project_path}')

    # ファイルシステムからpipelines.pyを読み取り
    scrapy_projects_dir = Path("scrapy_projects")
    possible_paths = [
        scrapy_projects_dir / project_path / project_path / "pipelines.py",
        scrapy_projects_dir / project_path / "pipelines.py",
    ]

    pipelines_file = None
    for path in possible_paths:
        if path.exists():
            pipelines_file = path
            break

    if not pipelines_file:
        print(f'❌ ファイルシステムにpipelines.pyが見つかりません')
        return False

    try:
        with open(pipelines_file, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f'📄 ファイル読み取り成功: {len(content)}文字')

        # データベースに直接更新
        db_path = Path("backend/database/scrapy_ui.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 既存のpipelines.pyを削除
        cursor.execute("""
            DELETE FROM project_files
            WHERE project_id = ? AND name = 'pipelines.py'
        """, (project_id,))

        deleted_count = cursor.rowcount
        print(f'🗑️ 既存ファイル削除: {deleted_count}件')

        # 新規作成
        import uuid
        cursor.execute("""
            INSERT INTO project_files
            (id, name, path, content, file_type, project_id, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            "pipelines.py",
            "pipelines.py",
            content,
            "python",
            project_id,
            user_id,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        print(f'✅ データベース新規作成成功')

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        print(f'❌ 手動同期エラー: {e}')
        return False

def main():
    """メイン実行関数"""
    print("🎯 「huhuhuh」プロジェクトのDB同期状況確認ツール")

    success = check_huhuhuh_sync()

    if success:
        print("\n🎉 確認完了！")
        print("\n🌐 WebUI確認:")
        print("  1. http://localhost:4000 にアクセス")
        print("  2. 「huhuhuh」プロジェクトを選択")
        print("  3. pipelines.pyファイルを開く")
        print("  4. 正しい内容が表示されることを確認")
    else:
        print("\n❌ 確認失敗")

if __name__ == "__main__":
    main()
