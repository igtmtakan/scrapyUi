"""
拡張機能API
Git統合、テンプレート管理、設定検証、リアルタイム編集のAPIエンドポイント
"""
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import json

from app.database import get_db, Project
from app.services.git_service import GitService, VersionManager
from app.services.template_service import TemplateService, TemplateType, Template
from app.services.config_validator import ScrapyConfigValidator
from app.services.performance_monitor import performance_monitor
from app.services.usage_analytics import usage_analytics
from app.services.predictive_analytics import predictive_analytics
from app.services.ai_integration import ai_analyzer
from app.websocket.realtime_editor import realtime_manager
from app.models.schemas import (
    ProjectFileCreate, ProjectFileUpdate, ProjectFileResponse
)

router = APIRouter()

# サービスインスタンス
git_service = GitService()
version_manager = VersionManager()
template_service = TemplateService()
config_validator = ScrapyConfigValidator()


# =============================================================================
# Git統合API
# =============================================================================

@router.post("/projects/{project_id}/git/init")
async def init_git_repository(project_id: str, db: Session = Depends(get_db)):
    """Gitリポジトリを初期化"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    success, error = git_service.init_repository(project_id)
    if not success:
        raise HTTPException(status_code=500, detail=error)

    return {"message": "Git repository initialized successfully"}


@router.get("/projects/{project_id}/git/status")
async def get_git_status(project_id: str, db: Session = Depends(get_db)):
    """Gitステータスを取得"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not git_service.is_git_repository(project_id):
        raise HTTPException(status_code=400, detail="Not a git repository")

    status = git_service.get_status(project_id)
    return status


