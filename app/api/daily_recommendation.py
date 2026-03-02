"""
每日股票推荐API接口
支持手动触发每日热门股票分析并发送邮件报告
"""
from typing import Optional
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field
from app.stock.task import stock_recommendation_task
from app.stock.analyzer import run_hot_stocks_analysis
from app.stock.email import build_email_html, send_email
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
    background_tasks.add_task(_run_daily_recommendation_task)
    
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


def _run_daily_recommendation_task():
    """
    后台任务：执行每日股票推荐
    """
    try:
        log.info("开始执行每日股票推荐任务...")
        
        # 运行热门股票分析
        recommendations = run_hot_stocks_analysis()
        
        if recommendations:
            # 发送邮件
            html = build_email_html(recommendations)
            send_email(html)
            log.info(f"每日推荐完成并发送邮件，共 {len(recommendations)} 只股票")
        else:
            log.warning("没有获取到推荐股票，跳过邮件发送")
            
    except Exception as e:
        log.error(f"每日推荐任务失败: {e}", exc_info=True)
