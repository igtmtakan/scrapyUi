"""
ScrapyUI タイムゾーン管理サービス

アプリケーション全体のタイムゾーン設定を管理し、
日時の変換や表示フォーマットを統一します。
"""

import os
import pytz
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

class TimezoneService:
    """タイムゾーン管理サービス"""
    
    def __init__(self):
        self.settings = self._load_timezone_settings()
        self.current_timezone = self._get_current_timezone()
        
    def _load_timezone_settings(self) -> Dict[str, Any]:
        """タイムゾーン設定を読み込み"""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "default_settings.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get('timezone', self._get_default_settings())
        except Exception as e:
            print(f"⚠️ タイムゾーン設定の読み込みに失敗: {e}")
            return self._get_default_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """デフォルトタイムゾーン設定"""
        return {
            "default": "Asia/Tokyo",
            "display_format": "%Y-%m-%d %H:%M:%S %Z",
            "available_timezones": [
                "Asia/Tokyo",
                "UTC",
                "America/New_York",
                "America/Los_Angeles",
                "Europe/London",
                "Europe/Paris",
                "Asia/Shanghai",
                "Asia/Seoul"
            ],
            "auto_detect": False
        }
    
    def _get_current_timezone(self) -> pytz.BaseTzInfo:
        """現在のタイムゾーンを取得"""
        # 環境変数での上書き
        env_timezone = os.getenv('SCRAPY_UI_TIMEZONE')
        if env_timezone:
            try:
                return pytz.timezone(env_timezone)
            except pytz.UnknownTimeZoneError:
                print(f"⚠️ 無効なタイムゾーン: {env_timezone}")
        
        # 設定ファイルから取得
        default_tz = self.settings.get('default', 'Asia/Tokyo')
        
        # 自動検出が有効な場合
        if self.settings.get('auto_detect', False):
            try:
                # システムのタイムゾーンを検出
                import time
                local_tz = time.tzname[0] if time.tzname else None
                if local_tz:
                    return pytz.timezone(local_tz)
            except:
                pass
        
        try:
            return pytz.timezone(default_tz)
        except pytz.UnknownTimeZoneError:
            print(f"⚠️ 無効なデフォルトタイムゾーン: {default_tz}, UTCを使用します")
            return pytz.UTC
    
    def get_current_timezone(self) -> pytz.BaseTzInfo:
        """現在のタイムゾーンを取得"""
        return self.current_timezone
    
    def get_timezone_name(self) -> str:
        """現在のタイムゾーン名を取得"""
        return str(self.current_timezone)
    
    def get_available_timezones(self) -> List[str]:
        """利用可能なタイムゾーン一覧を取得"""
        return self.settings.get('available_timezones', [])
    
    def get_all_timezones(self) -> List[str]:
        """すべてのタイムゾーン一覧を取得"""
        return sorted(pytz.all_timezones)
    
    def set_timezone(self, timezone_name: str) -> bool:
        """タイムゾーンを設定"""
        try:
            new_timezone = pytz.timezone(timezone_name)
            self.current_timezone = new_timezone
            
            # 環境変数に設定
            os.environ['SCRAPY_UI_TIMEZONE'] = timezone_name
            
            print(f"✅ タイムゾーンを {timezone_name} に設定しました")
            return True
        except pytz.UnknownTimeZoneError:
            print(f"❌ 無効なタイムゾーン: {timezone_name}")
            return False
    
    def now(self) -> datetime:
        """現在のタイムゾーンでの現在時刻を取得"""
        return datetime.now(self.current_timezone)
    
    def utc_now(self) -> datetime:
        """UTC現在時刻を取得"""
        return datetime.now(pytz.UTC)
    
    def convert_to_local(self, dt: datetime) -> datetime:
        """UTC時刻を現在のタイムゾーンに変換"""
        if dt.tzinfo is None:
            # ナイーブな datetime を UTC として扱う
            dt = pytz.UTC.localize(dt)
        elif dt.tzinfo != pytz.UTC:
            # 他のタイムゾーンの場合は一度UTCに変換
            dt = dt.astimezone(pytz.UTC)
        
        return dt.astimezone(self.current_timezone)
    
    def convert_to_utc(self, dt: datetime) -> datetime:
        """現在のタイムゾーンの時刻をUTCに変換"""
        if dt.tzinfo is None:
            # ナイーブな datetime を現在のタイムゾーンとして扱う
            dt = self.current_timezone.localize(dt)
        
        return dt.astimezone(pytz.UTC)
    
    def format_datetime(self, dt: datetime, format_str: Optional[str] = None) -> str:
        """日時を指定フォーマットで文字列化"""
        if format_str is None:
            format_str = self.settings.get('display_format', '%Y-%m-%d %H:%M:%S %Z')
        
        # 現在のタイムゾーンに変換してフォーマット
        local_dt = self.convert_to_local(dt)
        return local_dt.strftime(format_str)
    
    def parse_datetime(self, dt_str: str, format_str: Optional[str] = None) -> datetime:
        """文字列から日時を解析（現在のタイムゾーンとして扱う）"""
        if format_str is None:
            # 一般的なフォーマットを試行
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%d',
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(dt_str, fmt)
                    return self.current_timezone.localize(dt)
                except ValueError:
                    continue
            
            raise ValueError(f"日時文字列の解析に失敗: {dt_str}")
        else:
            dt = datetime.strptime(dt_str, format_str)
            return self.current_timezone.localize(dt)
    
    def get_timezone_info(self) -> Dict[str, Any]:
        """現在のタイムゾーン情報を取得"""
        now = self.now()
        utc_now = self.utc_now()
        
        return {
            'timezone': self.get_timezone_name(),
            'current_time': self.format_datetime(now),
            'utc_time': self.format_datetime(utc_now),
            'offset': now.strftime('%z'),
            'dst': now.dst() is not None and now.dst().total_seconds() > 0,
            'display_format': self.settings.get('display_format'),
            'available_timezones': self.get_available_timezones()
        }
    
    def get_timezone_offset_hours(self) -> float:
        """現在のタイムゾーンのUTCからのオフセット（時間）を取得"""
        now = self.now()
        offset_seconds = now.utcoffset().total_seconds()
        return offset_seconds / 3600
    
    def is_dst(self) -> bool:
        """現在サマータイム（夏時間）かどうかを判定"""
        now = self.now()
        return now.dst() is not None and now.dst().total_seconds() > 0
    
    def get_common_timezones(self) -> Dict[str, str]:
        """よく使用されるタイムゾーンの一覧を取得"""
        common_timezones = {
            'Asia/Tokyo': '日本標準時 (JST)',
            'UTC': '協定世界時 (UTC)',
            'America/New_York': '東部標準時 (EST/EDT)',
            'America/Los_Angeles': '太平洋標準時 (PST/PDT)',
            'Europe/London': 'グリニッジ標準時 (GMT/BST)',
            'Europe/Paris': '中央ヨーロッパ時間 (CET/CEST)',
            'Asia/Shanghai': '中国標準時 (CST)',
            'Asia/Seoul': '韓国標準時 (KST)',
            'Australia/Sydney': 'オーストラリア東部標準時 (AEST/AEDT)',
            'America/Chicago': '中部標準時 (CST/CDT)',
            'Asia/Kolkata': 'インド標準時 (IST)',
            'Asia/Dubai': '湾岸標準時 (GST)'
        }
        
        return common_timezones
    
    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """タイムゾーン設定を更新"""
        try:
            # 設定を検証
            if 'default' in new_settings:
                pytz.timezone(new_settings['default'])  # 有効性チェック
            
            # 設定を更新
            self.settings.update(new_settings)
            
            # 現在のタイムゾーンを再設定
            if 'default' in new_settings:
                self.current_timezone = pytz.timezone(new_settings['default'])
            
            print("✅ タイムゾーン設定を更新しました")
            return True
        except Exception as e:
            print(f"❌ タイムゾーン設定の更新に失敗: {e}")
            return False

# グローバルインスタンス
timezone_service = TimezoneService()

def get_current_timezone() -> pytz.BaseTzInfo:
    """現在のタイムゾーンを取得する便利関数"""
    return timezone_service.get_current_timezone()

def now() -> datetime:
    """現在のタイムゾーンでの現在時刻を取得する便利関数"""
    return timezone_service.now()

def format_datetime(dt: datetime, format_str: Optional[str] = None) -> str:
    """日時をフォーマットする便利関数"""
    return timezone_service.format_datetime(dt, format_str)
