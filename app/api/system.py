"""
系统管理API接口
提供健康检查、任务触发等系统级功能
"""
from fastapi import APIRouter
from app.stock.task import stock_recommendation_task
from app.utils.logging import log

router = APIRouter(tags=["系统管理"])


@router.get("/health")
def health_check():
    """
    健康检查接口
    
    返回系统运行状态
    """
    return {"status": "healthy", "message": "股票推荐系统运行正常"}


@router.post("/trigger")
def trigger_recommendation():
    """
    手动触发股票推荐任务接口
    
    立即执行每日股票推荐分析并发送邮件
    """
    log.info("手动触发股票推荐任务...")
    stock_recommendation_task()
    return {"status": "success", "message": "股票推荐任务已触发"}
