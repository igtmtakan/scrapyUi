"""
パフォーマンス監視サービス
リアルタイム性能分析とメトリクス収集
"""
import asyncio
import time
import psutil
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
from collections import defaultdict, deque
import threading


@dataclass
class PerformanceMetric:
    """パフォーマンスメトリクス"""
    timestamp: str
    project_id: str
    spider_name: Optional[str]
    metric_type: str  # 'cpu', 'memory', 'network', 'scrapy'
    value: float
    unit: str
    metadata: Dict[str, Any]


@dataclass
class ScrapyMetrics:
    """Scrapyメトリクス"""
    items_scraped: int = 0
    requests_sent: int = 0
    responses_received: int = 0
    errors_count: int = 0
    avg_response_time: float = 0.0
    pages_per_minute: float = 0.0
    success_rate: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0


class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self, db_path: str = "performance_metrics.db"):
        self.db_path = db_path
        self.metrics_buffer = deque(maxlen=1000)
        self.active_monitors = {}
        self.scrapy_stats = defaultdict(ScrapyMetrics)
        self.init_database()
        
    def init_database(self):
        """データベースを初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                project_id TEXT NOT NULL,
                spider_name TEXT,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON performance_metrics(timestamp);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_project_id ON performance_metrics(project_id);
        ''')
        
        conn.commit()
        conn.close()
    
    def start_monitoring(self, project_id: str, spider_name: str = None):
        """監視を開始"""
        monitor_key = f"{project_id}:{spider_name or 'global'}"
        
        if monitor_key not in self.active_monitors:
            self.active_monitors[monitor_key] = {
                'project_id': project_id,
                'spider_name': spider_name,
                'start_time': time.time(),
                'running': True
            }
            
            # 監視スレッドを開始
            thread = threading.Thread(
                target=self._monitor_loop,
                args=(project_id, spider_name),
                daemon=True
            )
            thread.start()
    
    def stop_monitoring(self, project_id: str, spider_name: str = None):
        """監視を停止"""
        monitor_key = f"{project_id}:{spider_name or 'global'}"
        
        if monitor_key in self.active_monitors:
            self.active_monitors[monitor_key]['running'] = False
            del self.active_monitors[monitor_key]
    
    def _monitor_loop(self, project_id: str, spider_name: str = None):
        """監視ループ"""
        monitor_key = f"{project_id}:{spider_name or 'global'}"
        
        while self.active_monitors.get(monitor_key, {}).get('running', False):
            try:
                # システムメトリクスを収集
                self._collect_system_metrics(project_id, spider_name)
                
                # Scrapyメトリクスを収集（該当する場合）
                if spider_name:
                    self._collect_scrapy_metrics(project_id, spider_name)
                
                # 5秒間隔で監視
                time.sleep(5)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(10)
    
    def _collect_system_metrics(self, project_id: str, spider_name: str = None):
        """システムメトリクスを収集"""
        timestamp = datetime.now().isoformat()
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self._add_metric(PerformanceMetric(
            timestamp=timestamp,
            project_id=project_id,
            spider_name=spider_name,
            metric_type='cpu',
            value=cpu_percent,
            unit='percent',
            metadata={'cores': psutil.cpu_count()}
        ))
        
        # メモリ使用率
        memory = psutil.virtual_memory()
        self._add_metric(PerformanceMetric(
            timestamp=timestamp,
            project_id=project_id,
            spider_name=spider_name,
            metric_type='memory',
            value=memory.percent,
            unit='percent',
            metadata={
                'total': memory.total,
                'available': memory.available,
                'used': memory.used
            }
        ))
        
        # ディスク使用率
        disk = psutil.disk_usage('/')
        self._add_metric(PerformanceMetric(
            timestamp=timestamp,
            project_id=project_id,
            spider_name=spider_name,
            metric_type='disk',
            value=disk.percent,
            unit='percent',
            metadata={
                'total': disk.total,
                'free': disk.free,
                'used': disk.used
            }
        ))
        
        # ネットワーク統計
        network = psutil.net_io_counters()
        self._add_metric(PerformanceMetric(
            timestamp=timestamp,
            project_id=project_id,
            spider_name=spider_name,
            metric_type='network',
            value=network.bytes_sent + network.bytes_recv,
            unit='bytes',
            metadata={
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
        ))
    
    def _collect_scrapy_metrics(self, project_id: str, spider_name: str):
        """Scrapyメトリクスを収集"""
        # ここでScrapyの統計情報を収集
        # 実際の実装では、Scrapyのstats collectorから情報を取得
        stats = self.scrapy_stats[f"{project_id}:{spider_name}"]
        timestamp = datetime.now().isoformat()
        
        metrics = [
            ('items_scraped', stats.items_scraped, 'count'),
            ('requests_sent', stats.requests_sent, 'count'),
            ('responses_received', stats.responses_received, 'count'),
            ('errors_count', stats.errors_count, 'count'),
            ('avg_response_time', stats.avg_response_time, 'seconds'),
            ('pages_per_minute', stats.pages_per_minute, 'rate'),
            ('success_rate', stats.success_rate, 'percent'),
        ]
        
        for metric_name, value, unit in metrics:
            self._add_metric(PerformanceMetric(
                timestamp=timestamp,
                project_id=project_id,
                spider_name=spider_name,
                metric_type=f'scrapy_{metric_name}',
                value=value,
                unit=unit,
                metadata={'spider': spider_name}
            ))
    
    def _add_metric(self, metric: PerformanceMetric):
        """メトリクスを追加"""
        self.metrics_buffer.append(metric)
        
        # データベースに保存（バッチ処理）
        if len(self.metrics_buffer) >= 50:
            self._flush_metrics()
    
    def _flush_metrics(self):
        """メトリクスをデータベースに保存"""
        if not self.metrics_buffer:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metrics_to_insert = []
        while self.metrics_buffer:
            metric = self.metrics_buffer.popleft()
            metrics_to_insert.append((
                metric.timestamp,
                metric.project_id,
                metric.spider_name,
                metric.metric_type,
                metric.value,
                metric.unit,
                json.dumps(metric.metadata)
            ))
        
        cursor.executemany('''
            INSERT INTO performance_metrics 
            (timestamp, project_id, spider_name, metric_type, value, unit, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', metrics_to_insert)
        
        conn.commit()
        conn.close()
    
    def get_metrics(
        self,
        project_id: str,
        metric_type: str = None,
        spider_name: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000
    ) -> List[Dict]:
        """メトリクスを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM performance_metrics WHERE project_id = ?"
        params = [project_id]
        
        if metric_type:
            query += " AND metric_type = ?"
            params.append(metric_type)
        
        if spider_name:
            query += " AND spider_name = ?"
            params.append(spider_name)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        metrics = []
        
        for row in rows:
            metric_dict = dict(zip(columns, row))
            if metric_dict['metadata']:
                metric_dict['metadata'] = json.loads(metric_dict['metadata'])
            metrics.append(metric_dict)
        
        conn.close()
        return metrics
    
    def get_real_time_stats(self, project_id: str) -> Dict[str, Any]:
        """リアルタイム統計を取得"""
        now = datetime.now()
        last_5_minutes = now - timedelta(minutes=5)
        
        metrics = self.get_metrics(
            project_id=project_id,
            start_time=last_5_minutes,
            end_time=now
        )
        
        stats = {
            'cpu_avg': 0,
            'memory_avg': 0,
            'disk_usage': 0,
            'network_throughput': 0,
            'active_spiders': 0,
            'total_requests': 0,
            'success_rate': 0,
            'avg_response_time': 0
        }
        
        cpu_values = []
        memory_values = []
        
        for metric in metrics:
            if metric['metric_type'] == 'cpu':
                cpu_values.append(metric['value'])
            elif metric['metric_type'] == 'memory':
                memory_values.append(metric['value'])
            elif metric['metric_type'] == 'scrapy_requests_sent':
                stats['total_requests'] += metric['value']
            elif metric['metric_type'] == 'scrapy_success_rate':
                stats['success_rate'] = metric['value']
            elif metric['metric_type'] == 'scrapy_avg_response_time':
                stats['avg_response_time'] = metric['value']
        
        if cpu_values:
            stats['cpu_avg'] = sum(cpu_values) / len(cpu_values)
        if memory_values:
            stats['memory_avg'] = sum(memory_values) / len(memory_values)
        
        # アクティブなスパイダー数
        stats['active_spiders'] = len([
            k for k in self.active_monitors.keys() 
            if k.startswith(f"{project_id}:")
        ])
        
        return stats
    
    def update_scrapy_stats(self, project_id: str, spider_name: str, stats_data: Dict):
        """Scrapy統計を更新"""
        key = f"{project_id}:{spider_name}"
        stats = self.scrapy_stats[key]
        
        stats.items_scraped = stats_data.get('item_scraped_count', 0)
        stats.requests_sent = stats_data.get('downloader/request_count', 0)
        stats.responses_received = stats_data.get('downloader/response_count', 0)
        stats.errors_count = stats_data.get('spider_exceptions', 0)
        
        if stats.requests_sent > 0:
            stats.success_rate = (stats.responses_received / stats.requests_sent) * 100
        
        # 平均レスポンス時間の計算
        response_times = stats_data.get('downloader/response_time', [])
        if response_times:
            stats.avg_response_time = sum(response_times) / len(response_times)
        
        # ページ/分の計算
        monitor_info = self.active_monitors.get(key, {})
        if monitor_info:
            elapsed_time = time.time() - monitor_info['start_time']
            if elapsed_time > 0:
                stats.pages_per_minute = (stats.responses_received / elapsed_time) * 60
    
    def generate_performance_report(self, project_id: str, days: int = 7) -> Dict[str, Any]:
        """パフォーマンスレポートを生成"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        metrics = self.get_metrics(
            project_id=project_id,
            start_time=start_time,
            end_time=end_time
        )
        
        report = {
            'period': f"{days} days",
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'summary': {
                'total_metrics': len(metrics),
                'avg_cpu': 0,
                'avg_memory': 0,
                'peak_cpu': 0,
                'peak_memory': 0,
                'total_requests': 0,
                'total_items': 0,
                'avg_success_rate': 0
            },
            'trends': {},
            'recommendations': []
        }
        
        # メトリクス分析
        cpu_values = []
        memory_values = []
        success_rates = []
        
        for metric in metrics:
            if metric['metric_type'] == 'cpu':
                cpu_values.append(metric['value'])
            elif metric['metric_type'] == 'memory':
                memory_values.append(metric['value'])
            elif metric['metric_type'] == 'scrapy_success_rate':
                success_rates.append(metric['value'])
            elif metric['metric_type'] == 'scrapy_requests_sent':
                report['summary']['total_requests'] += metric['value']
            elif metric['metric_type'] == 'scrapy_items_scraped':
                report['summary']['total_items'] += metric['value']
        
        if cpu_values:
            report['summary']['avg_cpu'] = sum(cpu_values) / len(cpu_values)
            report['summary']['peak_cpu'] = max(cpu_values)
        
        if memory_values:
            report['summary']['avg_memory'] = sum(memory_values) / len(memory_values)
            report['summary']['peak_memory'] = max(memory_values)
        
        if success_rates:
            report['summary']['avg_success_rate'] = sum(success_rates) / len(success_rates)
        
        # 推奨事項の生成
        if report['summary']['avg_cpu'] > 80:
            report['recommendations'].append("CPU使用率が高いです。並行リクエスト数を減らすことを検討してください。")
        
        if report['summary']['avg_memory'] > 85:
            report['recommendations'].append("メモリ使用率が高いです。メモリリークの可能性を確認してください。")
        
        if report['summary']['avg_success_rate'] < 90:
            report['recommendations'].append("成功率が低いです。エラーハンドリングとリトライ設定を見直してください。")
        
        return report


# グローバルインスタンス
performance_monitor = PerformanceMonitor()
