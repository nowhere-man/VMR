"""
API 端点实现 - 任务管理

提供任务创建、查询、列表等 RESTful API
"""
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..models import JobMetadata, JobMode, JobStatus
from ..schemas import CreateJobResponse, ErrorResponse, JobDetailResponse, JobListItem
from ..services import job_storage
from ..utils import extract_video_info, save_uploaded_file

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post(
    "",
    response_model=CreateJobResponse,
    status_code=201,
    responses={400: {"model": ErrorResponse}},
)
async def create_job(
    mode: str = Form(...),
    file: Optional[UploadFile] = File(None),
    reference: Optional[UploadFile] = File(None),
    distorted: Optional[UploadFile] = File(None),
    preset: Optional[str] = Form("medium"),
) -> CreateJobResponse:
    """
    创建新的视频质量分析任务

    - **mode**: 任务模式 (single_file 或 dual_file)
    - **file**: 单文件模式下的视频文件
    - **reference**: 双文件模式下的参考视频
    - **distorted**: 双文件模式下的待测视频
    - **preset**: 单文件模式下的转码预设（默认 medium）
    """
    # 验证模式
    try:
        job_mode = JobMode(mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {mode}. Must be 'single_file' or 'dual_file'",
        )

    # 生成任务 ID
    job_id = job_storage.generate_job_id()

    # 创建任务元数据
    metadata = JobMetadata(
        job_id=job_id,
        status=JobStatus.PENDING,
        mode=job_mode,
    )

    # 单文件模式
    if job_mode == JobMode.SINGLE_FILE:
        if not file:
            raise HTTPException(
                status_code=400,
                detail="File is required for single_file mode",
            )

        # 保存转码预设
        metadata.preset = preset

        # 创建任务
        job = job_storage.create_job(metadata)

        # 保存上传的文件
        file_content = await file.read()
        file_path = job.job_dir / file.filename
        save_uploaded_file(file_content, file_path)

        # 提取视频信息
        video_info = extract_video_info(file_path)
        metadata.reference_video = video_info

        # 更新元数据
        job_storage.update_job(job)

    # 双文件模式
    elif job_mode == JobMode.DUAL_FILE:
        if not reference:
            raise HTTPException(
                status_code=400,
                detail="Reference file is required for dual_file mode",
            )
        if not distorted:
            raise HTTPException(
                status_code=400,
                detail="Distorted file is required for dual_file mode",
            )

        # 创建任务
        job = job_storage.create_job(metadata)

        # 保存参考视频
        reference_content = await reference.read()
        reference_path = job.job_dir / reference.filename
        save_uploaded_file(reference_content, reference_path)
        metadata.reference_video = extract_video_info(reference_path)

        # 保存待测视频
        distorted_content = await distorted.read()
        distorted_path = job.job_dir / distorted.filename
        save_uploaded_file(distorted_content, distorted_path)
        metadata.distorted_video = extract_video_info(distorted_path)

        # 更新元数据
        job_storage.update_job(job)

    # 返回响应
    return CreateJobResponse(
        job_id=metadata.job_id,
        status=metadata.status,
        mode=metadata.mode,
        created_at=metadata.created_at,
    )


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_job(job_id: str) -> JobDetailResponse:
    """
    获取任务详情

    - **job_id**: 任务 ID
    """
    job = job_storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    metadata = job.metadata

    return JobDetailResponse(
        job_id=metadata.job_id,
        status=metadata.status,
        mode=metadata.mode,
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
        completed_at=metadata.completed_at,
        reference_filename=(
            metadata.reference_video.filename if metadata.reference_video else None
        ),
        distorted_filename=(
            metadata.distorted_video.filename if metadata.distorted_video else None
        ),
        preset=metadata.preset,
        metrics=metadata.metrics,
        error_message=metadata.error_message,
    )


@router.get("", response_model=List[JobListItem])
async def list_jobs(
    status: Optional[JobStatus] = None,
    limit: Optional[int] = None,
) -> List[JobListItem]:
    """
    列出所有任务

    - **status**: 可选的状态过滤
    - **limit**: 可选的数量限制
    """
    jobs = job_storage.list_jobs(status=status, limit=limit)

    return [
        JobListItem(
            job_id=job.metadata.job_id,
            status=job.metadata.status,
            mode=job.metadata.mode,
            created_at=job.metadata.created_at,
        )
        for job in jobs
    ]
