"""
使用統計サービス
機能利用状況の可視化と分析
"""
import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import uuid
from pathlib import Path


@dataclass
class UsageEvent:
    """使用イベント"""
    id: str
    user_id: str
    project_id: str
    event_type: str  # 'spider_run', 'file_edit', 'template_use', etc.
    event_category: str  # 'spider', 'file', 'template', 'git', etc.
    metadata: Dict[str, Any]
    timestamp: str
    session_id: str
    duration: Optional[float] = None


class UsageAnalytics:
    """使用統計分析クラス"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 統一データベースパスを使用
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = str(project_root / "backend" / "database" / "scrapy_ui.db")
        self.db_path = db_path
        self.active_sessions = {}
        self.init_database()
    
    def init_database(self):
        """データベースを初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_category TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL,
                duration REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                total_events INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # インデックス作成
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON usage_events(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_id ON usage_events(project_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON usage_events(event_type)')
        
        conn.commit()
        conn.close()
    
    def start_session(self, user_id: str, project_id: str) -> str:
        """セッションを開始"""
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'project_id': project_id,
            'start_time': timestamp,
            'event_count': 0
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_sessions (session_id, user_id, project_id, start_time)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user_id, project_id, timestamp))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def end_session(self, session_id: str):
        """セッションを終了"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        end_time = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions 
            SET end_time = ?, total_events = ?
            WHERE session_id = ?
        ''', (end_time, session['event_count'], session_id))
        
        conn.commit()
        conn.close()
        
        del self.active_sessions[session_id]
    
    def track_event(
        self,
        user_id: str,
        project_id: str,
        event_type: str,
        event_category: str,
        metadata: Dict[str, Any] = None,
        session_id: str = None,
        duration: float = None
    ) -> str:
        """イベントを追跡"""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        if not session_id:
            session_id = self.start_session(user_id, project_id)
        
        event = UsageEvent(
            id=event_id,
            user_id=user_id,
            project_id=project_id,
            event_type=event_type,
            event_category=event_category,
            metadata=metadata or {},
            timestamp=timestamp,
            session_id=session_id,
            duration=duration
        )
        
        # データベースに保存
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO usage_events 
            (id, user_id, project_id, event_type, event_category, metadata, timestamp, session_id, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.id, event.user_id, event.project_id, event.event_type,
            event.event_category, json.dumps(event.metadata), event.timestamp,
            event.session_id, event.duration
        ))
        
        conn.commit()
        conn.close()
        
        # セッション情報を更新
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['event_count'] += 1
        
        return event_id
    
    def get_usage_summary(self, project_id: str, days: int = 30) -> Dict[str, Any]:
        """使用統計サマリーを取得"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 基本統計
        cursor.execute('''
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT session_id) as total_sessions,
                AVG(duration) as avg_duration
            FROM usage_events 
            WHERE project_id = ? AND timestamp >= ? AND timestamp <= ?
        ''', (project_id, start_time.isoformat(), end_time.isoformat()))
        
        basic_stats = cursor.fetchone()
        
        # イベントタイプ別統計
        cursor.execute('''
            SELECT event_type, COUNT(*) as count
            FROM usage_events 
            WHERE project_id = ? AND timestamp >= ? AND timestamp <= ?
            GROUP BY event_type
            ORDER BY count DESC
        ''', (project_id, start_time.isoformat(), end_time.isoformat()))
        
        event_types = dict(cursor.fetchall())
        
        # カテゴリ別統計
        cursor.execute('''
            SELECT event_category, COUNT(*) as count
            FROM usage_events 
            WHERE project_id = ? AND timestamp >= ? AND timestamp <= ?
            GROUP BY event_category
            ORDER BY count DESC
        ''', (project_id, start_time.isoformat(), end_time.isoformat()))
        
        categories = dict(cursor.fetchall())
        
        # 日別統計
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as events,
                COUNT(DISTINCT user_id) as users
            FROM usage_events 
            WHERE project_id = ? AND timestamp >= ? AND timestamp <= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (project_id, start_time.isoformat(), end_time.isoformat()))
        
        daily_stats = [
            {'date': row[0], 'events': row[1], 'users': row[2]}
            for row in cursor.fetchall()
        ]
        
        # 時間別統計
        cursor.execute('''
            SELECT 
                strftime('%H', timestamp) as hour,
                COUNT(*) as events
            FROM usage_events 
            WHERE project_id = ? AND timestamp >= ? AND timestamp <= ?
            GROUP BY strftime('%H', timestamp)
            ORDER BY hour
        ''', (project_id, start_time.isoformat(), end_time.isoformat()))
        
        hourly_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'period': f"{days} days",
            'basic_stats': {
                'total_events': basic_stats[0] or 0,
                'unique_users': basic_stats[1] or 0,
                'total_sessions': basic_stats[2] or 0,
                'avg_duration': basic_stats[3] or 0
            },
            'event_types': event_types,
            'categories': categories,
            'daily_stats': daily_stats,
            'hourly_stats': hourly_stats
        }
    
    def get_user_activity(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """ユーザーアクティビティを取得"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ユーザーの基本統計
        cursor.execute('''
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT project_id) as projects_used,
                COUNT(DISTINCT session_id) as total_sessions,
                SUM(duration) as total_duration
            FROM usage_events 
            WHERE user_id = ? AND timestamp >= ? AND timestamp <= ?
        ''', (user_id, start_time.isoformat(), end_time.isoformat()))
        
        basic_stats = cursor.fetchone()
        
        # プロジェクト別統計
        cursor.execute('''
            SELECT project_id, COUNT(*) as events
            FROM usage_events 
            WHERE user_id = ? AND timestamp >= ? AND timestamp <= ?
            GROUP BY project_id
            ORDER BY events DESC
        ''', (user_id, start_time.isoformat(), end_time.isoformat()))
        
        project_stats = dict(cursor.fetchall())
        
        # 最も使用する機能
        cursor.execute('''
            SELECT event_type, COUNT(*) as count
            FROM usage_events 
            WHERE user_id = ? AND timestamp >= ? AND timestamp <= ?
            GROUP BY event_type
            ORDER BY count DESC
            LIMIT 10
        ''', (user_id, start_time.isoformat(), end_time.isoformat()))
        
        top_features = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'user_id': user_id,
            'period': f"{days} days",
            'basic_stats': {
                'total_events': basic_stats[0] or 0,
                'projects_used': basic_stats[1] or 0,
                'total_sessions': basic_stats[2] or 0,
                'total_duration': basic_stats[3] or 0
            },
            'project_stats': project_stats,
            'top_features': top_features
        }
    
    def get_feature_popularity(self, days: int = 30) -> Dict[str, Any]:
        """機能の人気度を取得"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 機能別使用統計
        cursor.execute('''
            SELECT 
                event_type,
                COUNT(*) as usage_count,
                COUNT(DISTINCT user_id) as unique_users,
                AVG(duration) as avg_duration
            FROM usage_events 
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY event_type
            ORDER BY usage_count DESC
        ''', (start_time.isoformat(), end_time.isoformat()))
        
        features = []
        for row in cursor.fetchall():
            features.append({
                'feature': row[0],
                'usage_count': row[1],
                'unique_users': row[2],
                'avg_duration': row[3] or 0,
                'popularity_score': row[1] * row[2]  # 使用回数 × ユニークユーザー数
            })
        
        # カテゴリ別統計
        cursor.execute('''
            SELECT 
                event_category,
                COUNT(*) as usage_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM usage_events 
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY event_category
            ORDER BY usage_count DESC
        ''', (start_time.isoformat(), end_time.isoformat()))
        
        categories = [
            {
                'category': row[0],
                'usage_count': row[1],
                'unique_users': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'period': f"{days} days",
            'features': features,
            'categories': categories
        }
    
    def generate_insights(self, project_id: str = None, days: int = 30) -> Dict[str, Any]:
        """インサイトを生成"""
        if project_id:
            summary = self.get_usage_summary(project_id, days)
        else:
            summary = self.get_feature_popularity(days)
        
        insights = {
            'trends': [],
            'recommendations': [],
            'alerts': []
        }
        
        # トレンド分析
        if project_id and summary['daily_stats']:
            recent_days = summary['daily_stats'][-7:]
            older_days = summary['daily_stats'][-14:-7] if len(summary['daily_stats']) >= 14 else []
            
            if older_days:
                recent_avg = sum(day['events'] for day in recent_days) / len(recent_days)
                older_avg = sum(day['events'] for day in older_days) / len(older_days)
                
                if recent_avg > older_avg * 1.2:
                    insights['trends'].append("使用量が増加傾向にあります")
                elif recent_avg < older_avg * 0.8:
                    insights['trends'].append("使用量が減少傾向にあります")
        
        # 推奨事項
        if project_id:
            event_types = summary['event_types']
            
            if 'spider_run' in event_types and event_types['spider_run'] > 100:
                insights['recommendations'].append("スパイダーの使用頻度が高いです。パフォーマンス最適化を検討してください。")
            
            if 'file_edit' in event_types and event_types['file_edit'] > 200:
                insights['recommendations'].append("ファイル編集が頻繁です。テンプレート機能の活用を検討してください。")
            
            if 'git_commit' not in event_types:
                insights['recommendations'].append("Git統合機能を使用してバージョン管理を始めることをお勧めします。")
        
        # アラート
        if project_id and summary['basic_stats']['unique_users'] == 0:
            insights['alerts'].append("最近のユーザーアクティビティがありません")
        
        return insights


# グローバルインスタンス
usage_analytics = UsageAnalytics()
