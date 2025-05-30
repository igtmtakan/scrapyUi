from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel, HttpUrl
import logging

from ...services.nodejs_client import get_nodejs_client
from ..auth import get_current_active_user
from ...database import User as DBUser

logger = logging.getLogger(__name__)

router = APIRouter()

class NodeJSHealthResponse(BaseModel):
    status: str
    nodejs_service: Dict[str, Any]
    integration_status: str

class TestConnectionRequest(BaseModel):
    message: Optional[str] = "Test from FastAPI"
    data: Optional[Dict[str, Any]] = None

class SPAScrapingRequest(BaseModel):
    url: HttpUrl
    wait_for: Optional[str] = None
    timeout: Optional[int] = 30000
    extract_data: Optional[Dict[str, Any]] = None
    screenshot: Optional[bool] = False

class DynamicScrapingRequest(BaseModel):
    url: HttpUrl
    actions: Optional[list] = []
    extract_after: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = 30000

class PDFGenerationRequest(BaseModel):
    url: Optional[HttpUrl] = None
    html: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class ScreenshotRequest(BaseModel):
    url: HttpUrl
    options: Optional[Dict[str, Any]] = None

# Workflow related models
class WorkflowStepModel(BaseModel):
    name: str
    type: str  # navigate, scrape, screenshot, pdf, interact, wait, script
    url: Optional[str] = None
    selectors: Optional[Dict[str, str]] = None
    javascript: Optional[str] = None
    actions: Optional[list] = None
    timeout: Optional[int] = None
    outputVariable: Optional[str] = None

class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    steps: list[WorkflowStepModel]
    timeout: Optional[int] = None
    retryAttempts: Optional[int] = None
    continueOnError: Optional[bool] = None
    parallel: Optional[bool] = None

class WorkflowExecuteRequest(BaseModel):
    variables: Optional[Dict[str, Any]] = None

class CommandExecuteRequest(BaseModel):
    command: str
    working_directory: Optional[str] = None
    timeout: Optional[int] = 30000

@router.get("/health", response_model=NodeJSHealthResponse)
async def check_nodejs_health():
    """Check Node.js service health and integration status"""
    try:
        client = await get_nodejs_client()
        response = await client.health_check()

        if response.success:
            return NodeJSHealthResponse(
                status="healthy",
                nodejs_service=response.data,
                integration_status="connected"
            )
        else:
            return NodeJSHealthResponse(
                status="unhealthy",
                nodejs_service={"error": response.error},
                integration_status="disconnected"
            )
    except Exception as e:
        logger.error(f"Failed to check Node.js health: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Node.js service health check failed: {str(e)}"
        )

@router.post("/test")
async def test_nodejs_connection(
    request: TestConnectionRequest,
    current_user: DBUser = Depends(get_current_active_user)
):
    """Test connection to Node.js service"""
    try:
        client = await get_nodejs_client()
        test_data = {
            "message": request.message,
            "user_id": current_user.id,
            "timestamp": "2024-01-01T00:00:00Z",
            "additional_data": request.data
        }

        response = await client.test_connection(test_data)

        if response.success:
            return {
                "success": True,
                "message": "Node.js service connection successful",
                "nodejs_response": response.data
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Node.js service error: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test Node.js connection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection test failed: {str(e)}"
        )

@router.post("/scraping/spa")
async def scrape_spa(
    request: SPAScrapingRequest,
    current_user: DBUser = Depends(get_current_active_user)
):
    """Scrape Single Page Application using Node.js service"""
    try:
        client = await get_nodejs_client()

        options = {
            "waitFor": request.wait_for,
            "timeout": request.timeout,
            "extractData": request.extract_data,
            "screenshot": request.screenshot
        }

        response = await client.scrape_spa(str(request.url), options)

        if response.success:
            return {
                "success": True,
                "message": "SPA scraping completed",
                "data": response.data,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"SPA scraping failed: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SPA scraping failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"SPA scraping error: {str(e)}"
        )

@router.post("/scraping/dynamic")
async def scrape_dynamic_content(
    request: DynamicScrapingRequest,
    current_user: DBUser = Depends(get_current_active_user)
):
    """Scrape dynamic content with actions using Node.js service"""
    try:
        client = await get_nodejs_client()

        options = {
            "actions": request.actions,
            "extractAfter": request.extract_after,
            "timeout": request.timeout
        }

        response = await client.scrape_dynamic_content(str(request.url), request.actions, options)

        if response.success:
            return {
                "success": True,
                "message": "Dynamic content scraping completed",
                "data": response.data,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Dynamic scraping failed: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dynamic scraping failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Dynamic scraping error: {str(e)}"
        )

@router.post("/pdf/generate")
async def generate_pdf(
    request: PDFGenerationRequest,
    current_user: DBUser = Depends(get_current_active_user)
):
    """Generate PDF using Node.js service"""
    try:
        if not request.url and not request.html:
            raise HTTPException(
                status_code=400,
                detail="Either url or html must be provided"
            )

        client = await get_nodejs_client()

        response = await client.generate_pdf(
            url=str(request.url) if request.url else None,
            html=request.html,
            options=request.options
        )

        if response.success:
            return {
                "success": True,
                "message": "PDF generation completed",
                "data": response.data,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"PDF generation failed: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation error: {str(e)}"
        )

