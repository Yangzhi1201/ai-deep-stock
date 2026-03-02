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
        change_class = "positive" if r["涨跌幅"].startswith("+") else "negative"

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
                    <div class="stock-change {change_class}">{r['涨跌幅']}</div>
                </div>
                <div class="stock-score">
                    <div class="stock-score-value">{r['综合评分']}</div>
                    <div class="stock-score-label">评分</div>
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
            /* 全局样式 */
            :root {{
                --primary: #165DFF;
                --primary-dark: #0E42B9;
                --success: #00B42A;
                --warning: #FF7D00;
                --danger: #F53F3F;
                --text: #1D2129;
                --text-secondary: #86909C;
                --background: #F5F7FA;
                --card-bg: #FFFFFF;
                --border: #E5E6EB;
                --shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                --shadow-hover: 0 8px 24px rgba(0, 0, 0, 0.12);
                --border-radius: 12px;
                --transition: all 0.3s ease;
            }}
            
            body {{
                margin: 0;
                padding: 0;
                font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
                background-color: var(--background);
                color: var(--text);
                line-height: 1.6;
            }}
            
            .container {{
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            /* 头部样式 */
            .header {{
                background: linear-gradient(135deg, var(--primary), var(--primary-dark));
                color: white;
                padding: 32px 36px;
                border-radius: var(--border-radius) var(--border-radius) 0 0;
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                right: 0;
                width: 200px;
                height: 200px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
                transform: translate(50%, -50%);
            }}
            
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
                position: relative;
                z-index: 1;
            }}
            
            .header p {{
                margin: 12px 0 0;
                opacity: 0.9;
                font-size: 14px;
                position: relative;
                z-index: 1;
            }}
            
            /* 股票卡片样式 */
            .stock-card {{
                background: var(--card-bg);
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                margin-bottom: 16px;
                overflow: hidden;
                transition: var(--transition);
                border: 1px solid var(--border);
            }}
            
            .stock-card:hover {{
                box-shadow: var(--shadow-hover);
                transform: translateY(-2px);
            }}
            
            .stock-header {{
                display: flex;
                align-items: center;
                padding: 16px 20px;
                border-bottom: 1px solid var(--border);
                background: #F9FAFB;
            }}
            
            .stock-rank {{
                font-size: 24px;
                font-weight: bold;
                margin-right: 20px;
                width: 40px;
                text-align: center;
                color: var(--primary);
            }}
            
            .stock-info {{
                flex: 1;
            }}
            
            .stock-name {{
                font-weight: 600;
                font-size: 18px;
                color: var(--text);
                margin-bottom: 4px;
            }}
            
            .stock-code {{
                color: var(--text-secondary);
                font-size: 14px;
            }}
            
            .stock-price {{
                text-align: center;
                margin: 0 20px;
                min-width: 100px;
            }}
            
            .stock-price-value {{
                font-size: 20px;
                font-weight: 600;
                color: var(--text);
                margin-bottom: 4px;
            }}
            
            .stock-change {{
                font-size: 14px;
                font-weight: 500;
            }}
            
            .stock-change.positive {{
                color: var(--success);
            }}
            
            .stock-change.negative {{
                color: var(--danger);
            }}
            
            .stock-score {{
                text-align: center;
                margin: 0 20px;
                min-width: 80px;
            }}
            
            .stock-score-value {{
                font-size: 24px;
                font-weight: bold;
                color: var(--primary);
                margin-bottom: 4px;
            }}
            
            .stock-score-label {{
                font-size: 12px;
                color: var(--text-secondary);
            }}
            
            .stock-details {{
                padding: 16px 20px;
            }}
            
            .stock-indicators {{
                font-size: 13px;
                color: var(--text-secondary);
                margin-bottom: 16px;
                line-height: 1.5;
            }}
            
            .stock-signals {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }}
            
            .signal-tag {{
                display: inline-block;
                background: #E8F3FF;
                color: var(--primary);
                padding: 4px 12px;
                border-radius: 16px;
                font-size: 12px;
                font-weight: 500;
                transition: var(--transition);
            }}
            
            .signal-tag:hover {{
                background: var(--primary);
                color: white;
            }}
            
            /* 警告样式 */
            .warning {{
                background: #FFF8E6;
                border-left: 4px solid var(--warning);
                padding: 16px 20px;
                margin-top: 24px;
                border-radius: 0 var(--border-radius) var(--border-radius) 0;
                box-shadow: var(--shadow);
            }}
            
            .warning p {{
                margin: 0;
                font-size: 14px;
                color: #B35E00;
                line-height: 1.5;
            }}
            
            /* 页脚样式 */
            .footer {{
                text-align: center;
                color: var(--text-secondary);
                font-size: 12px;
                margin-top: 24px;
                padding: 16px 0;
                border-top: 1px solid var(--border);
            }}
            
            /* 响应式设计 */
            @media screen and (max-width: 600px) {{
                .container {{
                    padding: 12px;
                }}
                
                .header {{
                    padding: 24px 20px;
                }}
                
                .header h1 {{
                    font-size: 22px;
                }}
                
                .stock-header {{
                    flex-wrap: wrap;
                    gap: 12px;
                    padding: 12px 16px;
                }}
                
                .stock-rank {{
                    font-size: 20px;
                    margin-right: 12px;
                }}
                
                .stock-name {{
                    font-size: 16px;
                }}
                
                .stock-price, .stock-score {{
                    margin: 8px 0;
                    min-width: auto;
                }}
                
                .stock-price-value, .stock-score-value {{
                    font-size: 18px;
                }}
                
                .stock-details {{
                    padding: 12px 16px;
                }}
                
                .stock-indicators {{
                    font-size: 12px;
                }}
                
                .signal-tag {{
                    font-size: 11px;
                    padding: 3px 10px;
                }}
            }}
            
            /* 动画效果 */
            @keyframes fadeIn {{
                from {{
                    opacity: 0;
                    transform: translateY(10px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .stock-card {{
                animation: fadeIn 0.5s ease forwards;
            }}
            
            .stock-card:nth-child(1) {{ animation-delay: 0.1s; }}
            .stock-card:nth-child(2) {{ animation-delay: 0.2s; }}
            .stock-card:nth-child(3) {{ animation-delay: 0.3s; }}
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