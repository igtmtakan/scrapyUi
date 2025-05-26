from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db, Result as DBResult, Task as DBTask, User as DBUser
from ..api.auth import get_current_active_user
from ..services.ai_service import ai_service

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)

class AnalysisRequest(BaseModel):
    task_ids: Optional[List[str]] = None
    analysis_type: str = "comprehensive"  # comprehensive, quality, patterns, optimization
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: Optional[int] = 1000

class SpiderSuggestionRequest(BaseModel):
    target_url: str
    desired_data: List[str]
    additional_context: Optional[str] = None

class OptimizationRequest(BaseModel):
    task_id: str
    include_logs: bool = True

@router.post(
    "/analyze-results",
    summary="結果データのAI分析",
    description="スクレイピング結果をAIで分析し、インサイトを提供します。"
)
async def analyze_results(
    request: AnalysisRequest,
    current_user: DBUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    ## 結果データのAI分析

    スクレイピング結果をAIで分析し、データ品質、パターン、最適化提案などのインサイトを提供します。

    ### リクエストボディ
    - **task_ids** (optional): 分析対象のタスクIDリスト
    - **analysis_type**: 分析タイプ (comprehensive, quality, patterns, optimization)
    - **date_from** (optional): 分析対象期間の開始日
    - **date_to** (optional): 分析対象期間の終了日
    - **limit** (optional): 分析対象の最大件数

    ### レスポンス
    - **200**: AI分析結果を返します
    - **400**: リクエストデータが不正な場合
    - **401**: 認証が必要
    - **500**: サーバーエラー
    """

    try:
        # 結果データを取得
        query = db.query(DBResult)

        # タスクIDでフィルタリング
        if request.task_ids:
            query = query.filter(DBResult.task_id.in_(request.task_ids))

        # 日付範囲でフィルタリング
        if request.date_from:
            from datetime import datetime
            date_from = datetime.fromisoformat(request.date_from.replace('Z', '+00:00'))
            query = query.filter(DBResult.created_at >= date_from)

        if request.date_to:
            from datetime import datetime
            date_to = datetime.fromisoformat(request.date_to.replace('Z', '+00:00'))
            query = query.filter(DBResult.created_at <= date_to)

        # 権限チェック（一般ユーザーは自分のタスクの結果のみ）
        if not current_user.is_superuser:
            # タスクを通じてユーザーの結果のみを取得
            user_tasks = db.query(DBTask).filter(DBTask.user_id == current_user.id).all()
            user_task_ids = [task.id for task in user_tasks]
            query = query.filter(DBResult.task_id.in_(user_task_ids))

        results = query.limit(request.limit).all()

        if not results:
            return {
                "analysis_type": request.analysis_type,
                "message": "No data found for analysis",
                "insights": [],
                "recommendations": []
            }

        # 結果データを辞書形式に変換
        results_data = []
        for result in results:
            results_data.append({
                "id": result.id,
                "task_id": result.task_id,
                "url": result.url,
                "data": result.data,
                "created_at": result.created_at.isoformat()
            })

        # AI分析を実行
        analysis_result = await ai_service.analyze_scraping_results(
            results_data,
            request.analysis_type
        )

        return {
            "analysis_type": request.analysis_type,
            "data_summary": {
                "total_results": len(results_data),
                "date_range": f"{request.date_from or 'N/A'} to {request.date_to or 'N/A'}",
                "task_count": len(set(r["task_id"] for r in results_data))
            },
            "analysis": analysis_result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post(
    "/suggest-spider",
    summary="スパイダー作成提案",
    description="対象URLと取得したいデータに基づいてスパイダー作成の提案を生成します。"
)
async def suggest_spider(
    request: SpiderSuggestionRequest,
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    ## スパイダー作成提案

    対象URLと取得したいデータフィールドに基づいて、AIがスパイダー作成の提案を生成します。

    ### リクエストボディ
    - **target_url**: 対象となるWebサイトのURL
    - **desired_data**: 取得したいデータフィールドのリスト
    - **additional_context** (optional): 追加のコンテキスト情報

    ### レスポンス
    - **200**: スパイダー作成提案を返します
    - **400**: リクエストデータが不正な場合
    - **401**: 認証が必要
    - **500**: サーバーエラー
    """

    try:
        # URL形式の基本的な検証
        if not request.target_url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL format"
            )

        if not request.desired_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one desired data field is required"
            )

        # AI提案を生成
        suggestions = await ai_service.generate_spider_suggestions(
            request.target_url,
            request.desired_data
        )

        return {
            "target_url": request.target_url,
            "desired_data": request.desired_data,
            "suggestions": suggestions,
            "generated_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spider suggestion failed: {str(e)}"
        )

