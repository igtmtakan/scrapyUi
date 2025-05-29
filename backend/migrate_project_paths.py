#!/usr/bin/env python3
"""
既存プロジェクトを新しい命名規則（<username>_<projectname>）に従って更新

このスクリプトは以下の処理を行います:
1. 既存プロジェクトのパスを新しい命名規則に更新
2. ファイルシステム上のディレクトリ名を変更
3. データベースのパス情報を更新
"""

import sqlite3
import os
import shutil
from pathlib import Path

def get_projects_to_update():
    """更新が必要なプロジェクトを取得"""
    conn = sqlite3.connect('database/scrapy_ui.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.name, p.path, p.user_id, u.username
        FROM projects p
        LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at
    ''')
    
    projects = cursor.fetchall()
    conn.close()
    
    updates_needed = []
    
    for project_id, name, current_path, user_id, username in projects:
        if username:
            # 新しい命名規則に従った推奨パス
            username_clean = username.lower().replace(' ', '_').replace('-', '_')
            name_clean = name.lower().replace(' ', '_').replace('-', '_')
            recommended_path = f'{username_clean}_{name_clean}'
            
            # 現在のパスと推奨パスが異なる場合は更新が必要
            if current_path != recommended_path:
                updates_needed.append({
                    'id': project_id,
                    'name': name,
                    'current_path': current_path,
                    'recommended_path': recommended_path,
                    'username': username
                })
    
    return updates_needed

def backup_database():
    """データベースのバックアップを作成"""
    db_path = Path('database/scrapy_ui.db')
    backup_path = db_path.with_suffix('.db.backup_paths')
    
    if db_path.exists():
        shutil.copy2(db_path, backup_path)
        print(f"✅ データベースバックアップ作成: {backup_path}")
        return True
    return False

def update_filesystem(current_path, new_path):
    """ファイルシステム上のディレクトリ名を変更"""
    scrapy_projects_dir = Path('scrapy_projects')
    current_dir = scrapy_projects_dir / current_path
    new_dir = scrapy_projects_dir / new_path
    
    if current_dir.exists():
        if new_dir.exists():
            print(f"⚠️  新しいディレクトリが既に存在: {new_dir}")
            return False
        
        try:
            shutil.move(str(current_dir), str(new_dir))
            print(f"✅ ディレクトリ移動: {current_path} → {new_path}")
            return True
        except Exception as e:
            print(f"❌ ディレクトリ移動失敗: {e}")
            return False
    else:
        print(f"⚠️  現在のディレクトリが存在しません: {current_dir}")
        return True  # ディレクトリが存在しない場合はDBのみ更新

def update_database(project_id, new_path):
    """データベースのパス情報を更新"""
    try:
        conn = sqlite3.connect('database/scrapy_ui.db')
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE projects SET path = ? WHERE id = ?',
            (new_path, project_id)
        )
        
        conn.commit()
        conn.close()
        print(f"✅ データベース更新: プロジェクトID {project_id}")
        return True
    except Exception as e:
        print(f"❌ データベース更新失敗: {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 60)
    print("既存プロジェクトの命名規則更新")
    print("=" * 60)
    
    # 更新が必要なプロジェクトを取得
    projects_to_update = get_projects_to_update()
    
    if not projects_to_update:
        print("✅ 全てのプロジェクトが既に正しい命名規則に従っています")
        return
    
    print(f"📋 更新が必要なプロジェクト: {len(projects_to_update)}個")
    print()
    
    for i, project in enumerate(projects_to_update, 1):
        print(f"{i}. {project['name']} ({project['username']})")
        print(f"   現在: {project['current_path']}")
        print(f"   新規: {project['recommended_path']}")
        print()
    
    # 確認
    response = input("これらのプロジェクトを更新しますか？ (y/N): ")
    if response.lower() != 'y':
        print("❌ 更新をキャンセルしました")
        return
    
    # データベースバックアップ
    if not backup_database():
        print("❌ データベースバックアップに失敗しました")
        return
    
    # 各プロジェクトを更新
    success_count = 0
    for project in projects_to_update:
        print(f"\n🔄 更新中: {project['name']}")
        
        # ファイルシステム更新
        fs_success = update_filesystem(
            project['current_path'], 
            project['recommended_path']
        )
        
        # データベース更新
        db_success = update_database(
            project['id'], 
            project['recommended_path']
        )
        
        if fs_success and db_success:
            success_count += 1
            print(f"✅ 更新完了: {project['name']}")
        else:
            print(f"❌ 更新失敗: {project['name']}")
    
    print(f"\n📊 更新結果: {success_count}/{len(projects_to_update)} 個のプロジェクトが正常に更新されました")
    
    if success_count == len(projects_to_update):
        print("🎉 全てのプロジェクトが正常に更新されました！")
    else:
        print("⚠️  一部のプロジェクトの更新に失敗しました")

if __name__ == "__main__":
    main()
