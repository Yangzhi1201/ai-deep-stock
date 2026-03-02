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
        change_class = "up" if r["涨跌幅"].startswith("+") else "down"

        rows_html += f"""
        <div class="stock-item">
            <div class="stock-item-header">
                <div class="stock-rank">{medal}</div>
                <div class="stock-info">
                    <div class="stock-name">{r['名称']}</div>
                    <div class="stock-code">{r['代码']}</div>
                </div>
                <div class="stock-price">
                    <div class="stock-price-value">{r['最新价']}</div>
                    <div class="stock-change {change_class}">{r['涨跌幅']}</div>
                </div>
            </div>
            <div class="stock-item-body">
                <div class="metric-item">
                    <div class="metric-label">RSI</div>
                    <div class="metric-value">{r['RSI']}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">DIF</div>
                    <div class="metric-value">{r['MACD_DIF']}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">DEA</div>
                    <div class="metric-value">{r['MACD_DEA']}</div>
                </div>
                <div class="stock-score">
                    <div class="stock-score-label">综合评分</div>
                    <div class="stock-score-value">{r['综合评分']}</div>
                </div>
            </div>
            <div class="stock-signals">
                {signals_html}
            </div>
        </div>
        """

    # 使用原始字符串来避免花括号转义问题
    html_template = r"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <title>A股买入推荐</title>
        <style>
            /* Design System Variables */
            :root {{
                --primary: #0F172A;
                --primary-light: #334155;
                --success: #10B981;
                --danger: #EF4444;
                --warning: #F59E0B;
                --text-primary: #1E293B;
                --text-secondary: #64748B;
                --text-muted: #94A3B8;
                --background: #F8FAFC;
                --surface: #FFFFFF;
                --border: #E2E8F0;
                --border-light: #F1F5F9;
                --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
                --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                --radius-sm: 6px;
                --radius-md: 8px;
                --radius-lg: 12px;
                --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            
            /* Reset & Base Styles */
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            html {{
                -webkit-text-size-adjust: 100%;
                -webkit-tap-highlight-color: transparent;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                background-color: var(--background);
                color: var(--text-primary);
                line-height: 1.6;
                font-size: 16px;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }}
            
            /* Container */
            .container {{
                max-width: 680px;
                margin: 0 auto;
                background: var(--surface);
                min-height: 100vh;
            }}
            
            /* Header */
            .header {{
                background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
                color: white;
                padding: 24px 16px;
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: -50%;
                right: -20%;
                width: 300px;
                height: 300px;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                border-radius: 50%;
            }}
            
            .header-content {{
                position: relative;
                z-index: 1;
            }}
            
            .header-title {{
                font-size: 20px;
                font-weight: 700;
                margin-bottom: 8px;
                letter-spacing: -0.025em;
            }}
            
            .header-subtitle {{
                font-size: 14px;
                opacity: 0.9;
                font-weight: 400;
            }}
            
            .header-badge {{
                display: inline-block;
                background: rgba(255, 255, 255, 0.15);
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
                margin-top: 12px;
                backdrop-filter: blur(10px);
            }}
            
            /* Content */
            .content {{
                padding: 16px;
            }}
            
            /* Stock List */
            .stock-list {{
                margin-bottom: 24px;
            }}
            
            /* Stock Item */
            .stock-item {{
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                margin-bottom: 12px;
                padding: 16px;
                transition: var(--transition);
            }}
            
            .stock-item:hover {{
                border-color: var(--primary);
                box-shadow: var(--shadow-sm);
            }}
            
            .stock-item-header {{
                display: flex;
                align-items: center;
                margin-bottom: 12px;
            }}
            
            .stock-rank {{
                display: flex;
                align-items: center;
                justify-content: center;
                width: 32px;
                height: 32px;
                background: var(--primary);
                color: white;
                border-radius: var(--radius-sm);
                font-size: 16px;
                font-weight: 700;
                margin-right: 12px;
                flex-shrink: 0;
            }}
            
            .stock-info {{
                flex: 1;
                min-width: 0;
            }}
            
            .stock-name {{
                font-size: 16px;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 2px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            
            .stock-code {{
                font-size: 13px;
                color: var(--text-muted);
                font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
            }}
            
            .stock-price {{
                text-align: right;
                margin-left: 12px;
                flex-shrink: 0;
            }}
            
            .stock-price-value {{
                font-size: 16px;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 2px;
            }}
            
            .stock-change {{
                font-size: 13px;
                font-weight: 500;
            }}
            
            .stock-change.up {{
                color: var(--success);
            }}
            
            .stock-change.down {{
                color: var(--danger);
            }}
            
            .stock-item-body {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
                margin-bottom: 12px;
            }}
            
            .metric-item {{
                background: var(--border-light);
                padding: 8px;
                border-radius: var(--radius-sm);
                text-align: center;
            }}
            
            .metric-label {{
                font-size: 11px;
                color: var(--text-muted);
                margin-bottom: 2px;
            }}
            
            .metric-value {{
                font-size: 14px;
                font-weight: 600;
                color: var(--text-primary);
            }}
            
            .stock-score {{
                grid-column: 1 / -1;
                background: rgba(15, 23, 42, 0.05);
                padding: 10px;
                border-radius: var(--radius-sm);
                text-align: center;
                margin-bottom: 12px;
            }}
            
            .stock-score-label {{
                font-size: 11px;
                color: var(--text-muted);
                margin-bottom: 4px;
            }}
            
            .stock-score-value {{
                font-size: 20px;
                font-weight: 700;
                color: var(--primary);
            }}
            
            .stock-signals {{
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            }}
            
            .signal-tag {{
                display: inline-flex;
                align-items: center;
                background: rgba(15, 23, 42, 0.05);
                color: var(--primary);
                padding: 4px 10px;
                border-radius: 16px;
                font-size: 11px;
                font-weight: 500;
                transition: var(--transition);
            }}
            
            .signal-tag:hover {{
                background: var(--primary);
                color: white;
            }}
            
            /* Warning Box */
            .warning-box {{
                background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
                border-left: 4px solid var(--warning);
                padding: 14px;
                border-radius: var(--radius-md);
                margin-top: 20px;
            }}
            
            .warning-content {{
                display: flex;
                align-items: flex-start;
                gap: 10px;
            }}
            
            .warning-icon {{
                font-size: 18px;
                flex-shrink: 0;
            }}
            
            .warning-text {{
                flex: 1;
            }}
            
            .warning-title {{
                font-weight: 600;
                color: #92400E;
                margin-bottom: 2px;
                font-size: 14px;
            }}
            
            .warning-message {{
                font-size: 13px;
                color: #B45309;
                line-height: 1.5;
            }}
            
            /* Footer */
            .footer {{
                text-align: center;
                padding: 20px 16px;
                border-top: 1px solid var(--border);
                color: var(--text-muted);
                font-size: 12px;
            }}
            
            .footer-links {{
                display: flex;
                justify-content: center;
                gap: 12px;
                margin-bottom: 8px;
                flex-wrap: wrap;
            }}
            
            .footer-link {{
                color: var(--text-secondary);
                text-decoration: none;
                transition: var(--transition);
                font-size: 11px;
            }}
            
            .footer-link:hover {{
                color: var(--primary);
            }}
            
            /* Responsive Design */
            @media screen and (max-width: 600px) {{
                .container {{
                    max-width: 100%;
                }}
                
                .header {{
                    padding: 20px 16px;
                }}
                
                .header-title {{
                    font-size: 18px;
                }}
                
                .content {{
                    padding: 12px;
                }}
                
                .stock-item {{
                    padding: 12px;
                }}
                
                .stock-item-body {{
                    grid-template-columns: 1fr;
                }}
                
                .stock-item-header {{
                    flex-wrap: wrap;
                    gap: 8px;
                }}
                
                .stock-price {{
                    margin-left: 0;
                    margin-top: 4px;
                }}
                
                .signal-tag {{
                    font-size: 10px;
                    padding: 3px 8px;
                }}
            }}
            
            /* Accessibility */
            @media (prefers-reduced-motion: reduce) {{
                * {{
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                }}
            }}
            
            /* Focus Styles */
            a:focus-visible,
            button:focus-visible {{
                outline: 2px solid var(--primary);
                outline-offset: 2px;
            }}
        </style>
    </head>
    <body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1 class="header-title">📊 A股每日买入推荐</h1>
                <p class="header-subtitle">{today_str} {weekday} · 技术面分析 · 热门股TOP{HOT_STOCK_COUNT}精选</p>
                <div class="header-badge">智能推荐系统</div>
            </div>
        </div>

        <div class="content">
            <div class="stock-list">
                {rows_html}
            </div>
            
            <div class="warning-box">
                <div class="warning-content">
                    <div class="warning-icon">⚠️</div>
                    <div class="warning-text">
                        <div class="warning-title">风险提示</div>
                        <div class="warning-message">本推荐基于技术指标量化分析，仅供参考，不构成投资建议。股市有风险，投资需谨慎。</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <div class="footer-links">
                <a href="#" class="footer-link">关于我们</a>
                <a href="#" class="footer-link">使用条款</a>
                <a href="#" class="footer-link">隐私政策</a>
            </div>
            <p>由 stock_recommender.py 自动生成 · 数据来源：东方财富</p>
        </div>
    </div>
    </body>
    </html>
    """

    # 替换模板中的变量
    html_template = html_template.replace("{today_str}", today_str)
    html_template = html_template.replace("{weekday}", weekday)
    html_template = html_template.replace("{HOT_STOCK_COUNT}", str(HOT_STOCK_COUNT))
    html_template = html_template.replace("{rows_html}", rows_html)

    return html_template

def send_email(html_content: str):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.date.today().weekday()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(f"📊 A股买入推荐 TOP3 | {today_str} {weekday}", "utf-8")
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = ", ".join(EMAIL_CONFIG["receiver"])
    
    # 添加纯文本版本作为备选
    plain_text = "A股买入推荐报告\n" + today_str + " " + weekday + "\n\n请在支持HTML的邮件客户端查看完整报告。"
    plain_part = MIMEText(plain_text.encode('utf-8'), "plain", _charset="utf-8")
    msg.attach(plain_part)
    
    # 添加HTML版本 - 确保HTML内容使用正确的编码
    html_part = MIMEText(html_content.encode('utf-8'), "html", _charset="utf-8")
    msg.attach(html_part)

    log.info(f"正在发送邮件至 {EMAIL_CONFIG['receiver']} ...")
    try:
        with smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
            server.sendmail(EMAIL_CONFIG["sender"], EMAIL_CONFIG["receiver"], msg.as_string())
        log.info("邮件发送成功！")
    except Exception as e:
        log.error(f"邮件发送失败: {e}")
        raise