@router.post(
    "/optimize-spider",
    summary="スパイダー最適化提案",
    description="タスクの実行統計とエラーログに基づいてスパイダーの最適化提案を生成します。"
)
async def optimize_spider(
    request: OptimizationRequest,
    current_user: DBUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    ## スパイダー最適化提案

    タスクの実行統計とエラーログを分析して、スパイダーのパフォーマンス最適化提案を生成します。

    ### リクエストボディ
    - **task_id**: 分析対象のタスクID
    - **include_logs**: ログ分析を含めるかどうか

    ### レスポンス
    - **200**: 最適化提案を返します
    - **404**: タスクが見つからない場合
    - **401**: 認証が必要
    - **403**: アクセス権限がない場合
    - **500**: サーバーエラー
    """

    try:
        # タスクを取得
        task = db.query(DBTask).filter(DBTask.id == request.task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        # 権限チェック
        if not current_user.is_superuser and task.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # タスク統計を収集
        spider_stats = {
            "task_id": task.id,
            "status": task.status.value,
            "items_count": task.items_count or 0,
            "requests_count": task.requests_count or 0,
            "error_count": task.error_count or 0,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "finished_at": task.finished_at.isoformat() if task.finished_at else None,
            "settings": task.settings or {}
        }

        # エラーログを取得
        error_logs = []
        if request.include_logs:
            from ..database import Log as DBLog
            logs = db.query(DBLog).filter(
                DBLog.task_id == request.task_id,
                DBLog.level.in_(["ERROR", "WARNING"])
            ).limit(100).all()

            error_logs = [log.message for log in logs]

        # AI最適化分析を実行
        optimization_result = await ai_service.optimize_spider_performance(
            spider_stats,
            error_logs
        )

        return {
            "task_id": request.task_id,
            "current_performance": spider_stats,
            "optimization": optimization_result,
            "analyzed_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization analysis failed: {str(e)}"
        )

@router.get(
    "/anomaly-detection/{task_id}",
    summary="データ異常検出",
    description="最近の結果と過去のデータを比較して異常を検出します。"
)
async def detect_anomalies(
    task_id: str,
    days_back: int = Query(7, ge=1, le=30, description="比較対象の過去日数"),
    current_user: DBUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    ## データ異常検出

    指定されたタスクの最近の結果と過去のデータを比較して、異常やパターンの変化を検出します。

    ### パラメータ
    - **task_id**: 分析対象のタスクID
    - **days_back**: 比較対象とする過去の日数 (1-30, デフォルト: 7)

    ### レスポンス
    - **200**: 異常検出結果を返します
    - **404**: タスクが見つからない場合
    - **401**: 認証が必要
    - **403**: アクセス権限がない場合
    - **500**: サーバーエラー
    """

    try:
        # タスクの存在確認と権限チェック
        task = db.query(DBTask).filter(DBTask.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        if not current_user.is_superuser and task.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        from datetime import datetime, timedelta

        # 最近のデータ（過去24時間）
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_results = db.query(DBResult).filter(
            DBResult.task_id == task_id,
            DBResult.created_at >= recent_cutoff
        ).all()

        # 過去のデータ（指定日数前から24時間前まで）
        historical_start = datetime.utcnow() - timedelta(days=days_back)
        historical_end = recent_cutoff
        historical_results = db.query(DBResult).filter(
            DBResult.task_id == task_id,
            DBResult.created_at >= historical_start,
            DBResult.created_at < historical_end
        ).all()

        # データを辞書形式に変換
        recent_data = [
            {
                "id": r.id,
                "url": r.url,
                "data": r.data,
                "created_at": r.created_at.isoformat()
            }
            for r in recent_results
        ]

        historical_data = [
            {
                "id": r.id,
                "url": r.url,
                "data": r.data,
                "created_at": r.created_at.isoformat()
            }
            for r in historical_results
        ]

        # 異常検出を実行
        anomaly_result = await ai_service.detect_data_anomalies(
            recent_data,
            historical_data
        )

        return {
            "task_id": task_id,
            "analysis_period": {
                "recent_period": "Last 24 hours",
                "historical_period": f"Last {days_back} days (excluding recent 24h)",
                "recent_count": len(recent_data),
                "historical_count": len(historical_data)
            },
            "anomaly_detection": anomaly_result,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(e)}"
        )

@router.get(
    "/insights/dashboard",
    summary="AIインサイトダッシュボード",
    description="ユーザーのスクレイピング活動に関するAIインサイトの概要を提供します。"
)
async def get_ai_insights_dashboard(
    current_user: DBUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    ## AIインサイトダッシュボード

    ユーザーのスクレイピング活動に関するAIインサイトの概要を提供します。

    ### レスポンス
    - **200**: AIインサイトダッシュボードを返します
    - **401**: 認証が必要
    - **500**: サーバーエラー
    """

    try:
        from datetime import datetime, timedelta

        # 過去30日間のデータを取得
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        # ユーザーのタスクを取得
        user_tasks = db.query(DBTask).filter(DBTask.user_id == current_user.id).all()
        user_task_ids = [task.id for task in user_tasks]

        if not user_task_ids:
            return {
                "message": "No tasks found for analysis",
                "insights": [],
                "recommendations": []
            }

        # 結果データを取得
        results = db.query(DBResult).filter(
            DBResult.task_id.in_(user_task_ids),
            DBResult.created_at >= cutoff_date
        ).limit(1000).all()

        # 基本統計
        total_results = len(results)
        total_tasks = len(user_tasks)
        active_tasks = len([t for t in user_tasks if t.status.value == "RUNNING"])

        # 簡単なインサイト生成
        insights = [
            f"You have collected {total_results} results in the last 30 days",
            f"You have {total_tasks} total tasks, with {active_tasks} currently active",
        ]

        if results:
            # ドメイン分析
            domains = set()
            for result in results:
                if result.url:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(result.url).netloc
                        domains.add(domain)
                    except:
                        pass

            insights.append(f"Data collected from {len(domains)} unique domains")

        recommendations = [
            "Consider implementing data validation for better quality",
            "Regular monitoring of spider performance is recommended",
            "Set up alerts for unusual data patterns"
        ]

        return {
            "user_id": current_user.id,
            "analysis_period": "Last 30 days",
            "summary": {
                "total_results": total_results,
                "total_tasks": total_tasks,
                "active_tasks": active_tasks,
                "unique_domains": len(domains) if 'domains' in locals() else 0
            },
            "insights": insights,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard generation failed: {str(e)}"
        )
