import requests
import time
import datetime
import pandas as pd
from typing import Optional, List, Dict
from app.utils.logging import log

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://guba.eastmoney.com/",
}

def get_hot_stocks(top_n: int = 10) -> List[Dict]:
    """
    调用东方财富人气榜 API，获取热门股票列表。
    返回: [{"code": "600410", "market": 1, "name": ""}, ...]
    market: 1=沪市, 0=深市
    """
    log.info("正在获取热门股票排行...")
    url = "https://emappdata.eastmoney.com/stockrank/getAllCurrentList"
    payload = {
        "appId": "appId01",
        "globalId": "786e4c21-70dc-435a-93bb-38",
        "marketType": "",
        "pageNo": 1,
        "pageSize": top_n,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        stocks = []
        for item in data.get("data", []):
            sc = item["sc"]  # 如 "SH600410" / "SZ002261"
            market = 1 if sc.startswith("SH") else 0
            code = sc[2:]
            stocks.append({"code": code, "market": market, "name": ""})

        # 批量获取股票名称
        stocks = _fill_stock_names(stocks)
        log.info(f"获取到热门股票 {len(stocks)} 只: {[s['name'] or s['code'] for s in stocks]}")
        return stocks

    except Exception as e:
        log.error(f"热门股票获取失败: {e}")
        raise


def _fill_stock_names(stocks: List[Dict]) -> List[Dict]:
    """通过 K 线接口的 name 字段获取股票名称"""
    for s in stocks:
        secid = f"{s['market']}.{s['code']}"
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51",
            "klt": 101,
            "fqt": 1,
            "beg": "0",
            "end": "20500101",
            "lmt": 1,
        }
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            data = resp.json()
            s["name"] = data.get("data", {}).get("name", s["code"])
        except Exception:
            s["name"] = s["code"]
        time.sleep(0.1)
    return stocks


def get_kline_data(code: str, market: int, days: int = 250) -> Optional[pd.DataFrame]:
    """
    获取个股日K线（前复权），返回 DataFrame。
    列: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
    """
    secid = f"{market}.{code}"
    start = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y%m%d")
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": 101,       # 日K
        "fqt": 1,         # 前复权
        "beg": start,
        "end": "20500101",
        "lmt": 500,
    }

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        klines = data.get("data", {}).get("klines", [])
        if not klines:
            return None

        rows = [k.split(",") for k in klines]
        df = pd.DataFrame(rows, columns=[
            "日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额",
            "振幅", "涨跌幅", "涨跌额", "换手率"
        ])
        for col in ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    except Exception as e:
        log.warning(f"  K线数据获取失败 ({code}): {e}")
        return None