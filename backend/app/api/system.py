from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import subprocess
import psutil
import redis
import requests
import os
import logging
from ..auth import get_current_user
from ..database import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/system",
    tags=["system"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

@router.get("/status")
async def get_system_status():
    """
    システム状態取得

    各種サービスの起動状況を取得します。
    """
    try:
        status_info = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {}
        }

        # Redis状態チェック
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
            r.ping()
            status_info["services"]["redis"] = {
                "status": "running",
                "message": "Redis is responding"
            }
        except Exception as e:
            status_info["services"]["redis"] = {
                "status": "error",
                "message": f"Redis connection failed: {str(e)}"
            }

        # Celeryワーカー状態チェック
        try:
            celery_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'celery' in cmdline.lower() and 'worker' in cmdline.lower():
                        celery_processes.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            status_info["services"]["celery_worker"] = {
                "status": "running" if celery_processes else "stopped",
                "message": f"Found {len(celery_processes)} Celery worker(s)" if celery_processes else "No Celery workers found"
            }
        except Exception as e:
            status_info["services"]["celery_worker"] = {
                "status": "error",
                "message": f"Error checking Celery worker: {str(e)}"
            }

        # FastAPIバックエンド状態チェック
        status_info["services"]["fastapi_backend"] = {
            "status": "running",
            "message": "FastAPI backend is running"
        }

        # SchedulerService状態チェック
        try:
            from ..services.scheduler_service import scheduler_service
            status_info["services"]["scheduler"] = {
                "status": "running" if scheduler_service.running else "stopped",
                "message": f"Scheduler is {'running' if scheduler_service.running else 'stopped'}"
            }
        except Exception as e:
            status_info["services"]["scheduler"] = {
                "status": "error",
                "message": f"Error checking Scheduler service: {str(e)}"
            }

        # Celery Scheduler (Beat) 状態チェック
        try:
            # Celery Beatプロセスの確認
            celery_beat_running = False
            celery_beat_pid = None

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'celery' in cmdline.lower() and 'beat' in cmdline.lower():
                        celery_beat_running = True
                        celery_beat_pid = proc.info['pid']
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if celery_beat_running:
                status_info["services"]["celery_scheduler"] = {
                    "status": "running",
                    "message": f"Celery Beat scheduler is running (PID: {celery_beat_pid})"
                }
            else:
                status_info["services"]["celery_scheduler"] = {
                    "status": "stopped",
                    "message": "Celery Beat scheduler is not running"
                }
        except Exception as e:
            status_info["services"]["celery_scheduler"] = {
                "status": "error",
                "message": f"Error checking Celery Beat scheduler: {str(e)}"
            }

        # Node.js Puppeteerサービス状態チェック
        try:
            # APIキーヘッダーを追加（環境変数から取得、デフォルト値あり）
            api_key = os.getenv("NODEJS_SERVICE_API_KEY", "scrapyui-nodejs-service-key-2024")
            headers = {
                "x-api-key": api_key
            }
            response = requests.get("http://localhost:3001/api/health", headers=headers, timeout=5)
            if response.status_code == 200:
                status_info["services"]["nodejs_puppeteer"] = {
                    "status": "running",
                    "message": "Node.js Puppeteer service is responding"
                }
            else:
                status_info["services"]["nodejs_puppeteer"] = {
                    "status": "error",
                    "message": f"Node.js Puppeteer service returned status {response.status_code}"
                }
        except requests.exceptions.ConnectionError:
            status_info["services"]["nodejs_puppeteer"] = {
                "status": "stopped",
                "message": "Node.js Puppeteer service is not responding"
            }
        except Exception as e:
            status_info["services"]["nodejs_puppeteer"] = {
                "status": "error",
                "message": f"Error checking Node.js Puppeteer service: {str(e)}"
            }

        # フロントエンド (Next.js) 状態チェック
        try:
            response = requests.get("http://localhost:4000", timeout=5)
            if response.status_code == 200:
                status_info["services"]["nextjs_frontend"] = {
                    "status": "running",
                    "message": "Next.js frontend is responding"
                }
            else:
                status_info["services"]["nextjs_frontend"] = {
                    "status": "error",
                    "message": f"Next.js frontend returned status {response.status_code}"
                }
        except requests.exceptions.ConnectionError:
            status_info["services"]["nextjs_frontend"] = {
                "status": "stopped",
                "message": "Next.js frontend is not responding"
            }
        except Exception as e:
            status_info["services"]["nextjs_frontend"] = {
                "status": "error",
                "message": f"Error checking Next.js frontend: {str(e)}"
            }

        return status_info

    except Exception as e:
        return {
            "error": f"Error getting system status: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/metrics")
