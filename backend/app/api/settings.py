"""
設定管理API

一般設定、Scrapy設定、システム設定の管理を行うAPIエンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
import os
from datetime import datetime, timezone

from ..database import get_db, User as DBUser
from .auth import get_current_active_user

router = APIRouter()

# デフォルト設定値
DEFAULT_GENERAL_SETTINGS = {
    "default_scrapy_version": "2.11.0",
    "project_directory": "/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects",
    "auto_save": True,
    "dark_mode": False,
    "default_log_level": "INFO",
    "concurrent_requests": 16,
    "download_delay": 0,
    "randomize_download_delay": True,
    "auto_throttle_enabled": True,
    "auto_throttle_start_delay": 1,
    "auto_throttle_max_delay": 60,
    "auto_throttle_target_concurrency": 1.0,
    "cookies_enabled": True,
    "retry_enabled": True,
    "retry_times": 2,
    "retry_http_codes": [500, 502, 503, 504, 408, 429],
}

# 設定ファイルのパス
SETTINGS_FILE_PATH = "/home/igtmtakan/workplace/python/scrapyUI/backend/config/general_settings.json"

def ensure_settings_directory():
    """設定ディレクトリが存在することを確認"""
    os.makedirs(os.path.dirname(SETTINGS_FILE_PATH), exist_ok=True)

def load_settings_from_file() -> Dict[str, Any]:
    """ファイルから設定を読み込み"""
    try:
        if os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # デフォルト値とマージ
                merged_settings = DEFAULT_GENERAL_SETTINGS.copy()
                merged_settings.update(settings)
                return merged_settings
        else:
            return DEFAULT_GENERAL_SETTINGS.copy()
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return DEFAULT_GENERAL_SETTINGS.copy()

def save_settings_to_file(settings: Dict[str, Any]) -> bool:
    """設定をファイルに保存"""
    try:
        ensure_settings_directory()
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"設定ファイル保存エラー: {e}")
        return False

@router.get(
    "/general",
    summary="一般設定取得",
    description="現在の一般設定を取得します。"
)
async def get_general_settings(
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## 一般設定取得

    認証されたユーザーの一般設定を取得します。

    ### レスポンス
    - **200**: 設定が正常に取得された場合
    - **401**: 認証が必要な場合
    - **500**: サーバーエラー
    """

    try:
        settings = load_settings_from_file()
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"設定の取得に失敗しました: {str(e)}"
        )

@router.put(
    "/general",
    summary="一般設定更新",
    description="一般設定を更新します。"
)
async def update_general_settings(
    settings: Dict[str, Any],
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## 一般設定更新

    認証されたユーザーの一般設定を更新します。

    ### リクエストボディ
    - **settings**: 更新する設定値の辞書

    ### レスポンス
    - **200**: 設定が正常に更新された場合
    - **400**: リクエストデータが不正な場合
    - **401**: 認証が必要な場合
    - **500**: サーバーエラー
    """

    try:
        # 現在の設定を読み込み
        current_settings = load_settings_from_file()

        # 許可されたキーのみ更新
        allowed_keys = set(DEFAULT_GENERAL_SETTINGS.keys())

        for key, value in settings.items():
            if key in allowed_keys:
                current_settings[key] = value

        # プロジェクトディレクトリは固定値に戻す
        current_settings["project_directory"] = DEFAULT_GENERAL_SETTINGS["project_directory"]

        # 設定をファイルに保存
        if save_settings_to_file(current_settings):
            return {"message": "設定が正常に更新されました"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="設定の保存に失敗しました"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"設定の更新に失敗しました: {str(e)}"
        )

@router.post(
    "/general/reset",
    summary="一般設定リセット",
    description="一般設定をデフォルト値にリセットします。"
)
async def reset_general_settings(
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## 一般設定リセット

    認証されたユーザーの一般設定をデフォルト値にリセットします。

    ### レスポンス
    - **200**: 設定が正常にリセットされた場合
    - **401**: 認証が必要な場合
    - **500**: サーバーエラー
    """

    try:
        # デフォルト設定を保存
        if save_settings_to_file(DEFAULT_GENERAL_SETTINGS.copy()):
            return {"message": "設定がデフォルト値にリセットされました"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="設定のリセットに失敗しました"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"設定のリセットに失敗しました: {str(e)}"
        )

@router.get(
    "/scrapy-versions",
    summary="利用可能なScrapyバージョン取得",
    description="利用可能なScrapyバージョンのリストを取得します。"
)
async def get_available_scrapy_versions(
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## 利用可能なScrapyバージョン取得

    インストール可能なScrapyバージョンのリストを取得します。

    ### レスポンス
    - **200**: バージョンリストが正常に取得された場合
    - **401**: 認証が必要な場合
    """

    return {
        "versions": ["2.11.0", "2.10.1", "2.9.0", "2.8.0"],
        "recommended": "2.11.0"
    }

@router.get(
    "/log-levels",
    summary="利用可能なログレベル取得",
    description="利用可能なログレベルのリストを取得します。"
)
async def get_available_log_levels(
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## 利用可能なログレベル取得

    Scrapyで利用可能なログレベルのリストを取得します。

    ### レスポンス
    - **200**: ログレベルリストが正常に取得された場合
    - **401**: 認証が必要な場合
    """

    return {
        "levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        "default": "INFO",
        "descriptions": {
            "DEBUG": "詳細なデバッグ情報",
            "INFO": "一般的な情報",
            "WARNING": "警告メッセージ",
            "ERROR": "エラーメッセージ",
            "CRITICAL": "重大なエラー"
        }
    }
