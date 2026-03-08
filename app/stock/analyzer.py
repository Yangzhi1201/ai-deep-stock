"""
股票分析核心模块
提供统一的分析功能，支持热门股票分析和指定股票分析
"""
import datetime
import time
from typing import Optional, List, Dict, Tuple
import pandas as pd
from app.stock.data import get_hot_stocks, get_kline_data, _fill_stock_names
from app.stock.indicators import compute_ma, compute_macd, compute_rsi
from app.utils.config import HOT_STOCK_COUNT, RECOMMEND_COUNT
from app.utils.logging import log


def get_recommendation(score: int, signals: List[str]) -> Tuple[str, str]:
    """
    根据评分和信号生成买入建议和风险等级
    返回: (recommendation, risk_level)
    """
    if score >= 80:
        return ("强烈推荐", "中等")
    elif score >= 60:
        return ("推荐买入", "中等")
    elif score >= 40:
        return ("谨慎关注", "较高")
    elif score >= 20:
        return ("观望", "高")
    else:
        return ("不建议", "很高")


def analyze_stock(code: str, market: int, name: str) -> Optional[Dict]:
    """
    分析单只股票的技术指标
    
    评分体系（满分 100）：
      - MA 均线系统：最高 40 分
      - MACD 指标：  最高 45 分
      - RSI 指标：   最高 25 分（超买扣分）
      - 量价配合：   最高 15 分
    """
    df = get_kline_data(code, market)
    if df is None or len(df) < 60:
        log.warning(f"  {name}({code}) 数据不足（{0 if df is None else len(df)}条），跳过")
        return None

    close = df["收盘"]
    vol = df["成交量"]
    score = 0
    signals = []

    # ── MA 均线分析 ──
    ma5 = compute_ma(close, 5)
    ma10 = compute_ma(close, 10)
    ma20 = compute_ma(close, 20)
    ma60 = compute_ma(close, 60)

    if ma5.iloc[-1] > ma10.iloc[-1] and ma5.iloc[-2] <= ma10.iloc[-2]:
        score += 20
        signals.append("MA5/MA10 金叉 ↑")
    if ma5.iloc[-1] > ma20.iloc[-1]:
        score += 10
        signals.append("短期均线多头排列")
    if close.iloc[-1] > ma60.iloc[-1]:
        score += 10
        signals.append("站上60日均线")

    # ── MACD 分析 ──
    dif, dea, macd_hist = compute_macd(close)
    if dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2]:
        score += 25
        signals.append("MACD 金叉 ↑")
    if macd_hist.iloc[-1] > 0 and macd_hist.iloc[-2] <= 0:
        score += 15
        signals.append("MACD 柱转正")
    if dif.iloc[-1] > 0:
        score += 5
        signals.append("MACD 多头区域")

    # ── RSI 分析 ──
    rsi = compute_rsi(close, 14)
    rsi_val = rsi.iloc[-1]
    if pd.isna(rsi_val):
        rsi_val = 50.0
    if rsi_val < 30:
        score += 25
        signals.append(f"RSI={rsi_val:.1f} 超卖区")
    elif rsi_val < 40:
        score += 15
        signals.append(f"RSI={rsi_val:.1f} 偏弱反弹区")
    elif 40 <= rsi_val <= 60:
        score += 10
        signals.append(f"RSI={rsi_val:.1f} 中性")
    elif rsi_val > 80:
        score -= 15
        signals.append(f"RSI={rsi_val:.1f} ⚠ 超买")

    # ── 量价配合 ──
    vol_ma5 = vol.rolling(5).mean()
    if vol.iloc[-1] > vol_ma5.iloc[-1] * 1.3 and close.iloc[-1] > close.iloc[-2]:
        score += 15
        signals.append("放量上涨")

    latest_price = close.iloc[-1]
    change_pct = df["涨跌幅"].iloc[-1]
    
    # 生成买入建议和风险等级
    recommendation, risk_level = get_recommendation(score, signals)

    # 确保 name 不为空
    if not name or name == code:
        name = code # 至少显示代码

    return {
        "代码": code,
        "名称": name,
        "最新价": f"{latest_price:.2f}",
        "涨跌幅": f"{change_pct:+.2f}%",
        "综合评分": score,
        "买入信号": signals,
        "RSI": f"{rsi_val:.1f}",
        "MACD_DIF": f"{dif.iloc[-1]:.3f}",
        "MACD_DEA": f"{dea.iloc[-1]:.3f}",
        "recommendation": recommendation,
        "risk_level": risk_level
    }


