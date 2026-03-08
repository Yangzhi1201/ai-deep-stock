import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import List, Dict, Tuple
from app.utils.config import EMAIL_CONFIG, HOT_STOCK_COUNT
from app.utils.logging import log


def get_base_styles() -> str:
    """获取基础CSS样式"""
    return """
    <style>
        /* ========== 设计系统变量 ========== */
        :root {
            --primary: #1a1a2e;
            --primary-light: #16213e;
            --accent: #0f3460;
            --highlight: #e94560;
            --success: #00d9a5;
            --danger: #ff4757;
            --warning: #ffa502;
            --info: #3742fa;
            --text-primary: #2f3542;
            --text-secondary: #57606f;
            --text-muted: #a4b0be;
            --background: #f1f2f6;
            --surface: #ffffff;
            --surface-elevated: #f8f9fa;
            --border: #dfe4ea;
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.04);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
            --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
        }
        
        /* ========== 基础重置 ========== */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: var(--background);
            color: var(--text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }
        
        /* ========== 容器 ========== */
        .email-wrapper {
            max-width: 720px;
            margin: 0 auto;
            background: var(--surface);
            min-height: 100vh;
        }
        
        /* ========== 头部区域 ========== */
        .email-header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 50%, var(--accent) 100%);
            color: white;
            padding: 40px 24px;
            position: relative;
            overflow: hidden;
        }
        
        .email-header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(233,69,96,0.15) 0%, transparent 70%);
            border-radius: 50%;
        }
        
        .email-header::after {
            content: '';
            position: absolute;
            bottom: -30%;
            left: -10%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(0,217,165,0.1) 0%, transparent 70%);
            border-radius: 50%;
        }
        
        .header-content {
            position: relative;
            z-index: 1;
        }
        
        .header-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            margin-bottom: 16px;
            border: 1px solid rgba(255,255,255,0.15);
        }
        
        .header-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        
        .header-subtitle {
            font-size: 15px;
            opacity: 0.85;
            font-weight: 400;
        }
        
        .header-meta {
            display: flex;
            gap: 16px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .meta-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            opacity: 0.9;
        }
        
        /* ========== 内容区域 ========== */
        .email-body {
            padding: 24px;
        }
        
        /* ========== 统计卡片 ========== */
        .stats-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
        }
        
        .stat-card {
            background: var(--surface-elevated);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 16px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: var(--highlight);
            margin-bottom: 4px;
        }
        
        .stat-label {
            font-size: 12px;
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        /* ========== 股票列表 ========== */
        .stock-list {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        /* ========== 股票卡片 ========== */
        .stock-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-sm);
            transition: box-shadow 0.3s;
        }
        
        .stock-card:hover {
            box-shadow: var(--shadow-md);
        }
        
        .stock-card-header {
            display: flex;
            align-items: center;
            padding: 20px;
            background: linear-gradient(to right, var(--surface-elevated), var(--surface));
            border-bottom: 1px solid var(--border);
        }
        
        .stock-rank {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: 700;
            margin-right: 16px;
            flex-shrink: 0;
        }
        
        .rank-1 { background: linear-gradient(135deg, #ffd700, #ffaa00); color: white; }
        .rank-2 { background: linear-gradient(135deg, #c0c0c0, #a0a0a0); color: white; }
        .rank-3 { background: linear-gradient(135deg, #cd7f32, #b87333); color: white; }
        .rank-other { background: var(--surface-elevated); color: var(--text-secondary); border: 2px solid var(--border); }
        
        .stock-info {
            flex: 1;
            min-width: 0;
        }
        
        .stock-name {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        
        .stock-code {
            font-size: 13px;
            color: var(--text-muted);
            font-family: 'SF Mono', monospace;
        }
        
        .stock-price-section {
            text-align: right;
            margin-left: 16px;
        }
        
        .stock-price {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        
        .stock-change {
            font-size: 14px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 20px;
            display: inline-block;
        }
        
        .change-up {
            background: rgba(0, 217, 165, 0.12);
            color: var(--success);
        }
        
        .change-down {
            background: rgba(255, 71, 87, 0.12);
            color: var(--danger);
        }
        
        /* ========== 指标网格 ========== */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1px;
            background: var(--border);
        }
        
        .metric-cell {
            background: var(--surface);
            padding: 16px 12px;
            text-align: center;
        }
        
        .metric-name {
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        
        .metric-value {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .metric-highlight {
            color: var(--highlight);
        }
        
        /* ========== 信号标签 ========== */
        .signals-section {
            padding: 16px 20px;
            background: var(--surface-elevated);
            border-top: 1px solid var(--border);
        }
        
        .signals-title {
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 10px;
            font-weight: 500;
        }
        
        .signals-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .signal-tag {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .signal-buy {
            background: rgba(0, 217, 165, 0.12);
            color: var(--success);
        }
        
        .signal-watch {
            background: rgba(255, 165, 2, 0.12);
            color: var(--warning);
        }
        
        .signal-neutral {
            background: rgba(55, 66, 250, 0.08);
            color: var(--info);
        }
        
        /* ========== 推荐等级 ========== */
        .recommendation-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 24px;
            font-size: 13px;
            font-weight: 600;
        }
        
        .rec-strong {
            background: linear-gradient(135deg, rgba(0, 217, 165, 0.15), rgba(0, 217, 165, 0.05));
            color: #00a884;
            border: 1px solid rgba(0, 217, 165, 0.3);
        }
        
        .rec-buy {
            background: linear-gradient(135deg, rgba(55, 66, 250, 0.12), rgba(55, 66, 250, 0.04));
            color: var(--info);
            border: 1px solid rgba(55, 66, 250, 0.25);
        }
        
        .rec-watch {
            background: linear-gradient(135deg, rgba(255, 165, 2, 0.12), rgba(255, 165, 2, 0.04));
            color: #d48f00;
            border: 1px solid rgba(255, 165, 2, 0.25);
        }
        
        /* ========== 风险提示 ========== */
        .risk-notice {
            margin-top: 32px;
            padding: 20px;
            background: linear-gradient(135deg, #fff9e6, #fff5d6);
            border-left: 4px solid var(--warning);
            border-radius: var(--radius-md);
        }
        
        .risk-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 600;
            color: #8b6914;
            margin-bottom: 8px;
        }
        
        .risk-text {
            font-size: 13px;
            color: #a0822a;
            line-height: 1.7;
        }
        
        /* ========== 页脚 ========== */
        .email-footer {
            text-align: center;
            padding: 32px 24px;
            background: var(--surface-elevated);
            border-top: 1px solid var(--border);
        }
        
        .footer-brand {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .footer-text {
            font-size: 12px;
            color: var(--text-muted);
        }
        
        /* ========== 响应式 ========== */
        @media (max-width: 600px) {
            .email-header { padding: 28px 20px; }
            .header-title { font-size: 22px; }
            .email-body { padding: 16px; }
            .metrics-grid { grid-template-columns: repeat(2, 1fr); }
            .stock-card-header { padding: 16px; }
            .stock-rank { width: 38px; height: 38px; font-size: 15px; }
        }
    </style>
    """


