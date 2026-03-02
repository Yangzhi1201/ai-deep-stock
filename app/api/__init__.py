"""
API路由包
包含所有API接口模块
"""

from app.api.stock_compare import router as stock_compare_router
from app.api.daily_recommendation import router as daily_recommendation_router
from app.api.system import router as system_router

__all__ = [
    "stock_compare_router",
    "daily_recommendation_router", 
    "system_router",
]
