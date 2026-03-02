import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import List, Dict
from app.utils.config import EMAIL_CONFIG, HOT_STOCK_COUNT
from app.utils.logging import log

def build_email_html(recommendations: List[Dict]) -> str:
    today_str = datetime.date.today().strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.date.today().weekday()]

    if not recommendations:
        return f"""
        <div style="font-family:'Microsoft YaHei',sans-serif;padding:20px;">
            <h2>📊 {today_str} ({weekday}) A股买入推荐</h2>
            <p style="color:#999;">今日未筛选到符合条件的股票，请关注后续推送。</p>
        </div>"""

    rows_html = ""
    for i, r in enumerate(recommendations, 1):
        medal = ["🥇", "🥈", "🥉"][i - 1]
        signals_html = "".join(
            f'<span class="signal-tag">{s}</span>'
            for s in r["买入信号"]
        )
        color = "#c62828" if r["涨跌幅"].startswith("+") else "#2e7d32"

        rows_html += f"""
        <div class="stock-card">
            <div class="stock-header">
                <div class="stock-rank">{medal}</div>
                <div class="stock-info">
                    <div class="stock-name">{r['名称']}</div>
                    <div class="stock-code">{r['代码']}</div>
                </div>
                <div class="stock-price">
                    <div class="stock-price-value">{r['最新价']}</div>
                    <div class="stock-change" style="color:{color};">{r['涨跌幅']}</div>
                </div>
                <div class="stock-score">
                    <div class="stock-score-value">{r['综合评分']}</div>
                </div>
            </div>
            <div class="stock-details">
                <div class="stock-indicators">
                    RSI: {r['RSI']}<br>
                    DIF: {r['MACD_DIF']}<br>
                    DEA: {r['MACD_DEA']}
                </div>
                <div class="stock-signals">
                    {signals_html}
                </div>
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin:0; padding:0; font-family:'Microsoft YaHei','Helvetica Neue',sans-serif; }}
            .container {{ max-width:800px; margin:0 auto; padding:20px; }}
            .header {{ background:linear-gradient(135deg,#1a237e,#283593); color:white; padding:24px 30px; border-radius:12px 12px 0 0; }}
            .header h1 {{ margin:0; font-size:22px; }}
            .header p {{ margin:8px 0 0; opacity:0.85; font-size:14px; }}
            .stock-card {{ background:white; box-shadow:0 2px 8px rgba(0,0,0,0.08); margin-bottom:12px; border-radius:8px; overflow:hidden; }}
            .stock-header {{ display:flex; align-items:center; padding:12px 16px; border-bottom:1px solid #f0f0f0; }}
            .stock-rank {{ font-size:20px; font-weight:bold; margin-right:16px; width:30px; text-align:center; }}
            .stock-info {{ flex:1; }}
            .stock-name {{ font-weight:bold; font-size:16px; }}
            .stock-code {{ color:#888; font-size:13px; }}
            .stock-price {{ text-align:center; margin:0 16px; }}
            .stock-price-value {{ font-size:18px; font-weight:bold; }}
            .stock-change {{ font-size:13px; }}
            .stock-score {{ text-align:center; margin:0 16px; }}
            .stock-score-value {{ font-size:22px; font-weight:bold; color:#1565c0; }}
            .stock-details {{ padding:12px 16px; }}
            .stock-indicators {{ font-size:12px; margin-bottom:12px; }}
            .stock-signals {{ }}
            .signal-tag {{ display:inline-block; background:#e8f5e9; color:#2e7d32; padding:2px 8px; border-radius:10px; margin:2px 4px 2px 0; font-size:12px; }}
            .warning {{ background:#fff8e1; border-left:4px solid #ffa000; padding:14px 18px; margin-top:16px; border-radius:0 8px 8px 0; }}
            .warning p {{ margin:0; font-size:13px; color:#e65100; }}
            .footer {{ text-align:center; color:#bbb; font-size:12px; margin-top:20px; }}
            @media screen and (max-width: 600px) {{
                .container {{ padding:10px; }}
                .header h1 {{ font-size:18px; }}
                .stock-header {{ flex-wrap:wrap; }}
                .stock-rank {{ font-size:18px; margin-right:12px; }}
                .stock-name {{ font-size:14px; }}
                .stock-price, .stock-score {{ margin:8px 0; width:100%; text-align:left; }}
                .stock-price-value, .stock-score-value {{ font-size:16px; }}
                .stock-indicators {{ font-size:11px; }}
                .signal-tag {{ font-size:11px; padding:2px 6px; }}
            }}
        </style>
    </head>
    <body>
    <div class="container">
        <div class="header">
            <h1>📊 A股每日买入推荐</h1>
            <p>{today_str} {weekday} · 技术面分析 · 热门股TOP{HOT_STOCK_COUNT}精选</p>
        </div>

        {rows_html}

        <div class="warning">
            <p>⚠️ <b>风险提示</b>：本推荐基于技术指标量化分析，仅供参考，不构成投资建议。股市有风险，投资需谨慎。</p>
        </div>
        <div class="footer">
            由 stock_recommender.py 自动生成 · 数据来源：东方财富
        </div>
    </div>
    </body>
    </html>"""


def send_email(html_content: str):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.date.today().weekday()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(f"📊 A股买入推荐 TOP3 | {today_str} {weekday}", "utf-8")
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = ", ".join(EMAIL_CONFIG["receiver"])
    
    # 添加纯文本版本作为备选
    plain_text = "A股买入推荐报告\n" + today_str + " " + weekday + "\n\n请在支持HTML的邮件客户端查看完整报告。"
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    
    # 添加HTML版本
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    log.info(f"正在发送邮件至 {EMAIL_CONFIG['receiver']} ...")
    try:
        with smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
            server.sendmail(EMAIL_CONFIG["sender"], EMAIL_CONFIG["receiver"], msg.as_string())
        log.info("邮件发送成功！")
    except Exception as e:
        log.error(f"邮件发送失败: {e}")
        raise