def build_stock_card(stock: Dict, rank: int) -> str:
    """构建单个股票卡片HTML"""
    medal_class = f"rank-{rank}" if rank <= 3 else "rank-other"
    medal_text = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else str(rank)
    
    change_class = "change-up" if stock["涨跌幅"].startswith("+") else "change-down"
    
    # 买入信号标签
    signals_html = ""
    for signal in stock.get("买入信号", []):
        if "金叉" in signal or "买入" in signal:
            signals_html += f'<span class="signal-tag signal-buy">📈 {signal}</span>'
        elif "超卖" in signal or "反弹" in signal:
            signals_html += f'<span class="signal-tag signal-watch">📊 {signal}</span>'
        else:
            signals_html += f'<span class="signal-tag signal-neutral">📉 {signal}</span>'
    
    # 推荐等级
    recommendation = stock.get("recommendation", "观望")
    if "强烈" in recommendation or "推荐买入" in recommendation:
        rec_class = "rec-strong"
        rec_icon = "🔥"
    elif "买入" in recommendation:
        rec_class = "rec-buy"
        rec_icon = "✓"
    else:
        rec_class = "rec-watch"
        rec_icon = "👁"
    
    return f"""
    <div class="stock-card">
        <div class="stock-card-header">
            <div class="stock-rank {medal_class}">{medal_text}</div>
            <div class="stock-info">
                <div class="stock-name">{stock['名称']}</div>
                <div class="stock-code">{stock['代码']}</div>
            </div>
            <div class="stock-price-section">
                <div class="stock-price">¥{stock['最新价']}</div>
                <span class="stock-change {change_class}">{stock['涨跌幅']}</span>
            </div>
        </div>
        <div class="metrics-grid">
            <div class="metric-cell">
                <div class="metric-name">综合评分</div>
                <div class="metric-value metric-highlight">{stock['综合评分']}分</div>
            </div>
            <div class="metric-cell">
                <div class="metric-name">RSI指标</div>
                <div class="metric-value">{stock['RSI']}</div>
            </div>
            <div class="metric-cell">
                <div class="metric-name">MACD DIF</div>
                <div class="metric-value">{stock['MACD_DIF']}</div>
            </div>
            <div class="metric-cell">
                <div class="metric-name">MACD DEA</div>
                <div class="metric-value">{stock['MACD_DEA']}</div>
            </div>
        </div>
        <div class="signals-section">
            <div class="signals-title">买入信号</div>
            <div class="signals-list">
                {signals_html}
                <span class="recommendation-badge {rec_class}">{rec_icon} {recommendation}</span>
            </div>
        </div>
    </div>
    """


