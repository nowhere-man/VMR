"""
基于模板的转码服务

使用转码模板执行视频编码任务
"""
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from src.models_template import EncodingTemplate, EncoderType

logger = logging.getLogger(__name__)


class TemplateEncoderService:
    """基于模板的转码服务"""

    def __init__(self):
        """初始化转码服务"""
        self.encoder_paths = {
            EncoderType.FFMPEG: "ffmpeg",
            EncoderType.X264: "x264",
            EncoderType.X265: "x265",
            EncoderType.VVENC: "vvenc",
        }

    async def encode_with_template(
        self, template: EncodingTemplate, source_files: Optional[List[Path]] = None
    ) -> dict:
        """
        使用模板执行转码任务

        Args:
            template: 转码模板
            source_files: 可选的源文件列表，如果不提供则使用模板中的 source_path

        Returns:
            包含转码结果信息的字典
        """
        # 获取源文件列表
        if source_files is None:
            source_files = self._resolve_source_files(template.metadata.source_path)

        if not source_files:
            raise ValueError(f"未找到源文件: {template.metadata.source_path}")

        logger.info(
            f"使用模板 {template.name} 转码 {len(source_files)} 个文件"
        )

        # 准备输出目录
        output_dir = Path(template.metadata.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 准备报告目录
        if template.metadata.enable_metrics:
            metrics_dir = Path(template.metadata.metrics_report_dir)
            metrics_dir.mkdir(parents=True, exist_ok=True)

        # 执行转码任务
        results = []
        failed = []

        # 根据并行任务数决定执行方式
        if template.metadata.parallel_jobs == 1:
            # 串行执行
            for source_file in source_files:
                try:
                    result = await self._encode_single_file(template, source_file)
                    results.append(result)
                except Exception as e:
                    logger.error(f"转码失败 {source_file}: {str(e)}")
                    failed.append({"file": str(source_file), "error": str(e)})
        else:
            # 并行执行
            tasks = []
            for source_file in source_files:
                task = self._encode_single_file(template, source_file)
                tasks.append(task)

            # 分批执行
            batch_size = template.metadata.parallel_jobs
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i : i + batch_size]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)

                for idx, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        source_file = source_files[i + idx]
                        logger.error(f"转码失败 {source_file}: {str(result)}")
                        failed.append({"file": str(source_file), "error": str(result)})
                    else:
                        results.append(result)

        return {
            "template_id": template.template_id,
            "template_name": template.name,
            "total_files": len(source_files),
            "successful": len(results),
            "failed": len(failed),
            "results": results,
            "errors": failed,
        }

    async def _encode_single_file(
        self, template: EncodingTemplate, source_file: Path
    ) -> dict:
        """
        转码单个文件

        Args:
            template: 转码模板
            source_file: 源文件路径

        Returns:
            包含转码结果的字典
        """
        # 构建输出文件路径
        output_file = (
            Path(template.metadata.output_dir)
            / f"{source_file.stem}_encoded.{template.metadata.output_format}"
        )

        # 获取编码器命令
        encoder_cmd = self._build_encoder_command(
            template, source_file, output_file
        )

        logger.info(f"转码: {source_file} -> {output_file}")
        logger.debug(f"命令: {' '.join(encoder_cmd)}")

        # 执行转码
        process = await asyncio.create_subprocess_exec(
            *encoder_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"转码失败: {stderr.decode()}")

        result = {
            "source_file": str(source_file),
            "output_file": str(output_file),
            "encoder_type": template.metadata.encoder_type,
        }

        # 如果启用质量指标计算
        if template.metadata.enable_metrics:
            metrics = await self._calculate_metrics(
                template, source_file, output_file
            )
            result["metrics"] = metrics

        return result

    def _build_encoder_command(
        self, template: EncodingTemplate, source_file: Path, output_file: Path
    ) -> List[str]:
        """
        构建编码器命令

        Args:
            template: 转码模板
            source_file: 源文件路径
            output_file: 输出文件路径

        Returns:
            编码器命令列表
        """
        encoder_type = template.metadata.encoder_type
        encoder_path = self.encoder_paths.get(encoder_type)

        if encoder_type == EncoderType.FFMPEG:
            # FFmpeg 命令格式
            cmd = [
                encoder_path,
                "-i",
                str(source_file),
            ]
            # 添加用户自定义参数
            if template.metadata.encoder_params:
                cmd.extend(template.metadata.encoder_params.split())
            cmd.append(str(output_file))

        elif encoder_type in [EncoderType.X264, EncoderType.X265]:
            # x264/x265 命令格式
            cmd = [
                encoder_path,
                template.metadata.encoder_params,
                "-o",
                str(output_file),
                str(source_file),
            ]

        elif encoder_type == EncoderType.VVENC:
            # vvenc 命令格式
            cmd = [
                encoder_path,
                "-i",
                str(source_file),
                "-o",
                str(output_file),
            ]
            if template.metadata.encoder_params:
                cmd.extend(template.metadata.encoder_params.split())

        else:
            raise ValueError(f"不支持的编码器类型: {encoder_type}")

        return cmd

    async def _calculate_metrics(
        self, template: EncodingTemplate, reference: Path, distorted: Path
    ) -> dict:
        """
        计算质量指标

        Args:
            template: 转码模板
            reference: 参考视频
            distorted: 待测视频

        Returns:
            包含质量指标的字典
        """
        from .ffmpeg import ffmpeg_service

        metrics = {}
        metrics_dir = Path(template.metadata.metrics_report_dir)

        try:
            # 根据配置计算不同的指标
            if "psnr" in template.metadata.metrics_types:
                psnr_log = metrics_dir / f"{distorted.stem}_psnr.log"
                psnr_result = await ffmpeg_service.calculate_psnr(
                    reference, distorted, psnr_log
                )
                metrics["psnr"] = psnr_result

            if "ssim" in template.metadata.metrics_types:
                ssim_log = metrics_dir / f"{distorted.stem}_ssim.log"
                ssim_result = await ffmpeg_service.calculate_ssim(
                    reference, distorted, ssim_log
                )
                metrics["ssim"] = ssim_result

            if "vmaf" in template.metadata.metrics_types:
                vmaf_json = metrics_dir / f"{distorted.stem}_vmaf.json"
                vmaf_result = await ffmpeg_service.calculate_vmaf(
                    reference, distorted, vmaf_json
                )
                metrics["vmaf"] = vmaf_result

        except Exception as e:
            logger.error(f"计算指标失败: {str(e)}")
            metrics["error"] = str(e)

        return metrics

    def _resolve_source_files(self, source_path: str) -> List[Path]:
        """
        解析源文件路径
        
        支持三种模式：
        1. 单个文件路径: /path/to/video.mp4
        2. 多个文件路径（逗号分隔）: /path/to/video1.mp4,/path/to/video2.mp4
        3. 目录路径: /path/to/videos/

        Args:
            source_path: 源路径

        Returns:
            源文件列表
        """
        # 检查是否包含逗号（多个文件）
        if ',' in source_path:
            files = []
            for file_path in source_path.split(','):
                file_path = file_path.strip()
                if file_path:
                    path = Path(file_path)
                    if path.is_file():
                        files.append(path)
                    else:
                        logger.warning(f"文件不存在: {file_path}")
            return sorted(files)
        
        path = Path(source_path.strip())

        # 如果是文件
        if path.is_file():
            return [path]

        # 如果是目录
        if path.is_dir():
            # 查找所有视频文件
            video_extensions = [".mp4", ".mkv", ".avi", ".mov", ".flv", ".yuv"]
            files = []
            for ext in video_extensions:
                files.extend(path.glob(f"*{ext}"))
            return sorted(files)

        # 如果包含通配符
        if "*" in source_path or "?" in source_path:
            parent = Path(source_path).parent
            pattern = Path(source_path).name
            return sorted(parent.glob(pattern))

        return []


# 全局单例
template_encoder_service = TemplateEncoderService()