def analyze_stocks_batch(
    stocks: List[Dict],
    sort_by: str = "综合评分",
    sort_order: str = "desc",
    delay: float = 0.3
) -> Tuple[List[Dict], Dict]:
    """
    批量分析多只股票
    
    Args:
        stocks: 股票列表，每个元素包含 code, market, name
        sort_by: 排序字段
        sort_order: 排序方向 (asc/desc)
        delay: 请求间隔时间（秒）
    
    Returns:
        (results, summary): 分析结果列表和汇总统计
    """
    log.info(f"开始批量分析 {len(stocks)} 只股票...")
    
    results = []
    failed_stocks = []
    
    # 填充股票名称
    # 注意：get_hot_stocks 已经调用过一次 _fill_stock_names，但如果是手动传入的列表可能未填充
    # 这里再次调用确保万无一失
    from app.stock.data import _fill_stock_names
    filled_stocks = _fill_stock_names(stocks)
    
    for stock in filled_stocks:
        # 确保 name 存在，如果还是没有，就用 code 代替
        stock_name = stock.get("name") or stock.get("code")
        log.info(f"  分析: {stock_name} ({stock['code']}) ...")
        
        result = analyze_stock(stock["code"], stock["market"], stock_name)
        
        if result:
            results.append(result)
        else:
            failed_stocks.append(f"{stock['name']}({stock['code']})")
        
        time.sleep(delay)  # 请求间隔，防止限频
    
    # 排序
    reverse = sort_order.lower() == "desc"
    
    if sort_by == "涨跌幅":
        # 涨跌幅需要特殊处理，去除百分号并转为浮点数
        results.sort(key=lambda x: float(x["涨跌幅"].replace("%", "")), reverse=reverse)
    else:
        results.sort(key=lambda x: x.get(sort_by, x["综合评分"]), reverse=reverse)
    
    # 生成汇总统计
    summary = {
        "total": len(stocks),
        "success": len(results),
        "failed": len(failed_stocks),
        "failed_stocks": failed_stocks,
        "strong_buy": len([r for r in results if r["recommendation"] == "强烈推荐"]),
        "buy": len([r for r in results if r["recommendation"] == "推荐买入"]),
        "watch": len([r for r in results if r["recommendation"] == "谨慎关注"]),
        "wait": len([r for r in results if r["recommendation"] == "观望"]),
        "avoid": len([r for r in results if r["recommendation"] == "不建议"]),
        "average_score": round(sum(r["综合评分"] for r in results) / len(results), 2) if results else 0,
        "highest_score_stock": max(results, key=lambda x: x["综合评分"])["名称"] if results else None,
        "lowest_score_stock": min(results, key=lambda x: x["综合评分"])["名称"] if results else None,
    }
    
    message = f"成功分析 {len(results)}/{len(stocks)} 只股票"
    if failed_stocks:
        message += f"，失败: {', '.join(failed_stocks)}"
    
    log.info(f"分析完成: {message}")
    
    return results, summary


def run_hot_stocks_analysis(top_n: int = HOT_STOCK_COUNT, recommend_n: int = RECOMMEND_COUNT) -> List[Dict]:
    """
    运行热门股票分析（每日推荐任务使用）
    
    Args:
        top_n: 获取热门股票数量
        recommend_n: 推荐股票数量
    
    Returns:
        推荐股票列表
    """
    hot_stocks = get_hot_stocks(top_n=top_n)
    
    results, summary = analyze_stocks_batch(
        stocks=hot_stocks,
        sort_by="综合评分",
        sort_order="desc",
        delay=0.3
    )
    
    # 过滤：仅保留 "强烈推荐" 或 "推荐买入" 的股票
    filtered_results = [
        r for r in results 
        if r["recommendation"] in ["强烈推荐", "推荐买入"]
    ]
    
    # 返回前N个推荐
    top_results = filtered_results[:recommend_n]
    log.info(f"推荐 TOP {recommend_n} (已过滤非买入评级): {[r['名称'] for r in top_results]}")
    
    return top_results


def parse_stock_code(stock_str: str) -> Dict:
    """
    解析股票代码字符串
    
    支持格式：
    - 600410.SH 或 600410.sh（沪市）
    - 002261.SZ 或 002261.sz（深市）
    - 600410（自动判断市场）
    """
    stock_str = stock_str.strip().upper()
    
    if ".SH" in stock_str:
        code = stock_str.replace(".SH", "")
        return {"code": code, "market": 1, "name": ""}
    elif ".SZ" in stock_str:
        code = stock_str.replace(".SZ", "")
        return {"code": code, "market": 0, "name": ""}
    else:
        # 根据代码前缀判断市场
        # 沪市：600, 601, 603, 688, 689
        # 深市：000, 001, 002, 003, 300, 301
        code = stock_str
        if code.startswith(("6", "68", "69")):
            return {"code": code, "market": 1, "name": ""}
        else:
            return {"code": code, "market": 0, "name": ""}