def build_daily_recommendation_html(recommendations: List[Dict]) -> str:
    """构建每日推荐邮件HTML"""
    today_str = datetime.date.today().strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.date.today().weekday()]
    
    if not recommendations:
        return build_empty_html("今日未筛选到符合条件的股票", "请关注后续推送或调整筛选条件")
    
    # 统计信息
    avg_score = sum(r["综合评分"] for r in recommendations) / len(recommendations) if recommendations else 0
    up_count = sum(1 for r in recommendations if r["涨跌幅"].startswith("+"))
    
    # 构建股票卡片
    cards_html = ""
    for i, stock in enumerate(recommendations, 1):
        cards_html += build_stock_card(stock, i)
    
    styles = get_base_styles()
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日股票推荐</title>
    {styles}
</head>
<body>
    <div class="email-wrapper">
        <div class="email-header">
            <div class="header-content">
                <div class="header-badge">📊 每日精选</div>
                <h1 class="header-title">A股买入推荐</h1>
                <p class="header-subtitle">基于技术面分析的优质股票筛选</p>
                <div class="header-meta">
                    <div class="meta-item">📅 {today_str} {weekday}</div>
                    <div class="meta-item">📈 精选 {len(recommendations)} 只</div>
                    <div class="meta-item">🔥 平均评分 {avg_score:.1f}</div>
                </div>
            </div>
        </div>
        
        <div class="email-body">
            <div class="stats-bar">
                <div class="stat-card">
                    <div class="stat-value">{len(recommendations)}</div>
                    <div class="stat-label">推荐数量</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_score:.0f}</div>
                    <div class="stat-label">平均评分</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{up_count}</div>
                    <div class="stat-label">上涨家数</div>
                </div>
            </div>
            
            <div class="stock-list">
                {cards_html}
            </div>
            
            <div class="risk-notice">
                <div class="risk-title">⚠️ 风险提示</div>
                <div class="risk-text">
                    本推荐基于技术指标量化分析，仅供参考，不构成投资建议。股市有风险，投资需谨慎。
                    请结合自身风险承受能力和投资目标做出决策。
                </div>
            </div>
        </div>
        
        <div class="email-footer">
            <div class="footer-brand">AI-Deep-Stock</div>
            <div class="footer-text">智能股票分析系统 · 数据来源：东方财富</div>
        </div>
    </div>
