#!/usr/bin/env python3
"""
タスク統計情報修正スクリプト
データベースの実際の結果件数に基づいてタスクの統計情報を更新
"""
import sqlite3
from pathlib import Path
from datetime import datetime

def fix_task_statistics():
    """タスク統計情報を修正"""

    db_path = Path("backend/database/scrapy_ui.db")

    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        print("🔍 タスク統計情報修正開始")

        # 統計が不一致のタスクを検索
        cursor.execute("""
            SELECT
                t.id,
                s.name as spider_name,
                t.items_count as task_items_count,
                t.requests_count as task_requests_count,
                COUNT(r.id) as actual_results_count,
                t.status,
                t.started_at,
                t.finished_at
            FROM tasks t
            LEFT JOIN results r ON t.id = r.task_id
            LEFT JOIN spiders s ON t.spider_id = s.id
            GROUP BY t.id
            HAVING t.items_count != COUNT(r.id) OR COUNT(r.id) = 0
            ORDER BY t.created_at DESC
        """)

        mismatched_tasks = cursor.fetchall()

        print(f"📊 統計不一致タスク数: {len(mismatched_tasks)}件")

        if not mismatched_tasks:
            print("✅ 全てのタスクの統計情報は正常です")
            return True

        fixed_count = 0

        for task_id, spider_name, task_items, task_requests, actual_count, status, started_at, finished_at in mismatched_tasks:
            print(f"\n🔧 修正中: {task_id}")
            print(f"   スパイダー: {spider_name}")
            print(f"   現在のアイテム数: {task_items}")
            print(f"   実際の結果数: {actual_count}")
            print(f"   現在のリクエスト数: {task_requests}")
            print(f"   ステータス: {status}")

            if actual_count > 0:
                # 実際の結果数に基づいて統計を更新
                new_requests_count = max(actual_count + 10, task_requests or 0)

                cursor.execute("""
                    UPDATE tasks
                    SET items_count = ?,
                        requests_count = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (actual_count, new_requests_count, datetime.now().isoformat(), task_id))

                print(f"   ✅ 更新完了:")
                print(f"      新アイテム数: {actual_count}")
                print(f"      新リクエスト数: {new_requests_count}")

                fixed_count += 1
            else:
                print(f"   ⚠️ 結果が0件のためスキップ")

        # 変更をコミット
        conn.commit()

        print(f"\n🎉 修正完了: {fixed_count}件のタスクを更新しました")

        return True

    except Exception as e:
        print(f"❌ 修正エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def fix_specific_task(task_id: str):
    """特定のタスクの統計情報を修正"""

    db_path = Path("backend/database/scrapy_ui.db")

    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        print(f"🔍 タスク {task_id} の統計情報修正")

        # タスク情報を取得
        cursor.execute("""
            SELECT t.id, s.name as spider_name, t.items_count, t.requests_count, t.status, t.started_at, t.finished_at
            FROM tasks t
            LEFT JOIN spiders s ON t.spider_id = s.id
            WHERE t.id = ?
        """, (task_id,))

        task_info = cursor.fetchone()

        if not task_info:
            print(f"❌ タスクが見つかりません: {task_id}")
            return False

        task_id, spider_name, current_items, current_requests, status, started_at, finished_at = task_info

        # 実際の結果数を取得
        cursor.execute("SELECT COUNT(*) FROM results WHERE task_id = ?", (task_id,))
        actual_count = cursor.fetchone()[0]

        print(f"📋 タスク情報:")
        print(f"   ID: {task_id}")
        print(f"   スパイダー: {spider_name}")
        print(f"   現在のアイテム数: {current_items}")
        print(f"   実際の結果数: {actual_count}")
        print(f"   現在のリクエスト数: {current_requests}")
        print(f"   ステータス: {status}")

        if actual_count == current_items:
            print("✅ 統計情報は既に正しく設定されています")
            return True

        # 統計情報を更新
        new_requests_count = max(actual_count + 10, current_requests or 0)

        cursor.execute("""
            UPDATE tasks
            SET items_count = ?,
                requests_count = ?,
                updated_at = ?
            WHERE id = ?
        """, (actual_count, new_requests_count, datetime.now().isoformat(), task_id))

        # 変更をコミット
        conn.commit()

        print(f"\n✅ 修正完了:")
        print(f"   新アイテム数: {actual_count}")
        print(f"   新リクエスト数: {new_requests_count}")

        return True

    except Exception as e:
        print(f"❌ 修正エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def verify_task_statistics():
    """タスク統計情報の検証"""

    db_path = Path("backend/database/scrapy_ui.db")

    if not db_path.exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        print("🔍 タスク統計情報検証")

        # 全タスクの統計を確認
        cursor.execute("""
            SELECT
                t.id,
                s.name as spider_name,
                t.items_count as task_items_count,
                COUNT(r.id) as actual_results_count,
                t.status,
                CASE
                    WHEN t.items_count = COUNT(r.id) THEN '✅'
                    ELSE '❌'
                END as status_icon
            FROM tasks t
            LEFT JOIN results r ON t.id = r.task_id
            LEFT JOIN spiders s ON t.spider_id = s.id
            GROUP BY t.id
            ORDER BY t.created_at DESC
            LIMIT 10
        """)

        tasks = cursor.fetchall()

        print(f"\n📊 最新10タスクの統計確認:")
        print(f"{'ステータス':<4} {'タスクID':<36} {'スパイダー':<20} {'統計':<8} {'実際':<8}")
        print("-" * 80)

        correct_count = 0
        total_count = 0

        for task_id, spider_name, task_items, actual_count, status, status_icon in tasks:
            print(f"{status_icon:<4} {task_id:<36} {spider_name:<20} {task_items:<8} {actual_count:<8}")

            if task_items == actual_count:
                correct_count += 1
            total_count += 1

        print("-" * 80)
        print(f"正確な統計: {correct_count}/{total_count} ({correct_count/total_count*100:.1f}%)")

        # 不一致の詳細
        cursor.execute("""
            SELECT
                COUNT(*) as mismatched_count
            FROM tasks t
            LEFT JOIN results r ON t.id = r.task_id
            GROUP BY t.id
            HAVING t.items_count != COUNT(r.id)
        """)

        mismatched = cursor.fetchone()
        mismatched_count = mismatched[0] if mismatched else 0

        if mismatched_count > 0:
            print(f"\n⚠️ 統計不一致タスク: {mismatched_count}件")
        else:
            print(f"\n✅ 全てのタスクの統計情報が正確です")

        return mismatched_count == 0

    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """メイン実行関数"""
    print("🎯 タスク統計情報修正ツール\n")

    # 1. 現在の状況を確認
    print("1. 現在の統計情報を確認中...")
    verify_task_statistics()

    # 2. 特定のタスクを修正
    target_task_id = "43dcad37-334a-4b0b-9b8f-24ea1212bd39"
    print(f"\n2. 特定タスク {target_task_id} を修正中...")
    fix_specific_task(target_task_id)

    # 3. 全体の修正
    print(f"\n3. 全体の統計情報を修正中...")
    fix_task_statistics()

    # 4. 修正後の確認
    print(f"\n4. 修正後の統計情報を確認中...")
    verify_task_statistics()

    print("\n🎉 タスク統計情報修正完了！")
    print("\n📋 修正内容:")
    print("  - タスクのitems_countを実際の結果数に更新")
    print("  - requests_countを適切な値に調整")
    print("  - updated_atを現在時刻に更新")

if __name__ == "__main__":
    main()
