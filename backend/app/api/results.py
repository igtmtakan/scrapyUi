from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from datetime import datetime, timedelta

from ..database import get_db, Result as DBResult, Task as DBTask, Project as DBProject, Spider as DBSpider
from ..models.schemas import Result, ResultCreate

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)

@router.get(
    "/",
    response_model=List[Result],
    summary="結果一覧取得",
    description="スクレイピング結果の一覧を取得します。",
    response_description="結果のリスト"
)
async def get_results(
    task_id: Optional[str] = Query(None, description="タスクIDでフィルタリング"),
    project_id: Optional[str] = Query(None, description="プロジェクトIDでフィルタリング"),
    spider_id: Optional[str] = Query(None, description="スパイダーIDでフィルタリング"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数の制限"),
    offset: int = Query(0, ge=0, description="オフセット"),
    start_date: Optional[str] = Query(None, description="開始日時 (ISO format)"),
    end_date: Optional[str] = Query(None, description="終了日時 (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    ## 結果一覧取得

    スクレイピング結果の一覧を取得します。

    ### パラメータ
    - **task_id** (optional): タスクIDでフィルタリング
    - **project_id** (optional): プロジェクトIDでフィルタリング
    - **spider_id** (optional): スパイダーIDでフィルタリング
    - **limit**: 取得件数の制限 (1-1000, デフォルト: 100)
    - **offset**: オフセット (デフォルト: 0)
    - **start_date** (optional): 開始日時でフィルタリング
    - **end_date** (optional): 終了日時でフィルタリング

    ### レスポンス
    - **200**: 結果のリストを返します
    - **400**: パラメータが不正な場合
    - **500**: サーバーエラー
    """

    query = db.query(DBResult)

    # フィルタリング
    if task_id:
        query = query.filter(DBResult.task_id == task_id)

    if project_id:
        # プロジェクトIDでフィルタリング（JOINが必要）
        query = query.join(DBTask).filter(DBTask.project_id == project_id)

    if spider_id:
        # スパイダーIDでフィルタリング（JOINが必要）
        query = query.join(DBTask).filter(DBTask.spider_id == spider_id)

    # 日付範囲でフィルタリング
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(DBResult.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format."
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(DBResult.created_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format."
            )

    # ソートとページネーション
    results = query.order_by(DBResult.created_at.desc()).offset(offset).limit(limit).all()

    return results

@router.get(
    "/{result_id}",
    response_model=Result,
    summary="結果詳細取得",
    description="指定された結果の詳細情報を取得します。",
    response_description="結果の詳細情報"
)
async def get_result(result_id: str, db: Session = Depends(get_db)):
    """
    ## 結果詳細取得

    指定された結果の詳細情報を取得します。

    ### パラメータ
    - **result_id**: 結果ID

    ### レスポンス
    - **200**: 結果の詳細情報を返します
    - **404**: 結果が見つからない場合
    - **500**: サーバーエラー
    """
    result = db.query(DBResult).filter(DBResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    return result

@router.get(
    "/task/{task_id}/summary",
    summary="タスク結果サマリー",
    description="指定されたタスクの結果サマリーを取得します。"
)
async def get_task_results_summary(task_id: str, db: Session = Depends(get_db)):
    """
    ## タスク結果サマリー

    指定されたタスクの結果サマリーを取得します。

    ### パラメータ
    - **task_id**: タスクID

    ### レスポンス
    - **200**: 結果サマリーを返します
    - **404**: タスクが見つからない場合
    - **500**: サーバーエラー
    """

    # タスクの存在確認
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # 結果の統計情報を取得
    results = db.query(DBResult).filter(DBResult.task_id == task_id).all()

    total_results = len(results)

    # データの分析
    url_domains = {}
    data_types = {}

    for result in results:
        # URLドメインの分析
        if result.url:
            try:
                from urllib.parse import urlparse
                domain = urlparse(result.url).netloc
                url_domains[domain] = url_domains.get(domain, 0) + 1
            except:
                pass

        # データタイプの分析
        if result.data:
            for key in result.data.keys():
                data_types[key] = data_types.get(key, 0) + 1

    # 最新と最古の結果
    first_result = results[0] if results else None
    last_result = results[-1] if results else None

    return {
        "task_id": task_id,
        "total_results": total_results,
        "url_domains": dict(sorted(url_domains.items(), key=lambda x: x[1], reverse=True)[:10]),
        "data_fields": dict(sorted(data_types.items(), key=lambda x: x[1], reverse=True)),
        "first_result_time": first_result.created_at if first_result else None,
        "last_result_time": last_result.created_at if last_result else None,
        "sample_data": results[0].data if results else None
    }

@router.get(
    "/analytics/overview",
    summary="結果分析概要",
    description="全体的な結果分析の概要を取得します。"
)
async def get_results_analytics_overview(
    days: int = Query(7, ge=1, le=365, description="分析対象日数"),
    db: Session = Depends(get_db)
):
    """
    ## 結果分析概要

    指定された期間の結果分析概要を取得します。

    ### パラメータ
    - **days**: 分析対象日数 (1-365, デフォルト: 7)

    ### レスポンス
    - **200**: 分析概要を返します
    - **500**: サーバーエラー
    """

    # 期間の計算
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 期間内の結果を取得
    results = db.query(DBResult).filter(
        DBResult.created_at >= start_date,
        DBResult.created_at <= end_date
    ).all()

    # 日別の結果数
    daily_counts = {}
    for result in results:
        date_key = result.created_at.date().isoformat()
        daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

    # プロジェクト別の結果数
    project_counts = {}
    for result in results:
        task = db.query(DBTask).filter(DBTask.id == result.task_id).first()
        if task:
            project = db.query(DBProject).filter(DBProject.id == task.project_id).first()
            if project:
                project_counts[project.name] = project_counts.get(project.name, 0) + 1

    # スパイダー別の結果数
    spider_counts = {}
    for result in results:
        task = db.query(DBTask).filter(DBTask.id == result.task_id).first()
        if task:
            spider = db.query(DBSpider).filter(DBSpider.id == task.spider_id).first()
            if spider:
                spider_counts[spider.name] = spider_counts.get(spider.name, 0) + 1

    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        },
        "total_results": len(results),
        "daily_counts": daily_counts,
        "project_counts": dict(sorted(project_counts.items(), key=lambda x: x[1], reverse=True)),
        "spider_counts": dict(sorted(spider_counts.items(), key=lambda x: x[1], reverse=True)),
        "average_per_day": len(results) / days if days > 0 else 0
    }

@router.post(
    "/export",
    summary="結果エクスポート",
    description="指定された条件の結果をエクスポートします。"
)
async def export_results(
    export_request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    ## 結果エクスポート

    指定された条件の結果をエクスポートします。

    ### リクエストボディ
    - **format**: エクスポート形式 (json, csv, xlsx, xml)
    - **task_ids** (optional): エクスポートするタスクIDのリスト
    - **fields** (optional): エクスポートするフィールドのリスト
    - **limit** (optional): エクスポート件数の制限

    ### レスポンス
    - **200**: エクスポートファイルのダウンロードURL
    - **400**: リクエストが不正な場合
    - **500**: サーバーエラー
    """

    export_format = export_request.get("format", "json")
    task_ids = export_request.get("task_ids", [])
    fields = export_request.get("fields", [])
    limit = export_request.get("limit", 1000)

    if export_format not in ["json", "csv", "xlsx", "xml"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid export format. Supported formats: json, csv, xlsx, xml"
        )

    # 結果を取得
    query = db.query(DBResult)
    if task_ids:
        query = query.filter(DBResult.task_id.in_(task_ids))

    results = query.limit(limit).all()

    # エクスポートファイルを生成（実装は簡略化）
    export_data = []
    for result in results:
        data = {
            "id": result.id,
            "task_id": result.task_id,
            "url": result.url,
            "created_at": result.created_at.isoformat(),
            "data": result.data
        }

        # 指定されたフィールドのみを含める
        if fields:
            filtered_data = {k: v for k, v in data.items() if k in fields}
            export_data.append(filtered_data)
        else:
            export_data.append(data)

    # TODO: 実際のファイル生成とダウンロードURL作成
    return {
        "export_id": f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "format": export_format,
        "total_records": len(export_data),
        "download_url": f"/api/results/download/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}",
        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
    }
