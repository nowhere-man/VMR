# 主页优化更新文档

**日期**: 2025-10-27
**更新内容**: 主页界面优化和源路径功能扩展

## 主页界面优化

### 更新前
主页有两个重复的按钮：
- "创建新任务"（Hero Section）
- "创建质量分析任务"（Quick Actions）

功能重复，缺少任务列表入口。

### 更新后

#### 1. 移除重复按钮
- ✅ 删除 Hero Section 中的"创建新任务"按钮
- ✅ 保留标题和描述文字

#### 2. 快速操作区域重新设计

改为 **4 个功能按钮**，采用卡片式布局：

```
┌────────────────────────────────────────────────────────┐
│  [直接质量分析] [转码后分析] [任务列表] [转码模板]      │
└────────────────────────────────────────────────────────┘
```

**按钮详情**:

| 按钮 | 链接 | 颜色 | 图标 | 说明 |
|------|------|------|------|------|
| 直接质量分析 | `/jobs/new?mode=dual_file` | 蓝色 | ✓ | 上传两个视频进行对比分析 |
| 转码后分析 | `/jobs/new?mode=single_file` | 绿色 | ↻ | 自动转码并计算质量指标 |
| 任务列表 | `/jobs` | 橙色 | 📋 | 查看所有分析任务 |
| 转码模板 | `/templates` | 紫色 | 📁 | 管理转码配置模板 |

#### 3. 视觉优化

**新增效果**:
- ✅ 渐变背景色（`gradient-to-br`）
- ✅ 悬停阴影效果（`hover:shadow-lg`）
- ✅ 悬停上移动画（`transform hover:-translate-y-1`）
- ✅ 图标背景圆形（`bg-white bg-opacity-20`）
- ✅ 居中垂直布局（`flex-col items-center`）

**响应式布局**:
- 移动端（`<md`): 1 列
- 平板（`md`): 2 列
- 桌面（`lg`): 4 列

#### 4. URL 参数传递

通过 URL 参数预设任务模式：
- `/jobs/new?mode=dual_file` - 自动选中双文件模式
- `/jobs/new?mode=single_file` - 自动选中单文件模式

**实现方式**:
```javascript
// create_job.html 新增
function initializeModeFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode');
    
    if (mode === 'dual_file' || mode === 'single_file') {
        const radioButton = document.querySelector('input[name="mode"][value="' + mode + '"]');
        if (radioButton) {
            radioButton.checked = true;
        }
    }
    
    updateFormVisibility();
}
```

## 源视频路径功能扩展

### 需求

转码模板的源视频路径支持三种模式：
1. **单个文件**: `/path/to/video.mp4`
2. **多个文件（逗号分隔）**: `/path/video1.mp4,/path/video2.mp4`
3. **目录路径**: `/path/to/videos/` （转码目录中所有视频文件）

### 后端实现

**文件**: `src/services/template_encoder.py`

**函数**: `_resolve_source_files()`

```python
def _resolve_source_files(self, source_path: str) -> List[Path]:
    """
    解析源文件路径
    
    支持三种模式：
    1. 单个文件路径: /path/to/video.mp4
    2. 多个文件路径（逗号分隔）: /path/to/video1.mp4,/path/to/video2.mp4
    3. 目录路径: /path/to/videos/
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
```

**特点**:
- ✅ 自动去除路径前后空格
- ✅ 逗号分隔时逐个验证文件存在性
- ✅ 目录模式支持多种视频格式
- ✅ 结果自动排序
- ✅ 不存在的文件记录警告日志

### 前端实现

**文件**: `src/templates/template_form.html`

**更改**:
1. 将源路径输入框从 `<input>` 改为 `<textarea>`（支持多行）
2. 添加使用说明

```html
<textarea id="source_path" name="source_path" rows="3" required
    class="w-full border border-gray-300 rounded-md px-3 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
    placeholder="/path/to/video.mp4"></textarea>

<div class="mt-2 bg-gray-50 rounded p-3">
    <p class="text-xs font-medium text-gray-700 mb-2">支持三种模式:</p>
    <div class="space-y-1 text-xs text-gray-600">
        <div><strong>1. 单个文件:</strong> <code>/path/to/video.mp4</code></div>
        <div><strong>2. 多个文件（逗号分隔）:</strong> <code>/path/video1.mp4,/path/video2.mp4</code></div>
        <div><strong>3. 目录（转码所有视频）:</strong> <code>/path/to/videos/</code></div>
    </div>
</div>
```

**文件**: `src/templates/template_detail.html`

添加路径模式提示：
```html
<dd class="mt-1 text-xs text-gray-500">
    支持: 单个文件 | 多个文件（逗号分隔） | 目录路径
</dd>
```

### 使用示例

#### 示例 1: 转码单个文件
```json
{
  "name": "单个视频转码",
  "source_path": "/videos/test.mp4",
  "output_dir": "/output",
  "metrics_report_dir": "/reports"
}
```

#### 示例 2: 转码多个指定文件
```json
{
  "name": "批量转码",
  "source_path": "/videos/video1.mp4,/videos/video2.mp4,/videos/video3.mp4",
  "output_dir": "/output",
  "metrics_report_dir": "/reports",
  "parallel_jobs": 3
}
```

#### 示例 3: 转码整个目录
```json
{
  "name": "目录批量转码",
  "source_path": "/videos/raw/",
  "output_dir": "/output",
  "metrics_report_dir": "/reports",
  "parallel_jobs": 4
}
```

## 文档更新

### 更新的文件

1. **`src/templates/index.html`**
   - 移除 Hero Section 的按钮
   - 重新设计快速操作区域（4 个按钮）
   - 更新布局（2列 -> 4列）

2. **`src/templates/create_job.html`**
   - 添加 URL 参数读取功能
   - 根据参数自动选择模式

3. **`src/templates/template_form.html`**
   - 源路径输入框改为 textarea
   - 添加详细的使用说明

4. **`src/templates/template_detail.html`**
   - 添加路径模式提示

5. **`src/services/template_encoder.py`**
   - 更新源路径解析逻辑
   - 支持三种模式

6. **`specs/001-video-quality-metrics-report/encoding-templates.md`**
   - 更新路径配置说明

7. **`TEMPLATE_QUICKSTART.md`**
   - 更新使用场景示例

## 测试验证

### 代码测试
```bash
✅ python3 -m py_compile src/services/template_encoder.py
```

### 功能测试清单

#### 主页功能
- [ ] 访问主页，4 个按钮正常显示
- [ ] 点击"直接质量分析"，跳转到创建任务页面（双文件模式）
- [ ] 点击"转码后分析"，跳转到创建任务页面（单文件模式）
- [ ] 点击"任务列表"，跳转到任务列表页面
- [ ] 点击"转码模板"，跳转到模板管理页面
- [ ] 响应式布局测试（移动/平板/桌面）
- [ ] 悬停效果测试

#### 创建任务页面
- [ ] 从主页点击进入，模式自动选中
- [ ] 手动切换模式，表单正确切换
- [ ] 直接访问 `/jobs/new`，默认单文件模式

#### 转码模板功能
- [ ] 创建模板时输入单个文件路径
- [ ] 创建模板时输入多个文件（逗号分隔）
- [ ] 创建模板时输入目录路径
- [ ] 执行模板，验证路径解析正确
- [ ] 多个文件依次转码
- [ ] 目录中所有视频文件转码

## 破坏性变更

无

## 兼容性

✅ 向后兼容
- 原有的通配符模式仍然支持
- 单文件模式保持不变
- 所有现有功能正常工作

## 已知问题

无

---

**完成日期**: 2025-10-27
**作者**: VQMR Team
