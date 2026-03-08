"""
每日股票推荐API接口
支持手动触发每日热门股票分析并发送邮件报告
"""
from typing import Optional
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field
from app.stock.task import analyze_and_send_daily_recommendation
from app.utils.config import HOT_STOCK_COUNT, RECOMMEND_COUNT
from app.utils.logging import log

router = APIRouter(prefix="/api/daily-recommendation", tags=["每日股票推荐"])


class DailyRecommendationResponse(BaseModel):
    """每日股票推荐响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")


@router.post("/", response_model=DailyRecommendationResponse)
async def trigger_daily_recommendation(background_tasks: BackgroundTasks):
    """
    手动触发每日股票推荐
    
    分析热门股票并发送邮件报告
    请求成功后立即返回，邮件在后台发送
    
    示例:
    - POST /api/daily-recommendation/
    """
    log.info("API请求: 手动触发每日股票推荐")
    
    # 后台执行推荐任务
    background_tasks.add_task(analyze_and_send_daily_recommendation)
    
    return DailyRecommendationResponse(
        success=True,
        message="已接收每日推荐请求，分析报告将发送至邮箱"
    )


@router.get("/", response_model=DailyRecommendationResponse)
async def get_daily_recommendation_status():
    """
    获取每日推荐服务状态
    
    返回服务配置信息
    """
    return DailyRecommendationResponse(
        success=True,
        message=f"每日股票推荐服务运行中，默认分析前 {HOT_STOCK_COUNT} 只热门股票，推荐前 {RECOMMEND_COUNT} 只"
    )
