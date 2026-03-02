"""
股票推荐任务模块
提供定时任务和手动触发功能
"""
import datetime
from typing import List, Dict
from app.stock.analyzer import run_hot_stocks_analysis
from app.stock.email import build_email_html, send_email
from app.utils.logging import log


def stock_recommendation_task():
    """
    股票推荐定时任务
    每日自动分析热门股票并发送邮件
    """
    log.info("=" * 50)
    log.info("开始执行 A股每日推荐分析...")
    log.info("=" * 50)

    # 检查是否是交易日（周一至周五）
    today = datetime.date.today()
    if today.weekday() >= 5:
        log.info("今天是周末，非交易日，跳过分析。")
        return

    try:
        # 运行热门股票分析
        recommendations = run_hot_stocks_analysis()
        
        if recommendations:
            # 发送邮件
            html = build_email_html(recommendations)
            send_email(html)
            log.info("任务完成！")
        else:
            log.warning("没有获取到推荐股票，跳过邮件发送。")
            
    except Exception as e:
        log.error(f"任务执行异常: {e}", exc_info=True)


def analyze_and_send_email(stocks: List[Dict]) -> Dict:
    """
    分析指定股票并发送邮件
    
    Args:
        stocks: 股票列表，每个元素包含 code, market, name
    
    Returns:
        包含分析结果和发送状态的字典
    """
    from app.stock.analyzer import analyze_stocks_batch
    
    log.info(f"开始分析指定股票列表，共 {len(stocks)} 只...")
    
    try:
        # 批量分析
        results, summary = analyze_stocks_batch(stocks)
        
        if results:
            # 发送邮件
            html = build_email_html(results)
            send_email(html)
            
            return {
                "success": True,
                "message": f"成功分析 {summary['success']}/{summary['total']} 只股票，邮件已发送",
                "summary": summary,
                "results": results
            }
        else:
            return {
                "success": False,
                "message": "没有成功分析任何股票",
                "summary": summary,
                "results": []
            }
            
    except Exception as e:
        log.error(f"分析并发送邮件失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"执行失败: {str(e)}",
            "summary": {},
            "results": []
        }
