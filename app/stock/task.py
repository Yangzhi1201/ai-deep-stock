import datetime
from app.stock.analyzer import run_analysis
from app.stock.email import build_email_html, send_email
from app.utils.logging import log

def stock_recommendation_task():
    """股票推荐定时任务"""
    log.info("=" * 50)
    log.info("开始执行 A股每日推荐分析...")
    log.info("=" * 50)

    # 检查是否是交易日（周一至周五）
    today = datetime.date.today()
    if today.weekday() >= 5:
        log.info("今天是周末，非交易日，跳过分析。")
        return

    try:
        recommendations = run_analysis()
        html = build_email_html(recommendations)
        send_email(html)
        log.info("任务完成！")
    except Exception as e:
        log.error(f"任务执行异常: {e}", exc_info=True)