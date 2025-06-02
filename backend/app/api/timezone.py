"""
ScrapyUI タイムゾーン設定API

タイムゾーンの取得、設定、変換機能を提供するAPIエンドポイント
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import pytz

from ..services.timezone_service import timezone_service
from ..services.default_settings_service import default_settings_service
from ..auth.dependencies import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/timezone", tags=["timezone"])

class TimezoneUpdateRequest(BaseModel):
    """タイムゾーン更新リクエスト"""
    timezone: str
    display_format: Optional[str] = None

class DateTimeConvertRequest(BaseModel):
    """日時変換リクエスト"""
    datetime_str: str
    from_timezone: Optional[str] = None
    to_timezone: Optional[str] = None
    format_str: Optional[str] = None

class TimezoneResponse(BaseModel):
    """タイムゾーン情報レスポンス"""
    timezone: str
    current_time: str
    utc_time: str
    offset: str
    dst: bool
    display_format: str
    available_timezones: List[str]

@router.get("/current", response_model=TimezoneResponse)
async def get_current_timezone():
    """現在のタイムゾーン情報を取得"""
    try:
        timezone_info = timezone_service.get_timezone_info()
        return TimezoneResponse(**timezone_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タイムゾーン情報の取得に失敗: {str(e)}")

@router.get("/available")
async def get_available_timezones():
    """利用可能なタイムゾーン一覧を取得"""
    try:
        return {
            "available_timezones": timezone_service.get_available_timezones(),
            "common_timezones": timezone_service.get_common_timezones(),
            "all_timezones": timezone_service.get_all_timezones()[:50]  # 最初の50個のみ
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タイムゾーン一覧の取得に失敗: {str(e)}")

@router.get("/common")
async def get_common_timezones():
    """よく使用されるタイムゾーン一覧を取得"""
    try:
        return {
            "common_timezones": timezone_service.get_common_timezones()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"共通タイムゾーン一覧の取得に失敗: {str(e)}")

@router.post("/set")
async def set_timezone(
    request: TimezoneUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """タイムゾーンを設定（管理者のみ）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    try:
        # タイムゾーンの有効性をチェック
        if request.timezone not in pytz.all_timezones:
            raise HTTPException(status_code=400, detail=f"無効なタイムゾーン: {request.timezone}")
        
        # タイムゾーンを設定
        success = timezone_service.set_timezone(request.timezone)
        if not success:
            raise HTTPException(status_code=400, detail="タイムゾーンの設定に失敗")
        
        # 設定ファイルも更新
        timezone_settings = default_settings_service.get_timezone_settings()
        timezone_settings['default'] = request.timezone
        
        if request.display_format:
            timezone_settings['display_format'] = request.display_format
        
        default_settings_service.update_settings('timezone', timezone_settings)
        
        return {
            "message": f"タイムゾーンを {request.timezone} に設定しました",
            "timezone_info": timezone_service.get_timezone_info()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タイムゾーンの設定に失敗: {str(e)}")

@router.get("/now")
async def get_current_time():
    """現在時刻を取得"""
    try:
        now_local = timezone_service.now()
        now_utc = timezone_service.utc_now()
        
        return {
            "local_time": timezone_service.format_datetime(now_local),
            "utc_time": timezone_service.format_datetime(now_utc),
            "timestamp": now_local.timestamp(),
            "timezone": timezone_service.get_timezone_name(),
            "offset_hours": timezone_service.get_timezone_offset_hours(),
            "is_dst": timezone_service.is_dst()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"現在時刻の取得に失敗: {str(e)}")

@router.post("/convert")
async def convert_datetime(request: DateTimeConvertRequest):
    """日時を変換"""
    try:
        # 元の日時を解析
        if request.from_timezone:
            from_tz = pytz.timezone(request.from_timezone)
            if request.format_str:
                dt = datetime.strptime(request.datetime_str, request.format_str)
                dt = from_tz.localize(dt)
            else:
                dt = timezone_service.parse_datetime(request.datetime_str)
                dt = dt.replace(tzinfo=from_tz)
        else:
            dt = timezone_service.parse_datetime(request.datetime_str, request.format_str)
        
        # 変換先タイムゾーン
        if request.to_timezone:
            to_tz = pytz.timezone(request.to_timezone)
            converted_dt = dt.astimezone(to_tz)
        else:
            converted_dt = timezone_service.convert_to_local(dt)
        
        return {
            "original": {
                "datetime": request.datetime_str,
                "timezone": request.from_timezone or timezone_service.get_timezone_name(),
                "formatted": timezone_service.format_datetime(dt)
            },
            "converted": {
                "datetime": timezone_service.format_datetime(converted_dt),
                "timezone": request.to_timezone or timezone_service.get_timezone_name(),
                "timestamp": converted_dt.timestamp()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日時の解析に失敗: {str(e)}")
    except pytz.UnknownTimeZoneError as e:
        raise HTTPException(status_code=400, detail=f"無効なタイムゾーン: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"日時変換に失敗: {str(e)}")

@router.get("/settings")
async def get_timezone_settings():
    """タイムゾーン設定を取得"""
    try:
        settings = default_settings_service.get_timezone_settings()
        current_info = timezone_service.get_timezone_info()
        
        return {
            "settings": settings,
            "current": current_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タイムゾーン設定の取得に失敗: {str(e)}")

@router.put("/settings")
async def update_timezone_settings(
    settings: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """タイムゾーン設定を更新（管理者のみ）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    try:
        # 設定の検証
        if 'default' in settings:
            if settings['default'] not in pytz.all_timezones:
                raise HTTPException(status_code=400, detail=f"無効なタイムゾーン: {settings['default']}")
        
        if 'available_timezones' in settings:
            for tz in settings['available_timezones']:
                if tz not in pytz.all_timezones:
                    raise HTTPException(status_code=400, detail=f"無効なタイムゾーン: {tz}")
        
        # 設定を更新
        success = timezone_service.update_settings(settings)
        if not success:
            raise HTTPException(status_code=400, detail="タイムゾーン設定の更新に失敗")
        
        # 設定ファイルも更新
        default_settings_service.update_settings('timezone', settings)
        
        return {
            "message": "タイムゾーン設定を更新しました",
            "settings": default_settings_service.get_timezone_settings(),
            "current": timezone_service.get_timezone_info()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タイムゾーン設定の更新に失敗: {str(e)}")

@router.get("/validate/{timezone_name}")
async def validate_timezone(timezone_name: str):
    """タイムゾーンの有効性を検証"""
    try:
        is_valid = timezone_name in pytz.all_timezones
        
        if is_valid:
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)
            
            return {
                "valid": True,
                "timezone": timezone_name,
                "current_time": now.strftime('%Y-%m-%d %H:%M:%S %Z'),
                "offset": now.strftime('%z'),
                "dst": now.dst() is not None and now.dst().total_seconds() > 0
            }
        else:
            return {
                "valid": False,
                "timezone": timezone_name,
                "message": "無効なタイムゾーンです"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タイムゾーンの検証に失敗: {str(e)}")

@router.get("/search/{query}")
async def search_timezones(query: str):
    """タイムゾーンを検索"""
    try:
        query_lower = query.lower()
        matching_timezones = [
            tz for tz in pytz.all_timezones 
            if query_lower in tz.lower()
        ]
        
        # 最大50件まで
        matching_timezones = matching_timezones[:50]
        
        # 詳細情報を追加
        detailed_results = []
        for tz_name in matching_timezones:
            try:
                tz = pytz.timezone(tz_name)
                now = datetime.now(tz)
                detailed_results.append({
                    "timezone": tz_name,
                    "current_time": now.strftime('%Y-%m-%d %H:%M:%S'),
                    "offset": now.strftime('%z'),
                    "dst": now.dst() is not None and now.dst().total_seconds() > 0
                })
            except:
                detailed_results.append({
                    "timezone": tz_name,
                    "current_time": None,
                    "offset": None,
                    "dst": None
                })
        
        return {
            "query": query,
            "count": len(detailed_results),
            "results": detailed_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タイムゾーン検索に失敗: {str(e)}")