</body>
</html>"""


def build_compare_html(recommendations: List[Dict], summary: Dict = None) -> str:
    """构建股票对比邮件HTML"""
    today_str = datetime.date.today().strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.date.today().weekday()]
    
    if not recommendations:
        return build_empty_html("对比分析暂无结果", "请检查股票代码是否正确")
    
    # 统计信息
    avg_score = summary.get("average_score", 0) if summary else 0
    strong_buy = summary.get("strong_buy", 0) if summary else 0
    buy = summary.get("buy", 0) if summary else 0
    
    # 构建股票卡片
    cards_html = ""
    for i, stock in enumerate(recommendations, 1):
        cards_html += build_stock_card(stock, i)
    
    styles = get_base_styles()
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票对比分析</title>
    {styles}
</head>
<body>
    <div class="email-wrapper">
        <div class="email-header">
            <div class="header-content">
                <div class="header-badge">⚖️ 综合对比</div>
                <h1 class="header-title">股票对比分析报告</h1>
                <p class="header-subtitle">多维度技术指标对比，助您做出明智决策</p>
                <div class="header-meta">
                    <div class="meta-item">📅 {today_str} {weekday}</div>
                    <div class="meta-item">📊 对比 {len(recommendations)} 只股票</div>
                    <div class="meta-item">✓ 按评分排序</div>
                </div>
            </div>
        </div>
        
        <div class="email-body">
            <div class="stats-bar">
                <div class="stat-card">
                    <div class="stat-value">{len(recommendations)}</div>
                    <div class="stat-label">对比数量</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_score:.0f}</div>
                    <div class="stat-label">平均评分</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{strong_buy + buy}</div>
                    <div class="stat-label">推荐买入</div>
                </div>
            </div>
            
            <div class="stock-list">
                {cards_html}
            </div>
            
            <div class="risk-notice">
                <div class="risk-title">⚠️ 风险提示</div>
                <div class="risk-text">
                    本对比分析基于技术指标量化评估，仅供参考，不构成投资建议。
                    股票投资存在风险，请结合自身情况谨慎决策。
                </div>
            </div>
        </div>
        
        <div class="email-footer">
            <div class="footer-brand">AI-Deep-Stock</div>
            <div class="footer-text">智能股票分析系统 · 数据来源：东方财富</div>
        </div>
    </div>
</body>
</html>"""


def build_empty_html(title: str, subtitle: str) -> str:
    """构建空状态HTML"""
    styles = get_base_styles()
    today_str = datetime.date.today().strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.date.today().weekday()]
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票分析报告</title>
    {styles}
</head>
<body>
    <div class="email-wrapper">
        <div class="email-header">
            <div class="header-content">
                <div class="header-badge">📊 分析报告</div>
                <h1 class="header-title">{title}</h1>
                <p class="header-subtitle">{subtitle}</p>
                <div class="header-meta">
                    <div class="meta-item">📅 {today_str} {weekday}</div>
                </div>
            </div>
        </div>
        
        <div class="email-body">
            <div style="text-align: center; padding: 60px 20px;">
                <div style="font-size: 64px; margin-bottom: 20px;">📭</div>
                <div style="font-size: 18px; color: var(--text-secondary); margin-bottom: 8px;">{title}</div>
                <div style="font-size: 14px; color: var(--text-muted);">{subtitle}</div>
            </div>
            
            <div class="risk-notice">
                <div class="risk-title">⚠️ 提示</div>
                <div class="risk-text">
                    如需获取最新推荐，请稍后再试或调整筛选条件。
                </div>
            </div>
        </div>
        
        <div class="email-footer">
            <div class="footer-brand">AI-Deep-Stock</div>
            <div class="footer-text">智能股票分析系统</div>
        </div>
    </div>
