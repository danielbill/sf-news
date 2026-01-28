"""调度器管理 API"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..scheduler import SchedulerManager, JobExecutionStore

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])

# 全局调度器实例
_scheduler: SchedulerManager = None


def get_scheduler() -> SchedulerManager:
    """获取调度器实例"""
    global _scheduler
    if _scheduler is None:
        raise HTTPException(status_code=400, detail="调度器未初始化")
    return _scheduler


def set_scheduler(scheduler: SchedulerManager):
    """设置调度器实例"""
    global _scheduler
    _scheduler = scheduler


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """获取调度器状态"""
    try:
        scheduler = get_scheduler()
        return {
            "code": 200,
            "message": "success",
            "data": scheduler.status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("/start")
async def start_scheduler() -> Dict[str, Any]:
    """启动调度器"""
    try:
        scheduler = get_scheduler()
        await scheduler.start()
        return {
            "code": 200,
            "message": "调度器已启动",
            "data": scheduler.status
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.post("/stop")
async def stop_scheduler() -> Dict[str, Any]:
    """停止调度器"""
    try:
        scheduler = get_scheduler()
        await scheduler.stop()
        return {
            "code": 200,
            "message": "调度器已停止",
            "data": scheduler.status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止失败: {str(e)}")


@router.post("/pause")
async def pause_scheduler() -> Dict[str, Any]:
    """暂停调度器"""
    try:
        scheduler = get_scheduler()
        await scheduler.pause()
        return {
            "code": 200,
            "message": "调度器已暂停",
            "data": scheduler.status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"暂停失败: {str(e)}")


@router.post("/resume")
async def resume_scheduler() -> Dict[str, Any]:
    """恢复调度器"""
    try:
        scheduler = get_scheduler()
        await scheduler.resume()
        return {
            "code": 200,
            "message": "调度器已恢复",
            "data": scheduler.status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")


@router.get("/jobs")
async def get_jobs(limit: int = 10) -> Dict[str, Any]:
    """获取任务执行历史"""
    try:
        store = JobExecutionStore()
        jobs = store.get_recent_jobs(limit)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "jobs": jobs,
                "count": len(jobs)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")
