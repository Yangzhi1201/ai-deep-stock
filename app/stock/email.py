import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
            f'<span style="display:inline-block;background:#e8f5e9;color:#2e7d32;'  
            f'padding:2px 8px;border-radius:10px;margin:2px 4px 2px 0;font-size:12px;' 
            f'{s}</span>'
            for s in r["买入信号"]
        )
        color = "#c62828" if r["涨跌幅"].startswith("+") else "#2e7d32"

        rows_html += f"""
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:14px 10px;text-align:center;font-size:20px;">{medal}</td>
            <td style="padding:14px 10px;">
                <div style="font-weight:bold;font-size:16px;">{r['名称']}</div>
                <div style="color:#888;font-size:13px;">{r['代码']}</div>
            </td>
            <td style="padding:14px 10px;text-align:center;">
                <div style="font-size:18px;font-weight:bold;">{r['最新价']}</div>
                <div style="color:{color};font-size:13px;">{r['涨跌幅']}</div>
            </td>
            <td style="padding:14px 10px;text-align:center;">
                <div style="font-size:22px;font-weight:bold;color:#1565c0;">{r['综合评分']}</div>
            </td>
            <td style="padding:14px 10px;font-size:12px;">
                RSI: {r['RSI']}<br>DIF: {r['MACD_DIF']}<br>DEA: {r['MACD_DEA']}
            </td>
            <td style="padding:14px 10px;">{signals_html}</td>
        </tr>"""

    return f"""
    <div style="font-family:'Microsoft YaHei','Helvetica Neue',sans-serif;max-width:800px;margin:0 auto;padding:20px;">
        <div style="background:linear-gradient(135deg,#1a237e,#283593);color:white;padding:24px 30px;border-radius:12px 12px 0 0;">
            <h1 style="margin:0;font-size:22px;">📊 A股每日买入推荐</h1>
            <p style="margin:8px 0 0;opacity:0.85;font-size:14px;">{today_str} {weekday} · 技术面分析 · 热门股TOP{HOT_STOCK_COUNT}精选</p>
        </div>

        <table style="width:100%;border-collapse:collapse;background:white;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <thead>
                <tr style="background:#f5f5f5;">
                    <th style="padding:12px 10px;font-size:13px;color:#666;">排名</th>
                    <th style="padding:12px 10px;font-size:13px;color:#666;text-align:left;">股票</th>
                    <th style="padding:12px 10px;font-size:13px;color:#666;">最新价</th>
                    <th style="padding:12px 10px;font-size:13px;color:#666;">评分</th>
                    <th style="padding:12px 10px;font-size:13px;color:#666;">指标</th>
                    <th style="padding:12px 10px;font-size:13px;color:#666;text-align:left;">买入信号</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>

        <div style="background:#fff8e1;border-left:4px solid #ffa000;padding:14px 18px;margin-top:16px;border-radius:0 8px 8px 0;">
            <p style="margin:0;font-size:13px;color:#e65100;">
                ⚠️ <b>风险提示</b>：本推荐基于技术指标量化分析，仅供参考，不构成投资建议。股市有风险，投资需谨慎。
            </p>
        </div>
        <p style="text-align:center;color:#bbb;font-size:12px;margin-top:20px;">
            由 stock_recommender.py 自动生成 · 数据来源：东方财富
        </p>
    </div>"""

def send_email(html_content: str):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.date.today().weekday()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 A股买入推荐 TOP3 | {today_str} {weekday}"
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = ", ".join(EMAIL_CONFIG["receiver"])
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