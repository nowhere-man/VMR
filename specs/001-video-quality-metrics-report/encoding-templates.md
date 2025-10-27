# 转码模板功能规格说明

**功能名称**: 转码模板管理 (Encoding Templates)
**创建日期**: 2025-10-27
**状态**: 已实现

## 功能概述

转码模板功能允许用户创建、管理和使用可重复的视频转码配置。用户可以定义编码器类型、参数、输入输出路径等配置，并保存为模板供后续使用。

## 核心特性

### 1. 模板创建与管理

用户可以创建包含以下配置的转码模板：

- **编码器类型**: 支持 FFmpeg、x264、x265、VVenC
- **编码参数**: 灵活的字符串格式参数配置
- **路径配置**:
  - 源视频路径（支持三种模式）:
    1. 单个文件: `/path/to/video.mp4`
    2. 多个文件（逗号分隔）: `/path/video1.mp4,/path/video2.mp4`
    3. 目录路径: `/path/to/videos/` （转码目录中所有视频文件）
  - 转码后视频输出目录
  - Metrics 报告保存目录
- **质量指标配置**:
  - 是否启用指标计算
  - 指标类型选择（PSNR、SSIM、VMAF）
- **高级选项**:
  - 输出视频格式
  - 并行任务数（1-16）

### 2. 模板持久化

所有模板配置保存在文件系统中，结构如下：

```
jobs/templates/
├── {template_id_1}/
│   └── template.json
├── {template_id_2}/
│   └── template.json
└── ...
```

### 3. 基于模板的转码

用户可以使用已创建的模板执行视频转码任务：
- 自动批处理多个视频文件
- 支持串行或并行执行
- 可选的质量指标自动计算
- 详细的执行结果和错误报告

## 数据模型

### EncoderType（编码器类型）

```python
class EncoderType(str, Enum):
    FFMPEG = "ffmpeg"   # FFmpeg 编码器
    X264 = "x264"       # x264 编码器
    X265 = "x265"       # x265 编码器
    VVENC = "vvenc"     # VVenC (VVC) 编码器
```

### EncodingTemplateMetadata（模板元数据）

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| template_id | str | ✅ | 模板 ID（nanoid 12字符） |
| name | str | ✅ | 模板名称（1-100字符） |
| description | str | ❌ | 模板描述（最多500字符） |
| encoder_type | EncoderType | ✅ | 编码器类型 |
| encoder_params | str | ✅ | 编码参数（1-2000字符） |
| source_path | str | ✅ | 源视频路径或目录 |
| output_dir | str | ✅ | 输出目录 |
| metrics_report_dir | str | ✅ | 报告目录 |
| enable_metrics | bool | ❌ | 是否启用指标计算（默认 true） |
| metrics_types | list[str] | ❌ | 指标类型列表（默认 ["psnr", "ssim", "vmaf"]） |
| output_format | str | ❌ | 输出格式（默认 "mp4"） |
| parallel_jobs | int | ❌ | 并行任务数（1-16，默认 1） |
| created_at | datetime | ✅ | 创建时间 |
| updated_at | datetime | ✅ | 更新时间 |

## API 端点

### 1. 创建模板

**端点**: `POST /api/templates`

**请求体**:
```json
{
  "name": "H264高质量转码",
  "description": "使用H264编码器的高质量转码配置",
  "encoder_type": "ffmpeg",
  "encoder_params": "-c:v libx264 -preset slow -crf 18",
  "source_path": "/videos/input/*.mp4",
  "output_dir": "/videos/output",
  "metrics_report_dir": "/videos/reports",
  "enable_metrics": true,
  "metrics_types": ["psnr", "ssim", "vmaf"],
  "output_format": "mp4",
  "parallel_jobs": 4
}
```

**响应** (201 Created):
```json
{
  "template_id": "abc123def456",
  "name": "H264高质量转码",
  "created_at": "2025-10-27T10:30:00Z"
}
```

### 2. 获取模板详情

**端点**: `GET /api/templates/{template_id}`

**响应** (200 OK):
```json
{
  "template_id": "abc123def456",
  "name": "H264高质量转码",
  "description": "使用H264编码器的高质量转码配置",
  "encoder_type": "ffmpeg",
  "encoder_params": "-c:v libx264 -preset slow -crf 18",
  "source_path": "/videos/input/*.mp4",
  "output_dir": "/videos/output",
  "metrics_report_dir": "/videos/reports",
  "enable_metrics": true,
  "metrics_types": ["psnr", "ssim", "vmaf"],
  "output_format": "mp4",
  "parallel_jobs": 4,
  "created_at": "2025-10-27T10:30:00Z",
  "updated_at": "2025-10-27T10:30:00Z"
}
```

### 3. 列出所有模板

**端点**: `GET /api/templates?encoder_type={type}&limit={n}`

**查询参数**:
- `encoder_type` (可选): 按编码器类型过滤
- `limit` (可选): 结果数量限制