@router.post("/screenshot/capture")
async def capture_screenshot(
    request: ScreenshotRequest,
    current_user: DBUser = Depends(get_current_active_user)
):
    """Capture screenshot using Node.js service"""
    try:
        client = await get_nodejs_client()

        response = await client.capture_screenshot(str(request.url), request.options)

        if response.success:
            return {
                "success": True,
                "message": "Screenshot capture completed",
                "data": response.data,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Screenshot capture failed: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Screenshot capture failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Screenshot capture error: {str(e)}"
        )

# Workflow endpoints
@router.get("/workflows")
async def get_workflows(
    current_user: DBUser = Depends(get_current_active_user)
):
    """Get all workflows from Node.js service"""
    try:
        client = await get_nodejs_client()
        response = await client.get_workflows()

        if response.success:
            return {
                "success": True,
                "message": "Workflows retrieved successfully",
                "data": response.data,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get workflows: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflows: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow retrieval error: {str(e)}"
        )

@router.post("/workflows")
async def create_workflow(
    request: WorkflowCreateRequest,
    current_user: DBUser = Depends(get_current_active_user)
):
    """Create a new workflow using Node.js service"""
    try:
        client = await get_nodejs_client()

        workflow_data = {
            "name": request.name,
            "description": request.description,
            "steps": [step.model_dump(exclude_none=True) for step in request.steps]
        }

        # Add optional fields only if they are not None
        if request.timeout is not None:
            workflow_data["timeout"] = request.timeout
        if request.retryAttempts is not None:
            workflow_data["retryAttempts"] = request.retryAttempts
        if request.continueOnError is not None:
            workflow_data["continueOnError"] = request.continueOnError
        if request.parallel is not None:
            workflow_data["parallel"] = request.parallel

        response = await client.create_workflow(workflow_data)

        if response.success:
            return {
                "success": True,
                "message": "Workflow created successfully",
                "data": response.data,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create workflow: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow creation error: {str(e)}"
        )

@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    current_user: DBUser = Depends(get_current_active_user)
):
    """Get a specific workflow by ID from Node.js service"""
    try:
        client = await get_nodejs_client()
        response = await client.get_workflow(workflow_id)

        if response.success:
            return {
                "success": True,
                "message": "Workflow retrieved successfully",
                "data": response.data,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get workflow: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow retrieval error: {str(e)}"
        )

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    current_user: DBUser = Depends(get_current_active_user)
):
    """Execute a workflow using Node.js service"""
    try:
        client = await get_nodejs_client()
        response = await client.execute_workflow(workflow_id, request.variables)

        if response.success:
            return {
                "success": True,
                "message": "Workflow execution started successfully",
                "data": response.data,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to execute workflow: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution error: {str(e)}"
        )

@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: DBUser = Depends(get_current_active_user)
):
    """Delete a workflow using Node.js service"""
    try:
        client = await get_nodejs_client()
        response = await client.delete_workflow(workflow_id)

        if response.success:
            return {
                "success": True,
                "message": "Workflow deleted successfully",
                "data": response.data,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to delete workflow: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow deletion error: {str(e)}"
        )

@router.get("/workflows/{workflow_id}/executions")
async def get_workflow_executions(
    workflow_id: str,
    current_user: DBUser = Depends(get_current_active_user)
):
    """Get workflow execution history from Node.js service"""
    try:
        client = await get_nodejs_client()
        response = await client.get_workflow_executions(workflow_id)

        if response.success:
            return {
                "success": True,
                "message": "Workflow executions retrieved successfully",
                "data": response.data,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get workflow executions: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow executions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow executions retrieval error: {str(e)}"
        )

@router.get("/workflows/templates/list")
async def get_workflow_templates(
    current_user: DBUser = Depends(get_current_active_user)
):
    """Get workflow templates from Node.js service"""
    try:
        client = await get_nodejs_client()
        response = await client.get_workflow_templates()

        if response.success:
            return {
                "success": True,
                "message": "Workflow templates retrieved successfully",
                "data": response.data,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get workflow templates: {response.error}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow templates retrieval error: {str(e)}"
        )

@router.post("/execute")
async def execute_command(
    request: CommandExecuteRequest,
    current_user: DBUser = Depends(get_current_active_user)
):
    """Execute a command using Node.js service"""
    try:
        import os

        # プロジェクトディレクトリが存在しない場合は作成
        if request.working_directory and not os.path.exists(request.working_directory):
            # scrapy_projectsディレクトリ内の場合のみ自動作成
            if "scrapy_projects" in request.working_directory:
                try:
                    os.makedirs(request.working_directory, exist_ok=True)
                    logger.info(f"Created working directory: {request.working_directory}")
                except Exception as e:
                    logger.error(f"Failed to create working directory: {str(e)}")
                    return {
                        "output": "",
                        "error": f"Failed to create working directory: {str(e)}",
                        "exit_code": 1
                    }

        client = await get_nodejs_client()

        command_data = {
            "command": request.command,
            "workingDir": request.working_directory,
            "timeout": request.timeout
        }

        response = await client.execute_command(command_data)

        if response.success:
            return {
                "output": response.data.get("stdout", ""),
                "error": response.data.get("stderr", ""),
                "exit_code": response.data.get("exitCode", 0)
            }
        else:
            return {
                "output": "",
                "error": response.error or "Command execution failed",
                "exit_code": 1
            }
    except Exception as e:
        logger.error(f"Command execution failed: {str(e)}")
        return {
            "output": "",
            "error": f"Command execution error: {str(e)}",
            "exit_code": 1
        }
