"""
API module

提供 RESTful API 端点
"""
from .jobs import router as jobs_router
from .pages import router as pages_router

__all__ = ["jobs_router", "pages_router"]
