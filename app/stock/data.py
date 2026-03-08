"""
股票数据获取模块
"""
import requests
import pandas as pd
import datetime
from typing import List, Dict, Optional, Union
from app.utils.logging import log
from app.config import get_settings

# 东方财富接口配置
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

settings = get_settings()

def get_hot_stocks(top_n: int = 10) -> List[Dict]:
    """
    获取热门股票（东方财富人气榜）
    """
    # 东方财富人气榜新接口 (需 POST)
    url = settings.eastmoney_hot_list_url
    
    # 必须的 Headers
    headers = HEADERS.copy()
    headers.update({
        "Content-Type": "application/json",
        "Host": "emappdata.eastmoney.com",
        "Origin": "https://vipmoney.eastmoney.com",
        "Referer": "https://vipmoney.eastmoney.com/collect/stockranking/pages/ranking/list.html"
    })
    
    payload = {
        "appId": "appId01",
        "globalId": settings.eastmoney_global_id,
        "marketType": "",
        "pageNo": 1,
        "pageSize": top_n
    }
    
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=settings.eastmoney_timeout)
        data = resp.json()
        items = data.get("data", [])
        
        stocks = []
        for item in items:
            # item: {'sc': 'SH600519', 'rk': 1, ...}
            raw_code = item.get("sc", "") # e.g., "SH600519"
            
            # 解析市场和代码
            if raw_code.startswith("SH"):
                market = 1
                code = raw_code[2:]
            elif raw_code.startswith("SZ"):
                market = 0
                code = raw_code[2:]
            else:
                # 尝试猜测
                if raw_code.startswith("6"):
                    market = 1
                    code = raw_code
                else:
                    market = 0
                    code = raw_code

            # 获取股票名称 (接口只返回代码，需额外获取或在后续流程补充)
            # 这里先给个默认值，或者尝试通过 K 线接口顺便获取名字
            # 为保持流程简单，这里先置空，依赖后续 _fill_stock_names 或 get_kline_data 补充
            name = code # 暂用代码代替
            
            stocks.append({
                "code": code,
                "market": market,
                "name": name # 暂时缺失
            })
            
        # 补充股票名称
        stocks = _fill_stock_names(stocks)
            
        return stocks
    except Exception as e:
        log.error(f"获取热门股票失败: {e}")
        return []

def _fill_stock_names(stocks: List[Dict]) -> List[Dict]:
    """
    批量或单独填充股票名称
    """
    for stock in stocks:
        # 如果 name 为空，或者 name 和 code 相同（有些地方用 code 占位）
        if not stock.get("name") or stock["name"] == stock["code"]: 
            try:
                # https://searchapi.eastmoney.com/api/suggest/get?input=600519&type=14
                suggest_url = settings.eastmoney_suggest_url
                params = {
                    "input": stock["code"],
                    "type": "14",
                    "token": settings.eastmoney_token
                }
                resp = requests.get(suggest_url, params=params, headers=HEADERS, timeout=settings.eastmoney_timeout)
                data = resp.json()
                items = data.get("QuotationCodeTable", {}).get("Data", [])
                if items:
                    stock["name"] = items[0]["Name"]
                    # log.debug(f"已获取股票名称: {stock['code']} -> {stock['name']}")
            except Exception as e:
                # log.warning(f"获取股票名称失败 {stock['code']}: {e}")
                pass
                
    return stocks

def get_kline_data(code: str, market: int, days: int = 300) -> Optional[pd.DataFrame]:
    """
    获取K线数据
    """
    # 市场代码转换：东财 1=沪, 0=深
    # 我们的系统：1=沪, 0=深
    secid = f"{market}.{code}"
    
    url = settings.eastmoney_kline_url
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
        resp = requests.get(url, params=params, headers=HEADERS, timeout=settings.eastmoney_timeout)
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
    search_url = settings.eastmoney_suggest_url
    search_params = {
        "input": sector_name,
        "type": "14", # type=14 通常是板块
        "token": settings.eastmoney_token,
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
        list_url = settings.eastmoney_clist_url
        list_params = {
            "pn": "1",
            "pz": str(top_n),
            "po": "1", # 1=desc, 0=asc
            "np": "1",
            "ut": settings.eastmoney_ut,
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
