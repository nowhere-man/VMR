"""
页面路由

提供 Web 界面的 HTML 页面
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.models import JobStatus
from src.services import job_storage
from src.services.template_storage import template_storage

router = APIRouter(tags=["pages"])

# 配置模板
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _fmt_time(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt.strftime("%Y-%m-%d %H:%M:%S")


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
            "created_at": _fmt_time(metadata.created_at),
            "updated_at": _fmt_time(metadata.updated_at),
            "completed_at": _fmt_time(metadata.completed_at),
            "template_name": metadata.template_name,
            "reference_filename": (
                metadata.reference_video.filename if metadata.reference_video else None
            ),
            "distorted_filename": (
                metadata.distorted_video.filename if metadata.distorted_video else None
            ),
            "encoded_filenames": [v.filename for v in (metadata.encoded_videos or [])],
            "preset": metadata.preset,
            "metrics": metadata.metrics,
            "error_message": metadata.error_message,
            "template_a_id": metadata.template_a_id,
            "template_b_id": metadata.template_b_id,
            "comparison_result": metadata.comparison_result,
            "execution_result": metadata.execution_result,
            "command_logs": [
                {
                    "command_id": cmd.command_id,
                    "command_type": cmd.command_type,
                    "command": cmd.command,
                    "status": cmd.status.value,
                    "source_file": cmd.source_file,
                    "started_at": cmd.started_at.isoformat() if cmd.started_at else None,
                    "completed_at": cmd.completed_at.isoformat() if cmd.completed_at else None,
                    "error_message": cmd.error_message,
                }
                for cmd in metadata.command_logs
            ],
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
            "template_name": job.metadata.template_name or "N/A",
            "created_at": _fmt_time(job.metadata.created_at) or "-",
            "completed_at": _fmt_time(job.metadata.completed_at) or "-",
            "error_message": job.metadata.error_message,
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


@router.get("/templates", response_class=HTMLResponse)
async def templates_list_page(request: Request) -> HTMLResponse:
    """转码模板列表页面"""
    return templates.TemplateResponse("templates_list.html", {"request": request})


@router.get("/templates/new", response_class=HTMLResponse)
async def create_template_page(request: Request) -> HTMLResponse:
    """创建新模板页面"""
    return templates.TemplateResponse(
        "template_form.html", {"request": request, "template_id": None}
    )


@router.get("/templates/{template_id}", response_class=HTMLResponse)
async def template_detail_page(request: Request, template_id: str) -> HTMLResponse:
    """模板详情页面（简化：复用表单编辑页）"""
    template = template_storage.get_template(template_id)

    if not template:
        return templates.TemplateResponse(
            "base.html",
            {
                "request": request,
                "error": f"Template {template_id} not found",
            },
            status_code=404,
        )

    return templates.TemplateResponse(
        "template_form.html", {"request": request, "template_id": template_id}
    )


@router.get("/templates/{template_id}/edit", response_class=HTMLResponse)
async def edit_template_page(request: Request, template_id: str) -> HTMLResponse:
    """编辑模板页面"""
    template = template_storage.get_template(template_id)

    if not template:
        return templates.TemplateResponse(
            "base.html",
            {
                "request": request,
                "error": f"Template {template_id} not found",
            },
            status_code=404,
        )

    return templates.TemplateResponse(
        "template_form.html", {"request": request, "template_id": template_id}
    )


@router.get("/bitstream", response_class=HTMLResponse)
async def bitstream_analysis_page(request: Request) -> HTMLResponse:
    """码流分析页面"""
    return templates.TemplateResponse("bitstream_analysis.html", {"request": request})
