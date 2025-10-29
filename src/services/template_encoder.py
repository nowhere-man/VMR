"""
基于模板的转码服务

使用转码模板执行视频编码任务
"""
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import List, Optional

import psutil

from src.models_template import EncodingTemplate, EncoderType, TemplateMode

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
        使用模板执行任务（根据模式：转码+分析、仅分析、仅转码）

        Args:
            template: 转码模板
            source_files: 可选的源文件列表，如果不提供则使用模板中的 source_path

        Returns:
            包含执行结果信息的字典
        """
        mode = template.metadata.mode
        
        # 根据模式选择不同的执行路径
        if mode == TemplateMode.ANALYZE_ONLY:
            return await self._analyze_only(template, source_files)
        elif mode == TemplateMode.TRANSCODE_ONLY:
            return await self._transcode_only(template, source_files)
        else:  # TRANSCODE_AND_ANALYZE
            return await self._transcode_and_analyze(template, source_files)

    async def _transcode_and_analyze(
        self, template: EncodingTemplate, source_files: Optional[List[Path]] = None
    ) -> dict:
        """转码+质量分析模式"""
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

        def _mean(values: List[Optional[float]]) -> Optional[float]:
            valid = [v for v in values if isinstance(v, (int, float))]
            if not valid:
                return None
            return sum(valid) / len(valid)

        average_speed = _mean([res.get("average_fps") for res in results])
        average_cpu = _mean([res.get("cpu_percent") for res in results])
        average_bitrate = _mean(
            [
                (res.get("output_info") or {}).get("bitrate")
                for res in results
            ]
        )

        return {
            "template_id": template.template_id,
            "template_name": template.name,
            "total_files": len(source_files),
            "successful": len(results),
            "failed": len(failed),
            "results": results,
            "errors": failed,
            "average_speed_fps": average_speed,
            "average_cpu_percent": average_cpu,
            "average_bitrate": average_bitrate,
        }

    async def _transcode_only(
        self, template: EncodingTemplate, source_files: Optional[List[Path]] = None
    ) -> dict:
        """仅转码模式（不进行质量分析）"""
        if source_files is None:
            source_files = self._resolve_source_files(template.metadata.source_path)

        if not source_files:
            raise ValueError(f"未找到源文件: {template.metadata.source_path}")

        logger.info(f"使用模板 {template.name} 转码（无质量分析） {len(source_files)} 个文件")

        output_dir = Path(template.metadata.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        failed = []

        # 临时禁用质量指标计算
        original_enable_metrics = template.metadata.enable_metrics
        template.metadata.enable_metrics = False

        try:
            if template.metadata.parallel_jobs == 1:
                for source_file in source_files:
                    try:
                        result = await self._encode_single_file(template, source_file)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"转码失败 {source_file}: {str(e)}")
                        failed.append({"file": str(source_file), "error": str(e)})
            else:
                tasks = []
                for source_file in source_files:
                    task = self._encode_single_file(template, source_file)
                    tasks.append(task)

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
        finally:
            template.metadata.enable_metrics = original_enable_metrics

        def _mean(values: List[Optional[float]]) -> Optional[float]:
            valid = [v for v in values if isinstance(v, (int, float))]
            if not valid:
                return None
            return sum(valid) / len(valid)

        average_speed = _mean([res.get("average_fps") for res in results])
        average_cpu = _mean([res.get("cpu_percent") for res in results])
        average_bitrate = _mean([(res.get("output_info") or {}).get("bitrate") for res in results])

        return {
            "template_id": template.template_id,
            "template_name": template.name,
            "total_files": len(source_files),
            "successful": len(results),
            "failed": len(failed),
            "results": results,
            "errors": failed,
            "average_speed_fps": average_speed,
            "average_cpu_percent": average_cpu,
            "average_bitrate": average_bitrate,
        }

    async def _analyze_only(
        self, template: EncodingTemplate, source_files: Optional[List[Path]] = None
    ) -> dict:
        """仅质量分析模式（不转码，直接对比参考视频和待测视频）"""
        if source_files is None:
            source_files = self._resolve_source_files(template.metadata.source_path)

        if not source_files:
            raise ValueError(f"未找到待测视频文件: {template.metadata.source_path}")

        if not template.metadata.reference_path:
            raise ValueError("仅分析模式需要指定 reference_path（参考视频路径）")

        reference_files = self._resolve_source_files(template.metadata.reference_path)
        if not reference_files:
            raise ValueError(f"未找到参考视频文件: {template.metadata.reference_path}")

        logger.info(f"使用模板 {template.name} 进行质量分析（无转码） {len(source_files)} 个文件")

        metrics_dir = Path(template.metadata.metrics_report_dir)
        metrics_dir.mkdir(parents=True, exist_ok=True)

        results = []
        failed = []

        # 根据文件数量决定匹配方式
        # 如果参考视频只有一个，则所有待测视频都与它对比
        # 如果数量相同，则一一对应
        if len(reference_files) == 1:
            reference_map = {src: reference_files[0] for src in source_files}
        elif len(reference_files) == len(source_files):
            reference_map = dict(zip(source_files, reference_files))
        else:
            raise ValueError(
                f"参考视频数量({len(reference_files)})与待测视频数量({len(source_files)})不匹配。"
                f"参考视频应为1个或与待测视频数量相同。"
            )

        for source_file in source_files:
            try:
                reference_file = reference_map[source_file]
                metrics = await self._calculate_metrics(template, reference_file, source_file)
                
                result = {
                    "source_file": str(source_file),
                    "output_file": str(source_file),  # 仅分析模式，输出即为源文件
                    "encoder_type": None,
                    "elapsed_seconds": 0.0,
                    "cpu_time_seconds": None,
                    "cpu_percent": None,
                    "average_fps": None,
                    "output_info": None,
                    "metrics": metrics,
                }
                results.append(result)
            except Exception as e:
                logger.error(f"质量分析失败 {source_file}: {str(e)}")
                failed.append({"file": str(source_file), "error": str(e)})

        return {
            "template_id": template.template_id,
            "template_name": template.name,
            "total_files": len(source_files),
            "successful": len(results),
            "failed": len(failed),
            "results": results,
            "errors": failed,
            "average_speed_fps": None,
            "average_cpu_percent": None,
            "average_bitrate": None,
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

        start_time = time.perf_counter()
        cpu_time_seconds = None
        cpu_percent = None
        process_handle = None

        # 执行转码
        process = await asyncio.create_subprocess_exec(
            *encoder_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            process_handle = psutil.Process(process.pid)
        except (psutil.NoSuchProcess, psutil.Error):
            process_handle = None

        stdout, stderr = await process.communicate()

        elapsed = time.perf_counter() - start_time

        if process_handle:
            try:
                cpu_times = process_handle.cpu_times()
                cpu_time_seconds = (cpu_times.user or 0.0) + (cpu_times.system or 0.0)
                cpu_denominator = elapsed * max(1, psutil.cpu_count() or os.cpu_count() or 1)
                if cpu_denominator > 0:
                    cpu_percent = min(100.0, (cpu_time_seconds / cpu_denominator) * 100.0)
            except (psutil.NoSuchProcess, psutil.Error):
                cpu_time_seconds = None
                cpu_percent = None

        if process.returncode != 0:
            raise RuntimeError(f"转码失败: {stderr.decode()}")

        from .ffmpeg import ffmpeg_service

        output_info = None
        average_fps = None
        try:
            output_info = await ffmpeg_service.get_video_info(output_file)
            if output_info:
                duration = output_info.get("duration") or 0.0
                fps = output_info.get("fps") or 0.0
                if duration > 0 and fps > 0 and elapsed > 0:
                    total_frames = fps * duration
                    average_fps = total_frames / elapsed
        except Exception as exc:
            logger.warning(f"读取输出视频信息失败: {exc}")
            output_info = None

        result = {
            "source_file": str(source_file),
            "output_file": str(output_file),
            "encoder_type": template.metadata.encoder_type,
            "elapsed_seconds": elapsed,
            "cpu_time_seconds": cpu_time_seconds,
            "cpu_percent": cpu_percent,
            "average_fps": average_fps,
            "output_info": output_info,
        }

        # 如果启用质量指标计算
        if template.metadata.enable_metrics:
            metrics = await self._calculate_metrics(
                template, source_file, output_file
            )
            result["metrics"] = metrics

        try:
            result["output_size_bytes"] = output_file.stat().st_size
        except OSError:
            result["output_size_bytes"] = None

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
        encoder_path = template.metadata.encoder_path or self.encoder_paths.get(encoder_type)

        if not encoder_path:
            raise ValueError(f"未配置编码器可执行文件，且无法推断 {encoder_type} 的默认路径")

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

    def resolve_source_files(self, template: EncodingTemplate) -> List[Path]:
        """获取模板配置对应的源文件列表"""

        return self._resolve_source_files(template.metadata.source_path)


# 全局单例
template_encoder_service = TemplateEncoderService()