</body>
</html>"""


def send_daily_recommendation_email(recommendations: List[Dict]):
    """发送每日推荐邮件"""
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.date.today().weekday()]
    
    html_content = build_daily_recommendation_html(recommendations)
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(f"📊 每日股票推荐 | {today_str} {weekday} | TOP{len(recommendations)}精选", "utf-8")
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = ", ".join(EMAIL_CONFIG["receiver"])
    
    # 纯文本版本
    plain_text = f"每日股票推荐报告\n{today_str} {weekday}\n共推荐 {len(recommendations)} 只股票\n\n请在支持HTML的邮件客户端查看完整报告。"
    plain_part = MIMEText(plain_text.encode('utf-8'), "plain", _charset="utf-8")
    msg.attach(plain_part)
    
    # HTML版本
    html_part = MIMEText(html_content.encode('utf-8'), "html", _charset="utf-8")
    msg.attach(html_part)
    
    _send_email(msg)


def send_compare_email(recommendations: List[Dict], summary: Dict = None):
    """发送股票对比邮件"""
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.date.today().weekday()]
    
    html_content = build_compare_html(recommendations, summary)
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(f"⚖️ 股票对比分析 | {today_str} {weekday} | {len(recommendations)}只股票", "utf-8")
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = ", ".join(EMAIL_CONFIG["receiver"])
    
    # 纯文本版本
    plain_text = f"股票对比分析报告\n{today_str} {weekday}\n共对比 {len(recommendations)} 只股票\n\n请在支持HTML的邮件客户端查看完整报告。"
    plain_part = MIMEText(plain_text.encode('utf-8'), "plain", _charset="utf-8")
    msg.attach(plain_part)
    
    # HTML版本
    html_part = MIMEText(html_content.encode('utf-8'), "html", _charset="utf-8")
    msg.attach(html_part)
    
    _send_email(msg)


def _send_email(msg: MIMEMultipart):
    """发送邮件"""
    log.info(f"正在发送邮件至 {EMAIL_CONFIG['receiver']} ...")
    try:
        with smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
            server.sendmail(EMAIL_CONFIG["sender"], EMAIL_CONFIG["receiver"], msg.as_string())
        log.info("邮件发送成功！")
    except Exception as e:
        log.error(f"邮件发送失败: {e}")
        raise


def send_custom_email(subject: str, content: str, to_list: List[str] = None):
    """
    发送自定义邮件
    
    Args:
        subject: 邮件主题
        content: 邮件HTML内容
        to_list: 收件人列表，如果为None则使用默认配置
    """
    if to_list is None:
        to_list = EMAIL_CONFIG["receiver"]
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = ", ".join(to_list)
    
    # 纯文本版本
    plain_text = "请在支持HTML的邮件客户端查看完整内容。"
    plain_part = MIMEText(plain_text.encode('utf-8'), "plain", _charset="utf-8")
    msg.attach(plain_part)
    
    # HTML版本
    html_part = MIMEText(content.encode('utf-8'), "html", _charset="utf-8")
    msg.attach(html_part)
    
    # 使用 _send_email 发送
    # 注意：_send_email 内部写死了 receiver 变量作为参数传给 sendmail，我们需要稍微调整 _send_email
    # 或者我们在这里直接重写发送逻辑
    
    log.info(f"正在发送自定义邮件至 {to_list} ...")
    try:
        with smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
            server.sendmail(EMAIL_CONFIG["sender"], to_list, msg.as_string())
        log.info("自定义邮件发送成功！")
    except Exception as e:
        log.error(f"自定义邮件发送失败: {e}")
        raise

# 兼容旧接口

def build_email_html(recommendations: List[Dict]) -> str:
    """兼容旧接口，默认使用每日推荐模板"""
    return build_daily_recommendation_html(recommendations)


def send_email(html_content: str):
    """兼容旧接口"""
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.date.today().weekday()]
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(f"📊 A股买入推荐 | {today_str} {weekday}", "utf-8")
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = ", ".join(EMAIL_CONFIG["receiver"])
    
    plain_text = f"A股买入推荐报告\n{today_str} {weekday}\n\n请在支持HTML的邮件客户端查看完整报告。"
    plain_part = MIMEText(plain_text.encode('utf-8'), "plain", _charset="utf-8")
    msg.attach(plain_part)
    
    html_part = MIMEText(html_content.encode('utf-8'), "html", _charset="utf-8")
    msg.attach(html_part)
    
    _send_email(msg)
