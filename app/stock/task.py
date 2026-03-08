"""
股票推荐任务模块
提供定时任务和手动触发功能
"""
import datetime
from typing import List, Dict
from app.agent.workflow import run_hot_stock_workflow, run_sector_stock_workflow
from app.utils.logging import log


def stock_recommendation_task():
    """
    股票推荐定时任务
    每日自动分析热门股票并发送邮件
    """
    log.info("=" * 50)
    log.info("开始执行 A股每日推荐分析 (Agent Workflow)...")
    log.info("=" * 50)

    # 检查是否是交易日（周一至周五）
    today = datetime.date.today()
    if today.weekday() >= 5:
        log.info("今天是周末，非交易日，跳过分析。")
        return

    try:
        # 1. 运行热门股票分析
        log.info("Step 1: 执行热门股票推荐...")
        result_hot = run_hot_stock_workflow()
        if result_hot.get("email_sent"):
            log.info("热门股票推荐邮件发送成功。")
        else:
            log.warning("热门股票推荐邮件发送失败或无推荐。")
            
        # 2. 运行热门板块分析 (可选)
        # 这里可以预定义一些热门板块，或者通过数据接口动态获取热门板块
        # 示例：每天关注一下"AI"和"新能源"
        target_sectors = ["人工智能", "新能源"]
        for sector in target_sectors:
            log.info(f"Step 2: 执行板块[{sector}]推荐...")
            result_sector = run_sector_stock_workflow(sector)
            if result_sector.get("email_sent"):
                log.info(f"板块[{sector}]推荐邮件发送成功。")
            else:
                log.warning(f"板块[{sector}]推荐邮件发送失败或无推荐。")
                
        log.info("所有定时任务执行完毕！")
            
    except Exception as e:
        log.error(f"任务执行异常: {e}", exc_info=True)
