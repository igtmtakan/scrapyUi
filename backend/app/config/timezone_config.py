"""
タイムゾーン設定
アプリケーション全体で使用するタイムゾーン設定を管理
"""

import pytz
from datetime import datetime
import os

# デフォルトタイムゾーン
DEFAULT_TIMEZONE = 'Asia/Tokyo'

# 環境変数からタイムゾーンを取得（デフォルトはAsia/Tokyo）
TIMEZONE_NAME = os.getenv('TIMEZONE', DEFAULT_TIMEZONE)

# タイムゾーンオブジェクト
TIMEZONE = pytz.timezone(TIMEZONE_NAME)

def get_timezone():
    """アプリケーションのタイムゾーンを取得"""
    return TIMEZONE

def get_timezone_name():
    """タイムゾーン名を取得"""
    return TIMEZONE_NAME

def now_in_timezone():
    """現在時刻をアプリケーションのタイムゾーンで取得"""
    return datetime.now(TIMEZONE)

def utc_to_local(utc_dt):
    """UTC時刻をローカルタイムゾーンに変換"""
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    return utc_dt.astimezone(TIMEZONE)

def local_to_utc(local_dt):
    """ローカル時刻をUTCに変換"""
    if local_dt.tzinfo is None:
        local_dt = TIMEZONE.localize(local_dt)
    return local_dt.astimezone(pytz.utc)

def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """日時をフォーマットして表示"""
    if dt.tzinfo is None:
        dt = TIMEZONE.localize(dt)
    elif dt.tzinfo != TIMEZONE:
        dt = dt.astimezone(TIMEZONE)
    return dt.strftime(format_str)
