import datetime
import time
from typing import Optional, List, Dict
import pandas as pd
from app.stock.data import get_hot_stocks, get_kline_data
from app.stock.indicators import compute_ma, compute_macd, compute_rsi
from app.utils.config import HOT_STOCK_COUNT, RECOMMEND_COUNT
from app.utils.logging import log

def analyze_stock(code: str, market: int, name: str) -> Optional[Dict]:
    """
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
    }

def run_analysis() -> List[Dict]:
    hot_stocks = get_hot_stocks(top_n=HOT_STOCK_COUNT)
    results = []

    for s in hot_stocks:
        log.info(f"  分析: {s['name']} ({s['code']}) ...")
        result = analyze_stock(s["code"], s["market"], s["name"])
        if result:
            results.append(result)
        time.sleep(0.3)  # 请求间隔，防止限频

    results.sort(key=lambda x: x["综合评分"], reverse=True)
    top = results[:RECOMMEND_COUNT]
    log.info(f"推荐 TOP {RECOMMEND_COUNT}: {[r['名称'] for r in top]}")
    return top