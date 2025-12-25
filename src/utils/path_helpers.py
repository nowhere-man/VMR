"""
路径验证工具模块

提供目录存在性检查和可写性验证功能。
"""

from pathlib import Path


def dir_exists(path: str) -> bool:
    """
    检查目录是否存在

    Args:
        path: 目录路径字符串

    Returns:
        目录存在返回 True，否则返回 False
    """
    return Path(path).is_dir()


def dir_writable(path: str) -> bool:
    """
    检查目录是否可写（如不存在会尝试创建）

    Args:
        path: 目录路径字符串

    Returns:
        目录可写返回 True，否则返回 False
    """
    p = Path(path)
    try:
        p.mkdir(parents=True, exist_ok=True)
        test = p / ".writetest"
        test.write_text("ok")
        test.unlink()
        return True
    except Exception:
        return False
