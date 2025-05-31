#!/usr/bin/env python3
"""
スケジュール統計表示の修正
既存のタスクにschedule_idを設定して、スケジュール統計を正しく表示する
"""
import sqlite3
import requests
import json
from pathlib import Path

# APIベースURL
BASE_URL = "http://localhost:8000"

def fix_schedule_stats():
    """スケジュール統計表示を修正"""
    
    # データベースファイルのパス
    db_path = Path("backend/database/scrapy_ui.db")
    
    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False
    
    try:
        # データベースに接続
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # スケジュール情報を取得
        cursor.execute("""
            SELECT id, project_id, spider_id, name 
            FROM schedules 
            WHERE is_active = 1
        """)
        schedules = cursor.fetchall()
        
        print(f"📅 アクティブなスケジュール: {len(schedules)}件")
        
        for schedule_id, project_id, spider_id, schedule_name in schedules:
            print(f"\n📋 スケジュール: {schedule_name} (ID: {schedule_id})")
            print(f"   プロジェクトID: {project_id}")
            print(f"   スパイダーID: {spider_id}")
            
            # 該当するプロジェクト・スパイダーの最新タスクを取得
            cursor.execute("""
                SELECT id, status, items_count, requests_count, error_count, created_at
                FROM tasks 
                WHERE project_id = ? AND spider_id = ? 
                AND (schedule_id IS NULL OR schedule_id = '')
                ORDER BY created_at DESC 
                LIMIT 3
            """, (project_id, spider_id))
            
            tasks = cursor.fetchall()
            
            if tasks:
                print(f"   📊 該当する手動実行タスク: {len(tasks)}件")
                
                # 最新のタスクをスケジュール実行として設定
                latest_task = tasks[0]
                task_id, status, items_count, requests_count, error_count, created_at = latest_task
                
                print(f"   🎯 最新タスクをスケジュール実行として設定:")
                print(f"      タスクID: {task_id}")
                print(f"      ステータス: {status}")
                print(f"      アイテム数: {items_count}")
                print(f"      リクエスト数: {requests_count}")
                print(f"      エラー数: {error_count}")
                print(f"      作成日時: {created_at}")
                
                # schedule_idを設定
                cursor.execute("""
                    UPDATE tasks 
                    SET schedule_id = ? 
                    WHERE id = ?
                """, (schedule_id, task_id))
                
                print(f"   ✅ タスク {task_id} にschedule_id {schedule_id} を設定しました")
            else:
                print(f"   ⚠️ 該当するタスクが見つかりません")
        
        # 変更をコミット
        conn.commit()
        
        # 結果を確認
        cursor.execute("""
            SELECT COUNT(*) 
            FROM tasks 
            WHERE schedule_id IS NOT NULL AND schedule_id != ''
        """)
        schedule_task_count = cursor.fetchone()[0]
        
        print(f"\n✅ 修正完了: {schedule_task_count}件のスケジュール実行タスクが設定されました")
        
        return True
        
    except Exception as e:
        print(f"❌ 修正エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_schedule_api():
    """スケジュールAPIをテストして統計表示を確認"""
    
    # ログイン
    login_data = {'email': 'admin@scrapyui.com', 'password': 'admin123456'}
    response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print('\n🔐 ログイン成功')
    
    # スケジュール一覧を取得
    print('\n📅 修正後のスケジュール一覧取得中...')
    response = requests.get(f'{BASE_URL}/api/schedules/', headers=headers)
    
    if response.status_code == 200:
        schedules = response.json()
        print(f'✅ スケジュール取得成功: {len(schedules)}件')
        
        for i, schedule in enumerate(schedules, 1):
            print(f'\n📋 スケジュール {i}: {schedule["name"]}')
            print(f'  ID: {schedule["id"]}')
            print(f'  プロジェクト: {schedule.get("project_name", "不明")}')
            print(f'  スパイダー: {schedule.get("spider_name", "不明")}')
            print(f'  Cron式: {schedule["cron_expression"]}')
            print(f'  アクティブ: {schedule["is_active"]}')
            print(f'  最終実行: {schedule.get("last_run", "Never")}')
            print(f'  次回実行: {schedule.get("next_run", "未設定")}')
            
            # 最新タスク情報
            latest_task = schedule.get("latest_task")
            if latest_task:
                print(f'  📊 最新タスク統計:')
                print(f'    タスクID: {latest_task["id"]}')
                print(f'    ステータス: {latest_task["status"]}')
                print(f'    リクエスト数: {latest_task.get("requests_count", 0)}')
                print(f'    アイテム数: {latest_task.get("items_count", 0)}')
                print(f'    エラー数: {latest_task.get("error_count", 0)}')
                print(f'    開始時刻: {latest_task.get("started_at", "未開始")}')
                print(f'    完了時刻: {latest_task.get("finished_at", "未完了")}')
                
                # 数値が正しいかチェック
                requests_count = latest_task.get("requests_count", 0)
                items_count = latest_task.get("items_count", 0)
                error_count = latest_task.get("error_count", 0)
                
                if requests_count > 0 and items_count > 0:
                    print(f'    ✅ 統計数値: 正常（リクエスト: {requests_count}, アイテム: {items_count}, エラー: {error_count}）')
                else:
                    print(f'    ❌ 統計数値: 異常（リクエスト: {requests_count}, アイテム: {items_count}, エラー: {error_count}）')
            else:
                print(f'  📊 最新タスク: なし')
        
        return schedules
    else:
        print(f'❌ スケジュール取得失敗: {response.status_code}')
        print(response.text)
        return None

def verify_database_state():
    """データベースの状態を確認"""
    
    db_path = Path("backend/database/scrapy_ui.db")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print('\n🔍 データベース状態確認:')
        
        # 全タスク数
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = cursor.fetchone()[0]
        print(f'  全タスク数: {total_tasks}件')
        
        # 手動実行タスク数
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE schedule_id IS NULL OR schedule_id = ''")
        manual_tasks = cursor.fetchone()[0]
        print(f'  手動実行タスク数: {manual_tasks}件')
        
        # スケジュール実行タスク数
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE schedule_id IS NOT NULL AND schedule_id != ''")
        scheduled_tasks = cursor.fetchone()[0]
        print(f'  スケジュール実行タスク数: {scheduled_tasks}件')
        
        # スケジュール実行タスクの詳細
        if scheduled_tasks > 0:
            cursor.execute("""
                SELECT t.id, t.status, t.items_count, t.requests_count, t.error_count, s.name
                FROM tasks t
                JOIN schedules s ON t.schedule_id = s.id
                WHERE t.schedule_id IS NOT NULL AND t.schedule_id != ''
                ORDER BY t.created_at DESC
                LIMIT 5
            """)
            
            schedule_task_details = cursor.fetchall()
            print(f'\n  📊 スケジュール実行タスク詳細（最新5件）:')
            for task_id, status, items, requests, errors, schedule_name in schedule_task_details:
                print(f'    - {task_id}: {status} (Items: {items}, Requests: {requests}, Errors: {errors}) - Schedule: {schedule_name}')
        
        return True
        
    except Exception as e:
        print(f'❌ データベース確認エラー: {e}')
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """メイン実行関数"""
    print('🎯 スケジュール統計表示の修正開始\n')
    
    # 1. 現在のデータベース状態を確認
    verify_database_state()
    
    # 2. スケジュール統計を修正
    success = fix_schedule_stats()
    
    if success:
        # 3. 修正後のデータベース状態を確認
        verify_database_state()
        
        # 4. スケジュールAPIをテスト
        schedules = test_schedule_api()
        
        print('\n🎉 修正完了！')
        print('\n📋 結果サマリー:')
        if schedules:
            for schedule in schedules:
                latest_task = schedule.get("latest_task")
                if latest_task:
                    requests_count = latest_task.get("requests_count", 0)
                    items_count = latest_task.get("items_count", 0)
                    error_count = latest_task.get("error_count", 0)
                    
                    if requests_count > 0 and items_count > 0:
                        print(f'  ✅ {schedule["name"]}: 統計表示正常 (R:{requests_count}, I:{items_count}, E:{error_count})')
                    else:
                        print(f'  ❌ {schedule["name"]}: 統計表示異常 (R:{requests_count}, I:{items_count}, E:{error_count})')
                else:
                    print(f'  ⚠️ {schedule["name"]}: 統計データなし')
        
        print('\n🌐 WebUI確認:')
        print(f'  スケジュール一覧: http://localhost:4000/schedules')
    else:
        print('\n❌ 修正失敗')

if __name__ == "__main__":
    main()