async def get_system_metrics():
    """
    システムメトリクス取得

    CPU、メモリ、ディスク使用量などのシステムメトリクスを取得します。
    """
    try:
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": {},
            "memory": {},
            "disk": {},
            "network": {}
        }

        # CPU使用率
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)  # 短いintervalに変更
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            metrics["cpu"] = {
                "usage_percent": cpu_percent,
                "count": cpu_count,
                "frequency": {
                    "current": cpu_freq.current if cpu_freq else None,
                    "min": cpu_freq.min if cpu_freq else None,
                    "max": cpu_freq.max if cpu_freq else None
                }
            }
        except Exception as e:
            metrics["cpu"] = {"error": str(e)}

        # メモリ使用量
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            metrics["memory"] = {
                "virtual": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "percent": swap.percent
                }
            }
        except Exception as e:
            metrics["memory"] = {"error": str(e)}

        # ディスク使用量
        try:
            disk_usage = psutil.disk_usage('/')

            metrics["disk"] = {
                "total": disk_usage.total,
                "used": disk_usage.used,
                "free": disk_usage.free,
                "percent": (disk_usage.used / disk_usage.total) * 100
            }
        except Exception as e:
            metrics["disk"] = {"error": str(e)}

        # ネットワーク統計
        try:
            network = psutil.net_io_counters()

            metrics["network"] = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        except Exception as e:
            metrics["network"] = {"error": str(e)}

        return metrics

    except Exception as e:
        return {
            "error": f"Error getting system metrics: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.post("/cleanup/processes")
async def cleanup_processes(current_user: User = Depends(get_current_user)):
    """
    プロセスクリーンアップ実行

    重複プロセスとゾンビプロセスをクリーンアップします。
    管理者権限が必要です。
    """

    # 管理者権限チェック
    if not (current_user.is_superuser or current_user.role.value == "ADMIN"):
        raise HTTPException(
            status_code=403,
            detail="Administrator privileges required for process cleanup"
        )

    try:
        from ..services.process_cleanup_service import process_cleanup_service

        logger.info(f"🧹 Process cleanup requested by user {current_user.email}")

        # 完全なクリーンアップを実行
        cleanup_results = process_cleanup_service.full_cleanup()

        logger.info(f"✅ Process cleanup completed: {cleanup_results}")

        return {
            "success": True,
            "message": "プロセスクリーンアップが正常に完了しました",
            "results": cleanup_results
        }

    except Exception as e:
        logger.error(f"❌ Process cleanup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Process cleanup failed: {str(e)}"
        )

@router.post("/cleanup/zombies")
async def cleanup_zombie_processes(current_user: User = Depends(get_current_user)):
    """
    ゾンビプロセスクリーンアップ

    ゾンビプロセスのみをクリーンアップします。
    管理者権限が必要です。
    """

    # 管理者権限チェック
    if not (current_user.is_superuser or current_user.role.value == "ADMIN"):
        raise HTTPException(
            status_code=403,
            detail="Administrator privileges required for zombie cleanup"
        )

    try:
        from ..services.process_cleanup_service import process_cleanup_service

        logger.info(f"🧟 Zombie cleanup requested by user {current_user.email}")

        # ゾンビプロセスクリーンアップを実行
        zombie_results = process_cleanup_service.cleanup_zombie_processes()

        logger.info(f"✅ Zombie cleanup completed: {zombie_results}")

        return {
            "success": True,
            "message": "ゾンビプロセスクリーンアップが正常に完了しました",
            "results": zombie_results
        }

    except Exception as e:
        logger.error(f"❌ Zombie cleanup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Zombie cleanup failed: {str(e)}"
        )

@router.post("/cleanup/duplicates")
async def cleanup_duplicate_processes(current_user: User = Depends(get_current_user)):
    """
    重複プロセスクリーンアップ

    重複プロセスのみをクリーンアップします。
    管理者権限が必要です。
    """

    # 管理者権限チェック
    if not (current_user.is_superuser or current_user.role.value == "ADMIN"):
        raise HTTPException(
            status_code=403,
            detail="Administrator privileges required for duplicate cleanup"
        )

    try:
        from ..services.process_cleanup_service import process_cleanup_service

        logger.info(f"🔄 Duplicate cleanup requested by user {current_user.email}")

        # 重複プロセスクリーンアップを実行
        duplicate_results = process_cleanup_service.cleanup_duplicate_processes()

        logger.info(f"✅ Duplicate cleanup completed: {duplicate_results}")

        return {
            "success": True,
            "message": "重複プロセスクリーンアップが正常に完了しました",
            "results": duplicate_results
        }

    except Exception as e:
        logger.error(f"❌ Duplicate cleanup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Duplicate cleanup failed: {str(e)}"
        )
