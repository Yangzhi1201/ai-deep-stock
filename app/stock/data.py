"""
股票数据获取模块
"""
import requests
import pandas as pd
import datetime
from typing import List, Dict, Optional, Union
from app.utils.logging import log

# 东方财富接口配置
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_hot_stocks(top_n: int = 10) -> List[Dict]:
    """
    获取热门股票（东方财富人气榜）
    """
    url = "https://emappdata.eastmoney.com/stock/rank/getbrand/list"
    params = {
        "type": "1",
        "pageSize": str(top_n),
        "page": "1",
        "deviceid": "12345678"
    }
    
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=5)
        data = resp.json()
        rank_list = data.get("data", [])
        
        stocks = []
        for item in rank_list:
            code = item["sc"]
            market = 1 if item["mkt"] == 1 else 0 # 简单推断，实际可能需要更严谨判断
            # 修正市场代码判断：东财 mkt 1=沪, 0=深
            # 但有时候 sc 带有市场前缀
            
            # 这里为了保险，重新解析一下
            if code.startswith("6"):
                market = 1
            else:
                market = 0
                
            stocks.append({
                "code": code,
                "market": market,
                "name": item["on"]
            })
            
        return stocks
    except Exception as e:
        log.error(f"获取热门股票失败: {e}")
        return []

def get_kline_data(code: str, market: int, days: int = 300) -> Optional[pd.DataFrame]:
    """
    获取K线数据
    """
    # 市场代码转换：东财 1=沪, 0=深
    # 我们的系统：1=沪, 0=深
    secid = f"{market}.{code}"
    
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f61", # 日期,开,收,高,低,量,额,涨跌幅
        "klt": "101", # 日K
        "fqt": "1",   # 前复权
        "end": "20500101",
        "lmt": str(days)
    }
    
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=5)
        data = resp.json()
        klines = data.get("data", {}).get("klines", [])
        
        if not klines:
            return None
            
        records = []
        for line in klines:
            parts = line.split(",")
            records.append({
                "日期": parts[0],
                "开盘": float(parts[1]),
                "收盘": float(parts[2]),
                "最高": float(parts[3]),
                "最低": float(parts[4]),
                "成交量": float(parts[5]),
                "成交额": float(parts[6]),
                "涨跌幅": float(parts[7]) if len(parts) > 7 else 0.0
            })
            
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        log.error(f"获取 {code} K线数据失败: {e}")
        return None

def _fill_stock_names(stocks: List[Dict]) -> List[Dict]:
    """
    填充股票名称（如果缺失）
    """
    # 简单实现，如果 name 为空，尝试获取
    # 这里暂时直接返回，因为大多数接口都带了 name
    # 或者如果需要，可以调用 get_kline_data 顺便获取 name（接口里有）
    return stocks

def get_sector_stocks(sector_name: str, top_n: int = 10) -> List[Dict]:
    """
    获取指定板块（行业/概念）的成分股。
    使用东方财富选股API模糊搜索板块。
    
    Args:
        sector_name: 板块名称，如 "电力设备", "AI", "白酒"
        top_n: 返回前多少只股票（按涨跌幅排序）
        
    Returns:
        股票列表 [{"code": "...", "market": 1, "name": "..."}]
    """
    log.info(f"正在搜索板块: {sector_name} ...")
    
    # 1. 搜索板块代码
    # 东方财富板块搜索接口 (示例: 搜索 "电力")
    search_url = "https://searchapi.eastmoney.com/api/suggest/get"
    search_params = {
        "input": sector_name,
        "type": "14", # type=14 通常是板块
        "token": "D43BF722C8E33BDC906FB84D85E326E8",
        "count": "5"
    }
    
    try:
        resp = requests.get(search_url, params=search_params, headers=HEADERS, timeout=10)
        data = resp.json()
        items = data.get("QuotationCodeTable", {}).get("Data", [])
        
        if not items:
            log.warning(f"未找到板块: {sector_name}")
            return []
            
        # 取第一个匹配的板块
        sector_code = items[0]["Code"] # e.g., "BK0428"
        sector_real_name = items[0]["Name"]
        log.info(f"找到板块: {sector_real_name} ({sector_code})")
        
        # 2. 获取板块成分股
        list_url = "https://push2.eastmoney.com/api/qt/clist/get"
        list_params = {
            "pn": "1",
            "pz": str(top_n),
            "po": "1", # 1=desc, 0=asc
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f3", # 按涨跌幅排序
            "fs": f"b:{sector_code}+f:!50",
            "fields": "f12,f13,f14", # f12=code, f13=market, f14=name
        }
        
        resp = requests.get(list_url, params=list_params, headers=HEADERS, timeout=10)
        data = resp.json()
        rows = data.get("data", {}).get("diff", [])
        
        stocks = []
        for row in rows:
            code = row["f12"]
            market_id = row["f13"]
            name = row["f14"]
            
            # 转换 market id: 0=深, 1=沪
            market = 1 if market_id == 1 else 0
            
            stocks.append({
                "code": code,
                "market": market,
                "name": name
            })
            
        return stocks
        
    except Exception as e:
        log.error(f"板块数据获取失败: {e}")
        return []
