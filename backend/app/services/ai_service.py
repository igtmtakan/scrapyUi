import openai
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from collections import Counter
import os

class AIAnalysisService:
    """AI分析サービス"""
    
    def __init__(self):
        # OpenAI API設定（環境変数から取得）
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
    
    async def analyze_scraping_results(
        self, 
        results: List[Dict[str, Any]], 
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """スクレイピング結果の AI分析"""
        
        if not self.openai_api_key:
            return self._fallback_analysis(results, analysis_type)
        
        try:
            # データの前処理
            processed_data = self._preprocess_results(results)
            
            if analysis_type == "comprehensive":
                return await self._comprehensive_analysis(processed_data)
            elif analysis_type == "quality":
                return await self._quality_analysis(processed_data)
            elif analysis_type == "patterns":
                return await self._pattern_analysis(processed_data)
            elif analysis_type == "optimization":
                return await self._optimization_analysis(processed_data)
            else:
                return await self._comprehensive_analysis(processed_data)
        
        except Exception as e:
            print(f"AI analysis error: {e}")
            return self._fallback_analysis(results, analysis_type)
    
    async def generate_spider_suggestions(
        self, 
        target_url: str, 
        desired_data: List[str]
    ) -> Dict[str, Any]:
        """スパイダー作成の提案を生成"""
        
        if not self.openai_api_key:
            return self._fallback_spider_suggestions(target_url, desired_data)
        
        try:
            prompt = f"""
            Target URL: {target_url}
            Desired data fields: {', '.join(desired_data)}
            
            Please analyze this website and provide:
            1. Recommended CSS selectors for each data field
            2. Suggested spider configuration
            3. Potential challenges and solutions
            4. Rate limiting recommendations
            5. Sample Scrapy spider code
            
            Format the response as JSON with the following structure:
            {{
                "selectors": {{"field_name": "css_selector"}},
                "config": {{"setting_name": "value"}},
                "challenges": ["challenge1", "challenge2"],
                "rate_limiting": {{"delay": 1, "randomize": true}},
                "sample_code": "python code string"
            }}
            """
            
            response = await self._call_openai_api(prompt, max_tokens=2000)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return self._parse_ai_response(response)
        
        except Exception as e:
            print(f"Spider suggestion error: {e}")
            return self._fallback_spider_suggestions(target_url, desired_data)
    
    async def optimize_spider_performance(
        self, 
        spider_stats: Dict[str, Any], 
        error_logs: List[str]
    ) -> Dict[str, Any]:
        """スパイダーパフォーマンスの最適化提案"""
        
        if not self.openai_api_key:
            return self._fallback_optimization(spider_stats, error_logs)
        
        try:
            # 統計情報の要約
            stats_summary = self._summarize_stats(spider_stats)
            error_summary = self._summarize_errors(error_logs)
            
            prompt = f"""
            Spider Performance Analysis:
            
            Statistics:
            {stats_summary}
            
            Common Errors:
            {error_summary}
            
            Please provide optimization recommendations including:
            1. Performance bottlenecks identification
            2. Configuration adjustments
            3. Error resolution strategies
            4. Scalability improvements
            5. Resource optimization
            
            Format as JSON with specific actionable recommendations.
            """
            
            response = await self._call_openai_api(prompt, max_tokens=1500)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return self._parse_optimization_response(response)
        
        except Exception as e:
            print(f"Optimization analysis error: {e}")
            return self._fallback_optimization(spider_stats, error_logs)
    
    async def detect_data_anomalies(
        self, 
        recent_results: List[Dict[str, Any]], 
        historical_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """データ異常の検出"""
        
        anomalies = {
            "detected_anomalies": [],
            "severity": "low",
            "recommendations": [],
            "confidence": 0.0
        }
        
        try:
            # 基本的な異常検出
            volume_anomaly = self._detect_volume_anomaly(recent_results, historical_results)
            if volume_anomaly:
                anomalies["detected_anomalies"].append(volume_anomaly)
            
            # データ品質の異常
            quality_anomaly = self._detect_quality_anomaly(recent_results, historical_results)
            if quality_anomaly:
                anomalies["detected_anomalies"].append(quality_anomaly)
            
            # パターンの変化
            pattern_anomaly = self._detect_pattern_anomaly(recent_results, historical_results)
            if pattern_anomaly:
                anomalies["detected_anomalies"].append(pattern_anomaly)
            
            # 重要度の計算
            if anomalies["detected_anomalies"]:
                anomalies["severity"] = self._calculate_severity(anomalies["detected_anomalies"])
                anomalies["recommendations"] = self._generate_anomaly_recommendations(anomalies["detected_anomalies"])
                anomalies["confidence"] = 0.8  # 基本的な検出の信頼度
            
            return anomalies
        
        except Exception as e:
            print(f"Anomaly detection error: {e}")
            return anomalies
    
    async def _comprehensive_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """包括的分析"""
        
        prompt = f"""
        Analyze this web scraping data comprehensively:
        
        Data Summary:
        - Total results: {data['total_results']}
        - Unique domains: {data['unique_domains']}
        - Data fields: {', '.join(data['common_fields'])}
        - Date range: {data['date_range']}
        
        Sample data structure:
        {json.dumps(data['sample_data'], indent=2)[:500]}...
        
        Provide insights on:
        1. Data quality assessment
        2. Coverage analysis
        3. Potential issues
        4. Improvement suggestions
        5. Business insights
        
        Format as JSON with detailed analysis.
        """
        
        response = await self._call_openai_api(prompt, max_tokens=1500)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return self._parse_analysis_response(response)
    
    async def _quality_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データ品質分析"""
        
        # 基本的な品質メトリクス
        quality_metrics = {
            "completeness": self._calculate_completeness(data),
            "consistency": self._calculate_consistency(data),
            "accuracy": self._estimate_accuracy(data),
            "timeliness": self._assess_timeliness(data)
        }
        
        return {
            "analysis_type": "quality",
            "metrics": quality_metrics,
            "overall_score": sum(quality_metrics.values()) / len(quality_metrics),
            "recommendations": self._generate_quality_recommendations(quality_metrics)
        }
    
    async def _pattern_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """パターン分析"""
        
        patterns = {
            "temporal_patterns": self._analyze_temporal_patterns(data),
            "domain_patterns": self._analyze_domain_patterns(data),
            "content_patterns": self._analyze_content_patterns(data)
        }
        
        return {
            "analysis_type": "patterns",
            "patterns": patterns,
            "insights": self._generate_pattern_insights(patterns)
        }
    
    async def _optimization_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """最適化分析"""
        
        optimization_areas = {
            "performance": self._analyze_performance_optimization(data),
            "resource_usage": self._analyze_resource_optimization(data),
            "data_extraction": self._analyze_extraction_optimization(data)
        }
        
        return {
            "analysis_type": "optimization",
            "areas": optimization_areas,
            "priority_recommendations": self._prioritize_optimizations(optimization_areas)
        }
    
    async def _call_openai_api(self, prompt: str, max_tokens: int = 1000) -> str:
        """OpenAI APIを呼び出し"""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert web scraping analyst. Provide detailed, actionable insights in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise
    
    def _preprocess_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """結果データの前処理"""
        
        if not results:
            return {
                "total_results": 0,
                "unique_domains": 0,
                "common_fields": [],
                "date_range": "N/A",
                "sample_data": {}
            }
        
        # ドメイン分析
        domains = set()
        for result in results:
            url = result.get("url", "")
            if url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    domains.add(domain)
                except:
                    pass
        
        # 共通フィールド分析
        all_fields = []
        for result in results:
            data = result.get("data", {})
            all_fields.extend(data.keys())
        
        common_fields = [field for field, count in Counter(all_fields).most_common(10)]
        
        # 日付範囲
        dates = []
        for result in results:
            created_at = result.get("created_at")
            if created_at:
                try:
                    dates.append(datetime.fromisoformat(created_at.replace('Z', '+00:00')))
                except:
                    pass
        
        date_range = "N/A"
        if dates:
            min_date = min(dates)
            max_date = max(dates)
            date_range = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
        
        return {
            "total_results": len(results),
            "unique_domains": len(domains),
            "common_fields": common_fields,
            "date_range": date_range,
            "sample_data": results[0] if results else {}
        }
    
    def _fallback_analysis(self, results: List[Dict[str, Any]], analysis_type: str) -> Dict[str, Any]:
        """AI APIが利用できない場合のフォールバック分析"""
        
        processed_data = self._preprocess_results(results)
        
        return {
            "analysis_type": analysis_type,
            "ai_powered": False,
            "summary": {
                "total_results": processed_data["total_results"],
                "unique_domains": processed_data["unique_domains"],
                "common_fields": processed_data["common_fields"][:5],
                "date_range": processed_data["date_range"]
            },
            "insights": [
                f"Collected {processed_data['total_results']} results",
                f"Data spans across {processed_data['unique_domains']} unique domains",
                f"Most common data fields: {', '.join(processed_data['common_fields'][:3])}"
            ],
            "recommendations": [
                "Consider implementing data validation",
                "Monitor scraping frequency to avoid rate limiting",
                "Regular data quality checks recommended"
            ]
        }
    
    def _fallback_spider_suggestions(self, target_url: str, desired_data: List[str]) -> Dict[str, Any]:
        """スパイダー提案のフォールバック"""
        
        return {
            "ai_powered": False,
            "target_url": target_url,
            "desired_data": desired_data,
            "basic_suggestions": {
                "selectors": {field: f"[data-{field.lower()}], .{field.lower()}" for field in desired_data},
                "config": {
                    "DOWNLOAD_DELAY": 1,
                    "RANDOMIZE_DOWNLOAD_DELAY": True,
                    "USER_AGENT": "ScrapyBot 1.0"
                },
                "recommendations": [
                    "Start with conservative rate limiting",
                    "Test selectors on a small sample first",
                    "Monitor for anti-bot measures",
                    "Implement proper error handling"
                ]
            }
        }
    
    def _fallback_optimization(self, spider_stats: Dict[str, Any], error_logs: List[str]) -> Dict[str, Any]:
        """最適化提案のフォールバック"""
        
        return {
            "ai_powered": False,
            "basic_optimizations": [
                "Adjust DOWNLOAD_DELAY based on response times",
                "Implement retry logic for failed requests",
                "Use connection pooling for better performance",
                "Monitor memory usage and implement cleanup"
            ],
            "error_analysis": {
                "total_errors": len(error_logs),
                "common_patterns": ["timeout", "connection", "parsing"] if error_logs else []
            }
        }
    
    # 追加のヘルパーメソッド（簡略化）
    def _calculate_completeness(self, data: Dict[str, Any]) -> float:
        """データ完全性の計算"""
        return 0.85  # 簡略化された値
    
    def _calculate_consistency(self, data: Dict[str, Any]) -> float:
        """データ一貫性の計算"""
        return 0.90  # 簡略化された値
    
    def _estimate_accuracy(self, data: Dict[str, Any]) -> float:
        """データ精度の推定"""
        return 0.88  # 簡略化された値
    
    def _assess_timeliness(self, data: Dict[str, Any]) -> float:
        """データ適時性の評価"""
        return 0.92  # 簡略化された値
    
    def _generate_quality_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """品質改善の推奨事項生成"""
        recommendations = []
        
        if metrics["completeness"] < 0.8:
            recommendations.append("Improve data completeness by enhancing selectors")
        if metrics["consistency"] < 0.8:
            recommendations.append("Standardize data formats and validation")
        if metrics["accuracy"] < 0.8:
            recommendations.append("Implement data verification mechanisms")
        
        return recommendations
    
    def _detect_volume_anomaly(self, recent: List[Dict], historical: List[Dict]) -> Optional[Dict]:
        """ボリューム異常の検出"""
        if len(recent) < len(historical) * 0.5:  # 50%以下の場合
            return {
                "type": "volume_drop",
                "severity": "medium",
                "description": f"Recent data volume ({len(recent)}) significantly lower than historical average ({len(historical)})"
            }
        return None
    
    def _detect_quality_anomaly(self, recent: List[Dict], historical: List[Dict]) -> Optional[Dict]:
        """品質異常の検出"""
        # 簡略化された実装
        return None
    
    def _detect_pattern_anomaly(self, recent: List[Dict], historical: List[Dict]) -> Optional[Dict]:
        """パターン異常の検出"""
        # 簡略化された実装
        return None
    
    def _calculate_severity(self, anomalies: List[Dict]) -> str:
        """異常の重要度計算"""
        if len(anomalies) >= 3:
            return "high"
        elif len(anomalies) >= 2:
            return "medium"
        else:
            return "low"
    
    def _generate_anomaly_recommendations(self, anomalies: List[Dict]) -> List[str]:
        """異常に対する推奨事項生成"""
        recommendations = []
        for anomaly in anomalies:
            if anomaly["type"] == "volume_drop":
                recommendations.append("Check spider configuration and target website availability")
        return recommendations

# グローバルインスタンス
ai_service = AIAnalysisService()
