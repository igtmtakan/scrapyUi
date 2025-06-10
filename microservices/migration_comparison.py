#!/usr/bin/env python3
"""
ScrapyUI Migration Comparison Report
既存システムとマイクロサービスの比較分析
"""

import json
import requests
from datetime import datetime
from typing import Dict, List

def generate_comparison_report():
    """移行比較レポートの生成"""
    
    print("📊 ScrapyUI 移行比較レポート")
    print("=" * 60)
    print(f"生成日時: {datetime.now().isoformat()}")
    print()
    
    # 1. 既存システムの情報
    print("🔍 既存システム分析")
    print("-" * 30)
    
    try:
        with open('/tmp/existing_schedules.json', 'r') as f:
            existing_schedules = json.load(f)
        
        with open('/tmp/project_spider_data.json', 'r') as f:
            project_data = json.load(f)
        
        print(f"📋 既存スケジュール数: {len(existing_schedules)}")
        print(f"📁 プロジェクト数: {len(project_data['projects'])}")
        print(f"🕷️ スパイダー数: {len(project_data['spiders'])}")
        
        # スケジュール詳細
        print("\n📋 既存スケジュール詳細:")
        for schedule in existing_schedules:
            spider_info = project_data['spiders'].get(schedule['spider_id'], {})
            print(f"  • {schedule['name']}: {schedule['cron_expression']} ({spider_info.get('name', 'Unknown')})")
        
    except Exception as e:
        print(f"❌ 既存システム分析エラー: {e}")
    
    print()
    
    # 2. マイクロサービスの情報
    print("🚀 マイクロサービス分析")
    print("-" * 30)
    
    try:
        # メトリクス取得
        metrics_response = requests.get("http://localhost:8005/metrics")
        if metrics_response.status_code == 200:
            metrics = metrics_response.json()
            
            print(f"⏱️ 稼働時間: {metrics['uptime']:.1f}秒")
            print(f"📋 スケジュール数: {metrics['stats']['schedules']}")
            print(f"⚙️ タスク数: {metrics['stats']['tasks']}")
            print(f"📊 結果数: {metrics['stats']['results']}")
            
            if 'task_statuses' in metrics:
                print("\n📈 タスク状態分布:")
                for status, count in metrics['task_statuses'].items():
                    print(f"  • {status}: {count}個")
        
        # タスク詳細取得
        tasks_response = requests.get("http://localhost:8005/tasks")
        if tasks_response.status_code == 200:
            tasks = tasks_response.json()['tasks']
            
            print(f"\n⚙️ タスク実行履歴:")
            for task in tasks:
                duration = "計算中"
                if task.get('finished_at') and task.get('started_at'):
                    start = datetime.fromisoformat(task['started_at'])
                    end = datetime.fromisoformat(task['finished_at'])
                    duration = f"{(end - start).total_seconds():.1f}秒"
                
                print(f"  • {task['id']}: {task['status']} (実行時間: {duration})")
        
        # 結果詳細取得
        results_response = requests.get("http://localhost:8005/results")
        if results_response.status_code == 200:
            results = results_response.json()['results']
            
            print(f"\n📊 結果詳細:")
            total_items = 0
            total_pages = 0
            total_duration = 0
            
            for result in results:
                data = result['data']
                items = data.get('items', 0)
                pages = data.get('pages', 0)
                duration = data.get('duration', 0)
                
                total_items += items
                total_pages += pages
                total_duration += duration
                
                print(f"  • {result['id']}: {items}アイテム, {pages}ページ, {duration}秒")
            
            if results:
                avg_items = total_items / len(results)
                avg_pages = total_pages / len(results)
                avg_duration = total_duration / len(results)
                
                print(f"\n📈 平均値:")
                print(f"  • アイテム/タスク: {avg_items:.1f}")
                print(f"  • ページ/タスク: {avg_pages:.1f}")
                print(f"  • 実行時間/タスク: {avg_duration:.1f}秒")
        
    except Exception as e:
        print(f"❌ マイクロサービス分析エラー: {e}")
    
    print()
    
    # 3. 移行結果分析
    print("📊 移行結果分析")
    print("-" * 30)
    
    try:
        with open('/tmp/migration_report.json', 'r') as f:
            migration_report = json.load(f)
        
        stats = migration_report['migration_stats']
        
        print(f"⏱️ 移行実行時間: {stats['start_time']} ～ {stats['end_time']}")
        print(f"✅ 移行成功: {stats['schedules_migrated']}個")
        print(f"❌ 移行失敗: {stats['schedules_failed']}個")
        print(f"🚀 テストタスク作成: {stats['tasks_created']}個")
        print(f"📊 テスト結果生成: {stats['results_generated']}個")
        print(f"📈 成功率: {migration_report['success_rate']:.1f}%")
        
    except Exception as e:
        print(f"❌ 移行結果分析エラー: {e}")
    
    print()
    
    # 4. 比較分析
    print("🔍 システム比較分析")
    print("-" * 30)
    
    print("【アーキテクチャ比較】")
    print("既存システム:")
    print("  • モノリシック構造")
    print("  • Celery依存")
    print("  • 単一障害点あり")
    print("  • スケーリング困難")
    
    print("\nマイクロサービス:")
    print("  • サービス分離")
    print("  • 軽量HTTP API")
    print("  • 障害局所化")
    print("  • 水平スケーリング可能")
    
    print("\n【パフォーマンス比較】")
    print("既存システム:")
    print("  • Celery Worker不安定")
    print("  • メモリリーク問題")
    print("  • 復旧に時間要")
    
    print("\nマイクロサービス:")
    print("  • 安定した実行")
    print("  • 軽量プロセス")
    print("  • 高速復旧")
    
    print("\n【運用性比較】")
    print("既存システム:")
    print("  • 複雑な依存関係")
    print("  • デバッグ困難")
    print("  • 部分更新不可")
    
    print("\nマイクロサービス:")
    print("  • 独立デプロイ")
    print("  • 明確な責任分離")
    print("  • 段階的更新可能")
    
    print()
    
    # 5. 推奨事項
    print("💡 推奨事項")
    print("-" * 30)
    
    print("【短期的対応】")
    print("1. マイクロサービス環境の本格構築")
    print("2. Docker/Kubernetes環境整備")
    print("3. 監視・ログ基盤構築")
    
    print("\n【中期的対応】")
    print("1. 段階的移行計画策定")
    print("2. データ移行ツール開発")
    print("3. 運用手順書作成")
    
    print("\n【長期的対応】")
    print("1. 完全マイクロサービス化")
    print("2. 自動スケーリング実装")
    print("3. 高可用性構成実現")
    
    print()
    print("=" * 60)
    print("📊 レポート生成完了")

if __name__ == "__main__":
    generate_comparison_report()