**响应** (200 OK):
```json
[
  {
    "template_id": "abc123def456",
    "name": "H264高质量转码",
    "description": "使用H264编码器的高质量转码配置",
    "encoder_type": "ffmpeg",
    "created_at": "2025-10-27T10:30:00Z"
  }
]
```

### 4. 更新模板

**端点**: `PUT /api/templates/{template_id}`

**请求体** (所有字段可选):
```json
{
  "name": "H264超高质量转码",
  "encoder_params": "-c:v libx264 -preset veryslow -crf 16",
  "parallel_jobs": 8
}
```

**响应** (200 OK): 返回完整的模板信息

### 5. 删除模板

**端点**: `DELETE /api/templates/{template_id}`

**响应** (204 No Content)

### 6. 验证模板路径

**端点**: `GET /api/templates/{template_id}/validate`

**响应** (200 OK):
```json
{
  "template_id": "abc123def456",
  "source_exists": true,
  "output_dir_writable": true,
  "metrics_dir_writable": true,
  "all_valid": true
}
```

### 7. 执行模板转码

**端点**: `POST /api/templates/{template_id}/execute`

**请求体**:
```json
{
  "source_files": [
    "/videos/input/video1.mp4",
    "/videos/input/video2.mp4"
  ]
}
```

**注意**: `source_files` 字段可选，不提供则使用模板中配置的 `source_path`

**响应** (200 OK):
```json
{
  "template_id": "abc123def456",
  "template_name": "H264高质量转码",
  "total_files": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "source_file": "/videos/input/video1.mp4",
      "output_file": "/videos/output/video1_encoded.mp4",
      "encoder_type": "ffmpeg",
      "metrics": {
        "psnr": {
          "psnr_avg": 42.35,
          "psnr_y": 43.12,
          "psnr_u": 41.58,
          "psnr_v": 42.35
        },
        "ssim": {
          "ssim_avg": 0.9823,
          "ssim_y": 0.9845,
          "ssim_u": 0.9801,
          "ssim_v": 0.9823
        },
        "vmaf": {
          "vmaf_mean": 85.67,
          "vmaf_harmonic_mean": 84.23
        }
      }
    },
    {
      "source_file": "/videos/input/video2.mp4",
      "output_file": "/videos/output/video2_encoded.mp4",
      "encoder_type": "ffmpeg",
      "metrics": { ... }
    }
  ],
  "errors": []
}
```

## 编码器参数格式

### FFmpeg

```bash
-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p
```

### x264

```bash
--preset slow --crf 18 --pix-fmt yuv420p
```

### x265

```bash
--preset slow --crf 18 --pix-fmt yuv420p
```

### VVenC

```bash
--preset slow --qp 22
```

## 使用示例

### 示例 1: 批量转码视频目录

1. 创建模板：
```bash
POST /api/templates
{
  "name": "批量H264转码",
  "encoder_type": "ffmpeg",
  "encoder_params": "-c:v libx264 -preset medium -crf 23",
  "source_path": "/videos/raw/",
  "output_dir": "/videos/encoded/",
  "metrics_report_dir": "/videos/reports/",
  "parallel_jobs": 4
}
```

2. 执行转码：
```bash
POST /api/templates/{template_id}/execute
{}
```

### 示例 2: 使用通配符处理特定文件

创建模板时使用通配符：
```json
{
  "source_path": "/videos/raw/test_*.mp4"
}
```

### 示例 3: 不启用质量指标

如果只需要转码，不需要计算指标：
```json
{
  "enable_metrics": false
}
```

## 错误处理

### 常见错误

1. **404 Not Found**: 模板不存在
2. **400 Bad Request**: 请求参数验证失败
3. **500 Internal Server Error**: 转码执行失败

### 错误响应格式

```json
{
  "detail": "Template abc123def456 not found"
}
```

## 限制与约束

1. **模板名称**: 1-100 字符
2. **模板描述**: 最多 500 字符
3. **编码参数**: 最多 2000 字符
4. **并行任务数**: 1-16
5. **支持的指标类型**: psnr, ssim, vmaf
6. **模板 ID**: 12 字符 nanoid

## 实现文件

- **数据模型**: `src/models_template.py`
- **存储服务**: `src/services/template_storage.py`
- **编码服务**: `src/services/template_encoder.py`
- **API 端点**: `src/api/templates.py`
- **Schema 定义**: `src/schemas_template.py`

## 未来增强

- [ ] 支持模板导入/导出（JSON 文件）
- [ ] 模板版本控制
- [ ] 预定义模板库
- [ ] 模板执行历史记录
- [ ] WebSocket 实时进度推送
- [ ] 支持更多编码器（AV1、VP9 等）
- [ ] 条件编码（根据源视频属性自动调整参数）

---

**最后更新**: 2025-10-27
**作者**: VQMR Team