@router.get("/projects/{project_id}/git/commits")
async def get_commit_history(
    project_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """コミット履歴を取得"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not git_service.is_git_repository(project_id):
        raise HTTPException(status_code=400, detail="Not a git repository")

    commits = git_service.get_commit_history(project_id, limit)
    return {"commits": commits}


@router.post("/projects/{project_id}/git/commit")
async def create_commit(
    project_id: str,
    commit_data: Dict,
    db: Session = Depends(get_db)
):
    """コミットを作成"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not git_service.is_git_repository(project_id):
        raise HTTPException(status_code=400, detail="Not a git repository")

    message = commit_data.get("message", "")
    author = commit_data.get("author", "ScrapyUI")

    if not message:
        raise HTTPException(status_code=400, detail="Commit message is required")

    # 全ファイルを追加
    success, error = git_service.add_all_files(project_id)
    if not success:
        raise HTTPException(status_code=500, detail=error)

    # コミット
    success, result = git_service.commit(project_id, message, author)
    if not success:
        raise HTTPException(status_code=500, detail=result)

    return {"message": "Commit created successfully", "result": result}


@router.get("/projects/{project_id}/git/branches")
async def get_branches(project_id: str, db: Session = Depends(get_db)):
    """ブランチ一覧を取得"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not git_service.is_git_repository(project_id):
        raise HTTPException(status_code=400, detail="Not a git repository")

    branches = git_service.list_branches(project_id)
    return {"branches": branches}


@router.post("/projects/{project_id}/git/branches")
async def create_branch(
    project_id: str,
    branch_data: Dict,
    db: Session = Depends(get_db)
):
    """新しいブランチを作成"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    branch_name = branch_data.get("name", "")
    if not branch_name:
        raise HTTPException(status_code=400, detail="Branch name is required")

    success, error = git_service.create_branch(project_id, branch_name)
    if not success:
        raise HTTPException(status_code=500, detail=error)

    return {"message": f"Branch '{branch_name}' created successfully"}


# =============================================================================
# テンプレート管理API
# =============================================================================

@router.get("/templates")
async def list_templates(
    template_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None
):
    """テンプレート一覧を取得"""
    filters = {}

    if template_type:
        try:
            filters['template_type'] = TemplateType(template_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid template type")

    if category:
        filters['category'] = category

    if tags:
        filters['tags'] = tags.split(',')

    templates = template_service.list_templates(**filters)
    return {"templates": [template.__dict__ for template in templates]}


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """特定のテンプレートを取得"""
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"template": template.__dict__}


@router.post("/templates")
async def create_template(template_data: Dict):
    """新しいテンプレートを作成"""
    try:
        template_type = TemplateType(template_data.get("type"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template type")

    required_fields = ["name", "description", "content"]
    for field in required_fields:
        if field not in template_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    # 変数を自動抽出
    variables = template_service.extract_variables(template_data["content"])

    template_id = template_service.create_template(
        name=template_data["name"],
        description=template_data["description"],
        template_type=template_type,
        content=template_data["content"],
        variables=variables,
        tags=template_data.get("tags", []),
        author=template_data.get("author", "ScrapyUI"),
        category=template_data.get("category", "custom")
    )

    return {"template_id": template_id, "message": "Template created successfully"}


@router.put("/templates/{template_id}")
async def update_template(template_id: str, template_data: Dict):
    """テンプレートを更新"""
    success = template_service.update_template(
        template_id=template_id,
        name=template_data.get("name"),
        description=template_data.get("description"),
        content=template_data.get("content"),
        variables=template_data.get("variables"),
        tags=template_data.get("tags"),
        category=template_data.get("category")
    )

    if not success:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Template updated successfully"}


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """テンプレートを削除"""
    success = template_service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Template deleted successfully"}


@router.post("/templates/{template_id}/render")
async def render_template(template_id: str, render_data: Dict):
    """テンプレートをレンダリング"""
    variables = render_data.get("variables", {})

    success, result = template_service.render_template(template_id, variables)
    if not success:
        raise HTTPException(status_code=400, detail=result)

    return {"rendered_content": result}


# =============================================================================
# 設定検証API
# =============================================================================

@router.post("/projects/{project_id}/validate-settings")
async def validate_project_settings(
    project_id: str,
    settings_content: Dict,
    db: Session = Depends(get_db)
):
    """プロジェクト設定を検証"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = settings_content.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Settings content is required")

    # 設定を検証
    validation_results = config_validator.validate_settings_file(content)

    # 最適化レポートを生成
    try:
        import ast
        tree = ast.parse(content)
        settings = config_validator._extract_settings(tree)
        optimization_report = config_validator.generate_optimization_report(settings)
    except:
        optimization_report = {}

    return {
        "validation_results": [result.__dict__ for result in validation_results],
        "optimization_report": optimization_report
    }


# =============================================================================
# パフォーマンス監視API
# =============================================================================

@router.post("/projects/{project_id}/monitoring/start")
async def start_performance_monitoring(
    project_id: str,
    spider_name: str = None,
    db: Session = Depends(get_db)
):
    """パフォーマンス監視を開始"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    performance_monitor.start_monitoring(project_id, spider_name)
    return {"message": "Performance monitoring started"}


@router.post("/projects/{project_id}/monitoring/stop")
async def stop_performance_monitoring(
    project_id: str,
    spider_name: str = None,
    db: Session = Depends(get_db)
):
    """パフォーマンス監視を停止"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    performance_monitor.stop_monitoring(project_id, spider_name)
    return {"message": "Performance monitoring stopped"}


@router.get("/projects/{project_id}/monitoring/stats")
async def get_real_time_stats(project_id: str, db: Session = Depends(get_db)):
    """リアルタイム統計を取得"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stats = performance_monitor.get_real_time_stats(project_id)
    return stats


@router.get("/projects/{project_id}/monitoring/report")
async def get_performance_report(
    project_id: str,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """パフォーマンスレポートを取得"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    report = performance_monitor.generate_performance_report(project_id, days)
    return report


# =============================================================================
# 使用統計API
# =============================================================================

@router.post("/analytics/track")
async def track_usage_event(event_data: Dict):
    """使用イベントを追跡"""
    required_fields = ["user_id", "project_id", "event_type", "event_category"]
    for field in required_fields:
        if field not in event_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    event_id = usage_analytics.track_event(
        user_id=event_data["user_id"],
        project_id=event_data["project_id"],
        event_type=event_data["event_type"],
        event_category=event_data["event_category"],
        metadata=event_data.get("metadata", {}),
        session_id=event_data.get("session_id"),
        duration=event_data.get("duration")
    )

    return {"event_id": event_id}


@router.get("/projects/{project_id}/analytics/summary")
async def get_usage_summary(
    project_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """使用統計サマリーを取得"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    summary = usage_analytics.get_usage_summary(project_id, days)
    return summary


@router.get("/analytics/features/popularity")
async def get_feature_popularity(days: int = 30):
    """機能の人気度を取得"""
    popularity = usage_analytics.get_feature_popularity(days)
    return popularity


@router.get("/projects/{project_id}/analytics/insights")
async def get_usage_insights(
    project_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """使用統計インサイトを取得"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    insights = usage_analytics.generate_insights(project_id, days)
    return insights


# =============================================================================
# 予測分析API
# =============================================================================

@router.get("/projects/{project_id}/predictions/performance")
async def predict_performance_issues(
    project_id: str,
    days_ahead: int = 7,
    db: Session = Depends(get_db)
):
    """パフォーマンス問題を予測"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    predictions = predictive_analytics.predict_performance_issues(project_id, days_ahead)
    return {"predictions": [pred.__dict__ for pred in predictions]}


@router.get("/projects/{project_id}/predictions/anomalies")
async def detect_anomalies(
    project_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """異常を検知"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    anomalies = predictive_analytics.detect_anomalies(project_id, hours)
    return {"anomalies": [anomaly.__dict__ for anomaly in anomalies]}


@router.get("/projects/{project_id}/predictions/resources")
async def predict_resource_usage(project_id: str, db: Session = Depends(get_db)):
    """リソース使用量を予測"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    predictions = predictive_analytics.predict_resource_usage(project_id)
    return predictions


@router.get("/projects/{project_id}/spiders/{spider_name}/predictions")
async def predict_spider_performance(
    project_id: str,
    spider_name: str,
    db: Session = Depends(get_db)
):
    """スパイダーパフォーマンスを予測"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    predictions = predictive_analytics.predict_spider_performance(project_id, spider_name)
    return predictions


# =============================================================================
# AI統合API
# =============================================================================

@router.post("/ai/generate/spider")
async def generate_spider_code(requirements: Dict):
    """AIでスパイダーコードを生成"""
    required_fields = ["spider_name", "target_url"]
    for field in required_fields:
        if field not in requirements:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    suggestion = ai_analyzer.generate_spider_code(requirements)
    return {"suggestion": suggestion.__dict__}


@router.post("/ai/analyze/code")
async def analyze_code_quality(code_data: Dict):
    """AIでコード品質を分析"""
    if "code" not in code_data:
        raise HTTPException(status_code=400, detail="Missing required field: code")

    bugs = ai_analyzer.analyze_code_quality(
        code=code_data["code"],
        file_type=code_data.get("file_type", "spider")
    )

    return {"bugs": [bug.__dict__ for bug in bugs]}


@router.post("/ai/optimize/code")
async def suggest_code_optimizations(optimization_data: Dict):
    """AIでコード最適化を提案"""
    if "code" not in optimization_data:
        raise HTTPException(status_code=400, detail="Missing required field: code")

    suggestions = ai_analyzer.suggest_optimizations(
        code=optimization_data["code"],
        performance_data=optimization_data.get("performance_data")
    )

    return {"suggestions": [suggestion.__dict__ for suggestion in suggestions]}


@router.post("/ai/generate/middleware")
async def generate_middleware_code(middleware_data: Dict):
    """AIでミドルウェアコードを生成"""
    if "middleware_type" not in middleware_data:
        raise HTTPException(status_code=400, detail="Missing required field: middleware_type")

    suggestion = ai_analyzer.generate_middleware_code(
        middleware_type=middleware_data["middleware_type"],
        requirements=middleware_data.get("requirements", {})
    )

    if not suggestion:
        raise HTTPException(status_code=400, detail="Unsupported middleware type")

    return {"suggestion": suggestion.__dict__}


# =============================================================================
# リアルタイム編集WebSocket
# =============================================================================

@router.websocket("/projects/{project_id}/files/{file_path:path}/edit")
async def websocket_realtime_edit(
    websocket: WebSocket,
    project_id: str,
    file_path: str,
    user_id: str,
    user_name: str = "Anonymous"
):
    """リアルタイム編集WebSocket接続"""
    try:
        # ユーザーを接続
        await realtime_manager.connect_user(
            websocket, user_id, user_name, project_id, file_path
        )

        while True:
            # メッセージを受信
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "edit_operation":
                await realtime_manager.handle_edit_operation(user_id, message.get("data", {}))
            elif message_type == "cursor_update":
                await realtime_manager.handle_cursor_update(user_id, message.get("data", {}))
            elif message_type == "save_file":
                await realtime_manager.save_file(user_id)

    except WebSocketDisconnect:
        await realtime_manager.disconnect_user(user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await realtime_manager.disconnect_user(user_id)
