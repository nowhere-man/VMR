"""
页面路由

提供 Web 界面的 HTML 页面
"""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..models import JobStatus
from ..services import job_storage

router = APIRouter(tags=["pages"])

# 配置模板
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/jobs/new", response_class=HTMLResponse)
async def create_job_page(request: Request) -> HTMLResponse:
    """创建新任务页面"""
    return templates.TemplateResponse("create_job.html", {"request": request})


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_report_page(request: Request, job_id: str) -> HTMLResponse:
    """任务报告页面"""
    job = job_storage.get_job(job_id)

    if not job:
        # 返回 404 页面
        return templates.TemplateResponse(
            "base.html",
            {
                "request": request,
                "error": f"Job {job_id} not found",
            },
            status_code=404,
        )

    metadata = job.metadata

    # 准备模板数据
    context = {
        "request": request,
        "job": {
            "job_id": metadata.job_id,
            "status": metadata.status.value,
            "mode": metadata.mode.value,
            "created_at": metadata.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": metadata.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "completed_at": (
                metadata.completed_at.strftime("%Y-%m-%d %H:%M:%S")
                if metadata.completed_at
                else None
            ),
            "reference_filename": (
                metadata.reference_video.filename if metadata.reference_video else None
            ),
            "distorted_filename": (
                metadata.distorted_video.filename if metadata.distorted_video else None
            ),
            "preset": metadata.preset,
            "metrics": metadata.metrics,
            "error_message": metadata.error_message,
        },
    }

    return templates.TemplateResponse("job_report.html", context)


@router.get("/jobs", response_class=HTMLResponse)
async def jobs_list_page(
    request: Request, status: Optional[str] = None
) -> HTMLResponse:
    """任务列表页面"""
    # 解析状态过滤
    filter_status = None
    if status:
        try:
            filter_status = JobStatus(status)
        except ValueError:
            pass

    # 获取任务列表
    jobs = job_storage.list_jobs(status=filter_status)

    # 准备模板数据
    jobs_data = [
        {
            "job_id": job.metadata.job_id,
            "status": job.metadata.status.value,
            "mode": job.metadata.mode.value,
            "created_at": job.metadata.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for job in jobs
    ]

    return templates.TemplateResponse(
        "jobs_list.html",
        {
            "request": request,
            "jobs": jobs_data,
            "status": status,
        },
    )
