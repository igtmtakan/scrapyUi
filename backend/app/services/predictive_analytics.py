"""
予測分析サービス
将来の問題予測と傾向分析
"""
import numpy as np
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import json
import math


@dataclass
class Prediction:
    """予測結果"""
    metric_name: str
    current_value: float
    predicted_value: float
    confidence: float
    trend: str  # 'increasing', 'decreasing', 'stable'
    risk_level: str  # 'low', 'medium', 'high'
    recommendations: List[str]


@dataclass
class Anomaly:
    """異常検知結果"""
    timestamp: str
    metric_name: str
    value: float
    expected_value: float
    deviation: float
    severity: str  # 'low', 'medium', 'high'
    description: str


class PredictiveAnalytics:
    """予測分析クラス"""
    
    def __init__(self, performance_db: str = "performance_metrics.db", usage_db: str = "usage_analytics.db"):
        self.performance_db = performance_db
        self.usage_db = usage_db
    
    def predict_performance_issues(self, project_id: str, days_ahead: int = 7) -> List[Prediction]:
        """パフォーマンス問題を予測"""
        predictions = []
        
        # 過去30日のデータを取得
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        metrics_data = self._get_performance_metrics(project_id, start_time, end_time)
        
        # 各メトリクスについて予測を実行
        for metric_type in ['cpu', 'memory', 'disk', 'scrapy_success_rate']:
            if metric_type in metrics_data:
                prediction = self._predict_metric(metric_type, metrics_data[metric_type], days_ahead)
                if prediction:
                    predictions.append(prediction)
        
        return predictions
    
    def detect_anomalies(self, project_id: str, hours: int = 24) -> List[Anomaly]:
        """異常を検知"""
        anomalies = []
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        metrics_data = self._get_performance_metrics(project_id, start_time, end_time)
        
        for metric_type, values in metrics_data.items():
            metric_anomalies = self._detect_metric_anomalies(metric_type, values)
            anomalies.extend(metric_anomalies)
        
        return anomalies
    
    def predict_resource_usage(self, project_id: str) -> Dict[str, Any]:
        """リソース使用量を予測"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=14)
        
        metrics_data = self._get_performance_metrics(project_id, start_time, end_time)
        
        predictions = {
            'cpu': self._predict_resource_trend('cpu', metrics_data.get('cpu', [])),
            'memory': self._predict_resource_trend('memory', metrics_data.get('memory', [])),
            'disk': self._predict_resource_trend('disk', metrics_data.get('disk', [])),
            'network': self._predict_resource_trend('network', metrics_data.get('network', []))
        }
        
        # 総合的なリスク評価
        risk_score = self._calculate_overall_risk(predictions)
        
        return {
            'predictions': predictions,
            'risk_score': risk_score,
            'recommendations': self._generate_resource_recommendations(predictions)
        }
    
    def predict_spider_performance(self, project_id: str, spider_name: str) -> Dict[str, Any]:
        """スパイダーパフォーマンスを予測"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        spider_metrics = self._get_spider_metrics(project_id, spider_name, start_time, end_time)
        
        predictions = {}
        
        # 成功率の予測
        if 'success_rate' in spider_metrics:
            success_trend = self._analyze_trend(spider_metrics['success_rate'])
            predictions['success_rate'] = {
                'current': spider_metrics['success_rate'][-1] if spider_metrics['success_rate'] else 0,
                'trend': success_trend,
                'predicted_7d': self._extrapolate_trend(spider_metrics['success_rate'], 7)
            }
        
        # レスポンス時間の予測
        if 'response_time' in spider_metrics:
            response_trend = self._analyze_trend(spider_metrics['response_time'])
            predictions['response_time'] = {
                'current': spider_metrics['response_time'][-1] if spider_metrics['response_time'] else 0,
                'trend': response_trend,
                'predicted_7d': self._extrapolate_trend(spider_metrics['response_time'], 7)
            }
        
        # エラー率の予測
        if 'error_rate' in spider_metrics:
            error_trend = self._analyze_trend(spider_metrics['error_rate'])
            predictions['error_rate'] = {
                'current': spider_metrics['error_rate'][-1] if spider_metrics['error_rate'] else 0,
                'trend': error_trend,
                'predicted_7d': self._extrapolate_trend(spider_metrics['error_rate'], 7)
            }
        
        return {
            'spider_name': spider_name,
            'predictions': predictions,
            'recommendations': self._generate_spider_recommendations(predictions)
        }
    
    def _get_performance_metrics(self, project_id: str, start_time: datetime, end_time: datetime) -> Dict[str, List]:
        """パフォーマンスメトリクスを取得"""
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT metric_type, value, timestamp
            FROM performance_metrics
            WHERE project_id = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp
        ''', (project_id, start_time.isoformat(), end_time.isoformat()))
        
        metrics_data = defaultdict(list)
        for row in cursor.fetchall():
            metric_type, value, timestamp = row
            metrics_data[metric_type].append({
                'value': value,
                'timestamp': timestamp
            })
        
        conn.close()
        return dict(metrics_data)
    
    def _get_spider_metrics(self, project_id: str, spider_name: str, start_time: datetime, end_time: datetime) -> Dict[str, List]:
        """スパイダーメトリクスを取得"""
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT metric_type, value, timestamp
            FROM performance_metrics
            WHERE project_id = ? AND spider_name = ? AND timestamp >= ? AND timestamp <= ?
            AND metric_type LIKE 'scrapy_%'
            ORDER BY timestamp
        ''', (project_id, spider_name, start_time.isoformat(), end_time.isoformat()))
        
        metrics_data = defaultdict(list)
        for row in cursor.fetchall():
            metric_type, value, timestamp = row
            # scrapy_プレフィックスを除去
            clean_type = metric_type.replace('scrapy_', '')
            metrics_data[clean_type].append(value)
        
        conn.close()
        return dict(metrics_data)
    
    def _predict_metric(self, metric_type: str, data: List[Dict], days_ahead: int) -> Optional[Prediction]:
        """メトリクスの予測"""
        if len(data) < 10:  # 最低10データポイント必要
            return None
        
        values = [point['value'] for point in data]
        
        # 線形回帰による予測
        x = np.arange(len(values))
        y = np.array(values)
        
        # 最小二乗法
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # 予測値計算
        future_x = len(values) + days_ahead * 24  # 1日24時間として計算
        predicted_value = slope * future_x + intercept
        
        # 信頼度計算（R²値）
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # トレンド判定
        if slope > 0.1:
            trend = 'increasing'
        elif slope < -0.1:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # リスク評価
        current_value = values[-1]
        risk_level = self._assess_risk(metric_type, current_value, predicted_value)
        
        # 推奨事項
        recommendations = self._generate_metric_recommendations(metric_type, trend, risk_level)
        
        return Prediction(
            metric_name=metric_type,
            current_value=current_value,
            predicted_value=predicted_value,
            confidence=r_squared,
            trend=trend,
            risk_level=risk_level,
            recommendations=recommendations
        )
    
    def _detect_metric_anomalies(self, metric_type: str, data: List[Dict]) -> List[Anomaly]:
        """メトリクス異常を検知"""
        if len(data) < 20:
            return []
        
        values = [point['value'] for point in data]
        timestamps = [point['timestamp'] for point in data]
        
        # 移動平均と標準偏差を計算
        window_size = min(10, len(values) // 2)
        anomalies = []
        
        for i in range(window_size, len(values)):
            window = values[i-window_size:i]
            mean = np.mean(window)
            std = np.std(window)
            
            current_value = values[i]
            deviation = abs(current_value - mean)
            
            # 3σルールで異常検知
            if std > 0 and deviation > 3 * std:
                severity = 'high' if deviation > 5 * std else 'medium'
                
                anomaly = Anomaly(
                    timestamp=timestamps[i],
                    metric_name=metric_type,
                    value=current_value,
                    expected_value=mean,
                    deviation=deviation,
                    severity=severity,
                    description=f"{metric_type}が期待値から大きく逸脱しています"
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _predict_resource_trend(self, resource_type: str, data: List[Dict]) -> Dict[str, Any]:
        """リソーストレンドを予測"""
        if not data:
            return {'trend': 'unknown', 'confidence': 0}
        
        values = [point['value'] for point in data]
        
        # 短期トレンド（最近25%のデータ）
        recent_size = max(1, len(values) // 4)
        recent_values = values[-recent_size:]
        
        # 長期トレンド（全データ）
        long_trend = self._analyze_trend(values)
        short_trend = self._analyze_trend(recent_values)
        
        # 季節性分析（時間別パターン）
        seasonality = self._analyze_seasonality(data)
        
        return {
            'long_term_trend': long_trend,
            'short_term_trend': short_trend,
            'seasonality': seasonality,
            'current_value': values[-1] if values else 0,
            'max_value': max(values) if values else 0,
            'min_value': min(values) if values else 0,
            'avg_value': np.mean(values) if values else 0
        }
    
    def _analyze_trend(self, values: List[float]) -> str:
        """トレンドを分析"""
        if len(values) < 2:
            return 'stable'
        
        # 線形回帰の傾き
        x = np.arange(len(values))
        y = np.array(values)
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _analyze_seasonality(self, data: List[Dict]) -> Dict[str, float]:
        """季節性を分析"""
        hourly_avg = defaultdict(list)
        
        for point in data:
            timestamp = datetime.fromisoformat(point['timestamp'])
            hour = timestamp.hour
            hourly_avg[hour].append(point['value'])
        
        # 時間別平均を計算
        hourly_patterns = {}
        for hour, values in hourly_avg.items():
            hourly_patterns[hour] = np.mean(values)
        
        return hourly_patterns
    
    def _extrapolate_trend(self, values: List[float], days: int) -> float:
        """トレンドを外挿"""
        if len(values) < 2:
            return values[0] if values else 0
        
        x = np.arange(len(values))
        y = np.array(values)
        slope, intercept = np.polyfit(x, y, 1)
        
        future_x = len(values) + days * 24  # 1日24時間
        return slope * future_x + intercept
    
    def _assess_risk(self, metric_type: str, current: float, predicted: float) -> str:
        """リスクを評価"""
        thresholds = {
            'cpu': {'high': 90, 'medium': 70},
            'memory': {'high': 90, 'medium': 70},
            'disk': {'high': 95, 'medium': 80},
            'scrapy_success_rate': {'high': 70, 'medium': 85}  # 成功率は低いほど危険
        }
        
        if metric_type not in thresholds:
            return 'low'
        
        threshold = thresholds[metric_type]
        value = max(current, predicted)
        
        if metric_type == 'scrapy_success_rate':
            # 成功率は逆転
            if value < threshold['high']:
                return 'high'
            elif value < threshold['medium']:
                return 'medium'
            else:
                return 'low'
        else:
            if value > threshold['high']:
                return 'high'
            elif value > threshold['medium']:
                return 'medium'
            else:
                return 'low'
    
    def _calculate_overall_risk(self, predictions: Dict[str, Any]) -> float:
        """総合リスクスコアを計算"""
        risk_scores = []
        
        for resource, pred in predictions.items():
            if 'current_value' in pred:
                # リソース使用率に基づくスコア
                usage = pred['current_value']
                if usage > 90:
                    risk_scores.append(0.9)
                elif usage > 70:
                    risk_scores.append(0.6)
                elif usage > 50:
                    risk_scores.append(0.3)
                else:
                    risk_scores.append(0.1)
        
        return np.mean(risk_scores) if risk_scores else 0.0
    
    def _generate_metric_recommendations(self, metric_type: str, trend: str, risk_level: str) -> List[str]:
        """メトリクス推奨事項を生成"""
        recommendations = []
        
        if metric_type == 'cpu':
            if risk_level == 'high':
                recommendations.append("CPU使用率が高いです。並行リクエスト数を減らしてください。")
                recommendations.append("不要なプロセスを停止してください。")
            if trend == 'increasing':
                recommendations.append("CPU使用率が増加傾向です。監視を強化してください。")
        
        elif metric_type == 'memory':
            if risk_level == 'high':
                recommendations.append("メモリ使用率が高いです。メモリリークを確認してください。")
                recommendations.append("キャッシュサイズを調整してください。")
            if trend == 'increasing':
                recommendations.append("メモリ使用率が増加傾向です。定期的な再起動を検討してください。")
        
        elif metric_type == 'scrapy_success_rate':
            if risk_level == 'high':
                recommendations.append("成功率が低いです。エラーハンドリングを改善してください。")
                recommendations.append("リトライ設定を見直してください。")
        
        return recommendations
    
    def _generate_resource_recommendations(self, predictions: Dict[str, Any]) -> List[str]:
        """リソース推奨事項を生成"""
        recommendations = []
        
        for resource, pred in predictions.items():
            if pred.get('current_value', 0) > 80:
                recommendations.append(f"{resource}使用率が高いです。リソースの追加を検討してください。")
            
            if pred.get('long_term_trend') == 'increasing':
                recommendations.append(f"{resource}の長期的な増加傾向が見られます。容量計画を見直してください。")
        
        return recommendations
    
    def _generate_spider_recommendations(self, predictions: Dict[str, Any]) -> List[str]:
        """スパイダー推奨事項を生成"""
        recommendations = []
        
        if 'success_rate' in predictions:
            success_pred = predictions['success_rate']
            if success_pred.get('predicted_7d', 100) < 90:
                recommendations.append("成功率の低下が予測されます。エラーハンドリングを強化してください。")
        
        if 'response_time' in predictions:
            response_pred = predictions['response_time']
            if response_pred.get('trend') == 'increasing':
                recommendations.append("レスポンス時間の増加が予測されます。遅延設定を調整してください。")
        
        if 'error_rate' in predictions:
            error_pred = predictions['error_rate']
            if error_pred.get('trend') == 'increasing':
                recommendations.append("エラー率の増加が予測されます。対象サイトの変更を確認してください。")
        
        return recommendations


# グローバルインスタンス
predictive_analytics = PredictiveAnalytics()
