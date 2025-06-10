#!/usr/bin/env python3
"""
JSONLファイル管理ツール
大量に蓄積されたJSONLファイルを整理し、最新の実行結果のみを抽出
"""
import json
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

def analyze_jsonl_file(jsonl_path):
    """JSONLファイルを分析して実行セッションを特定"""
    print(f"🔍 Analyzing JSONL file: {jsonl_path}")
    
    sessions = defaultdict(list)
    total_lines = 0
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                scraped_at = data.get('scraped_at', '')
                
                if scraped_at:
                    # 時刻を分単位で丸めてセッションを特定
                    dt = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                    session_key = dt.strftime('%Y-%m-%d %H:%M')
                    sessions[session_key].append((line_num, data))
                
                total_lines += 1
                
                if line_num % 10000 == 0:
                    print(f"  処理中: {line_num:,} 行")
                    
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"  ⚠️ Error at line {line_num}: {e}")
                continue
    
    print(f"📊 分析結果:")
    print(f"  総行数: {total_lines:,}")
    print(f"  実行セッション数: {len(sessions)}")
    
    # セッションを時刻順でソート
    sorted_sessions = sorted(sessions.items(), key=lambda x: x[0], reverse=True)
    
    print(f"\n📅 最近の実行セッション:")
    for i, (session_key, items) in enumerate(sorted_sessions[:10]):
        print(f"  {i+1:2d}. {session_key} - {len(items):,} items")
    
    return sorted_sessions

def extract_latest_session(jsonl_path, output_path=None, session_index=0):
    """最新のセッションを抽出"""
    sessions = analyze_jsonl_file(jsonl_path)
    
    if not sessions:
        print("❌ No sessions found")
        return False
    
    if session_index >= len(sessions):
        print(f"❌ Session index {session_index} out of range (0-{len(sessions)-1})")
        return False
    
    session_key, items = sessions[session_index]
    print(f"\n🎯 Extracting session: {session_key} ({len(items):,} items)")
    
    if not output_path:
        output_path = f"ranking_results_latest_{session_key.replace(' ', '_').replace(':', '-')}.jsonl"
    
    # 最新セッションのデータを出力
    with open(output_path, 'w', encoding='utf-8') as f:
        for line_num, data in items:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    print(f"✅ Latest session extracted to: {output_path}")
    print(f"📊 Items: {len(items):,}")
    
    return output_path

def backup_and_clean_jsonl(jsonl_path, keep_sessions=3):
    """JSONLファイルをバックアップして最新のセッションのみを残す"""
    print(f"🔄 Backing up and cleaning: {jsonl_path}")
    
    # バックアップ作成
    backup_path = f"{jsonl_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(jsonl_path, backup_path)
    print(f"💾 Backup created: {backup_path}")
    
    # セッション分析
    sessions = analyze_jsonl_file(jsonl_path)
    
    if len(sessions) <= keep_sessions:
        print(f"✅ File already clean (only {len(sessions)} sessions)")
        return jsonl_path
    
    # 最新のセッションのみを保持
    keep_sessions_data = sessions[:keep_sessions]
    total_keep_items = sum(len(items) for _, items in keep_sessions_data)
    
    print(f"🧹 Keeping latest {keep_sessions} sessions ({total_keep_items:,} items)")
    
    # 新しいファイルを作成
    temp_path = f"{jsonl_path}.temp"
    with open(temp_path, 'w', encoding='utf-8') as f:
        for session_key, items in keep_sessions_data:
            print(f"  Writing session: {session_key} ({len(items):,} items)")
            for line_num, data in items:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    # 元ファイルを置換
    import os
    os.replace(temp_path, jsonl_path)
    
    print(f"✅ File cleaned: {jsonl_path}")
    print(f"📊 Reduced from {sum(len(items) for _, items in sessions):,} to {total_keep_items:,} items")
    
    return jsonl_path

def get_session_stats(jsonl_path):
    """セッション統計を取得"""
    sessions = analyze_jsonl_file(jsonl_path)
    
    print(f"\n📈 詳細統計:")
    for i, (session_key, items) in enumerate(sessions[:20]):
        if items:
            first_item = items[0][1]
            last_item = items[-1][1]
            
            start_time = first_item.get('scraped_at', '')
            end_time = last_item.get('scraped_at', '')
            
            print(f"  {i+1:2d}. {session_key}")
            print(f"      Items: {len(items):,}")
            print(f"      Start: {start_time}")
            print(f"      End:   {end_time}")
            print()

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='JSONL file manager')
    parser.add_argument('jsonl_file', help='Path to JSONL file')
    parser.add_argument('--analyze', action='store_true', help='Analyze file sessions')
    parser.add_argument('--extract-latest', action='store_true', help='Extract latest session')
    parser.add_argument('--session-index', type=int, default=0, help='Session index to extract (0=latest)')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--clean', action='store_true', help='Clean file (keep latest sessions only)')
    parser.add_argument('--keep-sessions', type=int, default=3, help='Number of sessions to keep when cleaning')
    parser.add_argument('--stats', action='store_true', help='Show detailed session statistics')
    
    args = parser.parse_args()
    
    jsonl_path = Path(args.jsonl_file)
    if not jsonl_path.exists():
        print(f"❌ File not found: {jsonl_path}")
        sys.exit(1)
    
    if args.analyze:
        analyze_jsonl_file(jsonl_path)
    elif args.extract_latest:
        extract_latest_session(jsonl_path, args.output, args.session_index)
    elif args.clean:
        backup_and_clean_jsonl(jsonl_path, args.keep_sessions)
    elif args.stats:
        get_session_stats(jsonl_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
