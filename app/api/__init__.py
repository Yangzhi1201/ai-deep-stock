"""
API路由包
包含所有API接口模块
"""

from app.api.system import router as system_router
from app.api.recommendation import router as recommendation_router

__all__ = [
    "system_router",
    "recommendation_router",
]
