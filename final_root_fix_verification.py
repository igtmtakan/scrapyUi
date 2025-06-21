#!/usr/bin/env python3
"""
最終的な根本対応検証スクリプト

データベースから直接タスクデータを分析して、
根本対応が成功したかを検証します。
"""

import sys
import os
from datetime import datetime, timedelta

# ScrapyUIのパスを追加
sys.path.append('/home/igtmtakan/workplace/python/scrapyUI')

from backend.app.database import SessionLocal, Task, Result, TaskStatus


def analyze_task_statistics():
    """タスク統計の詳細分析"""
    print("🔍 Analyzing task statistics for root fix verification...")
    
    db = SessionLocal()
    try:
        # 最近48時間のタスクを取得
        cutoff_time = datetime.now() - timedelta(hours=48)
        all_tasks = db.query(Task).filter(
            Task.created_at >= cutoff_time
        ).order_by(Task.created_at.desc()).all()
        
        print(f"📋 Found {len(all_tasks)} tasks in last 48 hours")
        
        # ステータス別分析
        status_counts = {}
        for task in all_tasks:
            status = task.status.value if hasattr(task.status, 'value') else str(task.status)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\n📊 Task Status Distribution:")
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        
        # 完了タスクの詳細分析
        finished_tasks = [t for t in all_tasks if t.status == TaskStatus.FINISHED]
        print(f"\n🎯 Analyzing {len(finished_tasks)} FINISHED tasks:")
        
        zero_items_tasks = []
        proper_stats_tasks = []
        short_duration_tasks = []
        
        for task in finished_tasks:
            # 実行時間を計算
            duration = 0
            if task.started_at and task.finished_at:
                duration = (task.finished_at - task.started_at).total_seconds()
            
            # 短時間タスクの判定
            if duration < 10:
                short_duration_tasks.append(task)
            
            # 統計の分析
            if task.items_count == 0 and task.requests_count == 0:
                zero_items_tasks.append(task)
            elif task.items_count > 0 and task.requests_count > 0:
                proper_stats_tasks.append(task)
        
        print(f"   Zero Statistics Tasks: {len(zero_items_tasks)}")
        print(f"   Proper Statistics Tasks: {len(proper_stats_tasks)}")
        print(f"   Short Duration Tasks (<10s): {len(short_duration_tasks)}")
        
        return {
            'total_tasks': len(all_tasks),
            'finished_tasks': len(finished_tasks),
            'zero_stats_tasks': len(zero_items_tasks),
            'proper_stats_tasks': len(proper_stats_tasks),
            'short_duration_tasks': len(short_duration_tasks),
            'zero_tasks_list': zero_items_tasks,
            'short_tasks_list': short_duration_tasks
        }
        
    finally:
        db.close()


def analyze_short_duration_tasks(short_tasks):
    """短時間完了タスクの詳細分析"""
    print(f"\n🔬 Detailed analysis of {len(short_tasks)} short-duration tasks:")
    
    if not short_tasks:
        print("   No short-duration tasks found")
        return True
    
    fixed_count = 0
    problematic_count = 0
    
    for i, task in enumerate(short_tasks[:10]):  # 最初の10個を詳細分析
        duration = 0
        if task.started_at and task.finished_at:
            duration = (task.finished_at - task.started_at).total_seconds()
        
        has_proper_stats = task.items_count > 0 and task.requests_count > 0
        
        print(f"   Task {i+1}: {task.id[:12]}... | {duration:.1f}s | Items: {task.items_count} | Requests: {task.requests_count} | {'✅' if has_proper_stats else '❌'}")
        
        if has_proper_stats:
            fixed_count += 1
        else:
            problematic_count += 1
    
    print(f"\n📊 Short-Duration Task Analysis:")
    print(f"   Fixed Tasks: {fixed_count}")
    print(f"   Problematic Tasks: {problematic_count}")
    print(f"   Fix Rate: {(fixed_count/(fixed_count+problematic_count)*100):.1f}%" if (fixed_count+problematic_count) > 0 else "N/A")
    
    return problematic_count == 0


