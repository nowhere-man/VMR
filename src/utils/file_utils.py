"""文件操作工具函数（仅保留当前使用的能力）"""
from pathlib import Path

from src.models import VideoInfo


def save_uploaded_file(file_content: bytes, destination: Path) -> None:
    """保存上传的文件到指定路径"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "wb") as f:
        f.write(file_content)


def extract_video_info(file_path: Path) -> VideoInfo:
    """
    提取视频文件基础信息（文件名、大小）。
    其他元数据如时长/分辨率后续由 ffmpeg 获取。
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_stat = file_path.stat()
    return VideoInfo(
        filename=file_path.name,
        size_bytes=file_stat.st_size,
        duration=None,
        width=None,
        height=None,
        fps=None,
        bitrate=None,
    )