def check_before_after_comparison():
    """修正前後の比較"""
    print(f"\n📈 Before/After Comparison:")
    
    db = SessionLocal()
    try:
        # 修正前（24時間前より古い）のタスク
        before_cutoff = datetime.now() - timedelta(hours=24)
        before_tasks = db.query(Task).filter(
            Task.created_at < before_cutoff,
            Task.status == TaskStatus.FINISHED
        ).limit(50).all()
        
        # 修正後（最近24時間）のタスク
        after_tasks = db.query(Task).filter(
            Task.created_at >= before_cutoff,
            Task.status == TaskStatus.FINISHED
        ).all()
        
        def analyze_task_group(tasks, label):
            zero_stats = sum(1 for t in tasks if t.items_count == 0 and t.requests_count == 0)
            proper_stats = sum(1 for t in tasks if t.items_count > 0 and t.requests_count > 0)
            total = len(tasks)
            
            print(f"   {label}:")
            print(f"     Total Tasks: {total}")
            print(f"     Zero Statistics: {zero_stats} ({(zero_stats/total*100):.1f}%)" if total > 0 else "     Zero Statistics: 0")
            print(f"     Proper Statistics: {proper_stats} ({(proper_stats/total*100):.1f}%)" if total > 0 else "     Proper Statistics: 0")
            
            return zero_stats, proper_stats, total
        
        before_zero, before_proper, before_total = analyze_task_group(before_tasks, "Before Fix (>24h ago)")
        after_zero, after_proper, after_total = analyze_task_group(after_tasks, "After Fix (last 24h)")
        
        # 改善度を計算
        if before_total > 0 and after_total > 0:
            before_zero_rate = before_zero / before_total * 100
            after_zero_rate = after_zero / after_total * 100
            improvement = before_zero_rate - after_zero_rate
            
            print(f"\n📊 Improvement Analysis:")
            print(f"   Zero Statistics Rate Reduction: {improvement:.1f} percentage points")
            print(f"   Fix Effectiveness: {'✅ Significant' if improvement > 10 else '⚠️ Moderate' if improvement > 0 else '❌ No improvement'}")
            
            return improvement > 0
        
        return False
        
    finally:
        db.close()


def run_immediate_updater_test():
    """即座統計更新サービスのテスト"""
    print(f"\n🧪 Testing immediate statistics updater...")
    
    try:
        from backend.app.services.immediate_task_statistics_updater import immediate_updater
        
        # 最近の問題タスクを検索
        db = SessionLocal()
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            problematic_tasks = db.query(Task).filter(
                Task.created_at >= cutoff_time,
                Task.status == TaskStatus.FINISHED,
                Task.items_count == 0
            ).limit(5).all()
            
            if not problematic_tasks:
                print("   ✅ No problematic tasks found - fix is working!")
                return True
            
            print(f"   Found {len(problematic_tasks)} problematic tasks to fix")
            
            # 即座統計更新を実行
            result = immediate_updater.batch_update_recent_tasks(hours_back=24)
            
            print(f"   Batch update result: {result.get('updated_tasks', 0)}/{result.get('total_tasks', 0)} tasks updated")
            
            return result.get('updated_tasks', 0) > 0
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"   ❌ Error testing immediate updater: {e}")
        return False


def main():
    """メイン検証実行"""
    print("🎯 Final Root Cause Fix Verification")
    print("=" * 60)
    print("This comprehensive test will verify that the root cause fix")
    print("for task_175-type problems (zero items/requests) is working.")
    print("=" * 60)
    
    try:
        # 1. 全体的なタスク統計分析
        stats = analyze_task_statistics()
        
        # 2. 短時間完了タスクの詳細分析
        short_tasks_ok = analyze_short_duration_tasks(stats['short_tasks_list'])
        
        # 3. 修正前後の比較
        improvement_ok = check_before_after_comparison()
        
        # 4. 即座統計更新サービスのテスト
        updater_ok = run_immediate_updater_test()
        
        # 5. 最終判定
        print("\n" + "=" * 60)
        print("🎯 FINAL ROOT CAUSE FIX VERIFICATION RESULTS:")
        print("=" * 60)
        
        # 成功条件の評価
        zero_rate = stats['zero_stats_tasks'] / stats['finished_tasks'] * 100 if stats['finished_tasks'] > 0 else 0
        proper_rate = stats['proper_stats_tasks'] / stats['finished_tasks'] * 100 if stats['finished_tasks'] > 0 else 0
        
        print(f"📊 Overall Statistics:")
        print(f"   Total Finished Tasks: {stats['finished_tasks']}")
        print(f"   Zero Statistics Rate: {zero_rate:.1f}%")
        print(f"   Proper Statistics Rate: {proper_rate:.1f}%")
        
        print(f"\n🔍 Verification Results:")
        print(f"   ✅ Short-Duration Tasks Fixed: {'Yes' if short_tasks_ok else 'No'}")
        print(f"   ✅ Overall Improvement: {'Yes' if improvement_ok else 'No'}")
        print(f"   ✅ Updater Service Working: {'Yes' if updater_ok else 'No'}")
        
        # 最終判定
        if zero_rate < 10 and proper_rate > 80:
            print(f"\n🎉 ROOT CAUSE FIX: FULLY SUCCESSFUL!")
            print(f"   ✅ Zero statistics rate is very low ({zero_rate:.1f}%)")
            print(f"   ✅ Proper statistics rate is high ({proper_rate:.1f}%)")
            print(f"   ✅ The task_175-type problem is resolved!")
        elif zero_rate < 30 and proper_rate > 60:
            print(f"\n✅ ROOT CAUSE FIX: MOSTLY SUCCESSFUL!")
            print(f"   ✅ Significant improvement in task statistics")
            print(f"   ⚠️ Some edge cases may still exist")
        else:
            print(f"\n❌ ROOT CAUSE FIX: NEEDS FURTHER WORK!")
            print(f"   ❌ Zero statistics rate is still high ({zero_rate:.1f}%)")
            print(f"   ❌ More investigation needed")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
