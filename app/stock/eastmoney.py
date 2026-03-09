"""
东方财富数据接口封装模块
提供热门股票、K线数据、板块数据等接口的封装
"""
import requests
import pandas as pd
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.utils.logging import log
from app.config import get_settings

settings = get_settings()

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 配置带有重试机制的 Session
_session = requests.Session()
_retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
_session.mount('http://', HTTPAdapter(max_retries=_retries))
_session.mount('https://', HTTPAdapter(max_retries=_retries))


class EastMoneyClient:
    """
    东方财富 API 客户端
    封装所有东方财富相关的数据接口
    """
    
    def __init__(self):
        self.headers = DEFAULT_HEADERS.copy()
        self.session = _session
        self.timeout = settings.eastmoney_timeout
    
    def get_hot_stocks(self, top_n: int = 10) -> List[Dict]:
        """
        获取热门股票（东方财富人气榜）
        
        Args:
            top_n: 获取前 N 只股票
            
        Returns:
            股票列表，每个元素包含 code, market, name
        """
        url = settings.eastmoney_hot_list_url
        
        headers = self.headers.copy()
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
            resp = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
            data = resp.json()
            items = data.get("data", [])
            
            stocks = []
            for item in items:
                raw_code = item.get("sc", "")  # e.g., "SH600519"
                
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
                
                stocks.append({
                    "code": code,
                    "market": market,
                    "name": code  # 暂时用代码代替，后续会填充
                })
            
            # 补充股票名称
            stocks = self._fill_stock_names(stocks)
            return stocks
            
        except Exception as e:
            log.error(f"获取热门股票失败: {e}")
            return []
    
    def _fill_stock_names(self, stocks: List[Dict]) -> List[Dict]:
        """
        批量填充股票名称
        
        Args:
            stocks: 股票列表
            
        Returns:
            填充好名称的股票列表
        """
        for stock in stocks:
            if not stock.get("name") or stock["name"] == stock["code"]:
                try:
                    name = self.get_stock_name(stock["code"])
                    if name:
                        stock["name"] = name
                except Exception:
                    pass
        return stocks
    
    def get_stock_name(self, code: str) -> Optional[str]:
        """
        根据股票代码获取股票名称
        
        Args:
            code: 股票代码，如 "600519"
            
        Returns:
            股票名称，如 "贵州茅台"
        """
        try:
            url = settings.eastmoney_suggest_url
            params = {
                "input": code,
                "type": "14",
                "token": settings.eastmoney_token
            }
            resp = self.session.get(url, params=params, headers=self.headers, timeout=self.timeout)
            data = resp.json()
            items = data.get("QuotationCodeTable", {}).get("Data", [])
            if items:
                return items[0]["Name"]
        except Exception as e:
            log.warning(f"获取股票名称失败 {code}: {e}")
        return None
    
    def get_kline_data(self, code: str, market: int, days: int = 300) -> Optional[pd.DataFrame]:
        """
        获取K线数据
        
        Args:
            code: 股票代码
            market: 市场代码，1=沪, 0=深
            days: 获取天数
            
        Returns:
            DataFrame 包含日期、开盘、收盘、最高、最低、成交量等字段
        """
        secid = f"{market}.{code}"
        
        url = settings.eastmoney_kline_url
        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f61",
            "klt": "101",  # 日K
            "fqt": "1",    # 前复权
            "end": "20500101",
            "lmt": str(days)
        }
        
        try:
            resp = self.session.get(url, params=params, headers=self.headers, timeout=self.timeout)
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
            
            return pd.DataFrame(records)
            
        except Exception as e:
            log.error(f"获取 {code} K线数据失败: {e}")
            return None
    
    def search_sector(self, sector_name: str) -> Optional[Dict]:
        """
        搜索板块
        
        Args:
            sector_name: 板块名称，如 "白酒"
            
        Returns:
            板块信息，包含 Code 和 Name
        """
        try:
            url = settings.eastmoney_suggest_url
            params = {
                "input": sector_name,
                "type": "14",
                "token": settings.eastmoney_token,
                "count": "5"
            }
            resp = self.session.get(url, params=params, headers=self.headers, timeout=10)
            data = resp.json()
            items = data.get("QuotationCodeTable", {}).get("Data", [])
            
            if items:
                return {
                    "code": items[0]["Code"],
                    "name": items[0]["Name"]
                }
        except Exception as e:
            log.error(f"搜索板块失败: {e}")
        return None
    
    def get_sector_stocks(self, sector_name: str, top_n: int = 10) -> List[Dict]:
        """
        获取板块成分股
        
        Args:
            sector_name: 板块名称，如 "电力设备"
            top_n: 返回前 N 只股票（按涨跌幅排序）
            
        Returns:
            股票列表
        """
        log.info(f"正在搜索板块: {sector_name} ...")
        
        # 搜索板块
        sector = self.search_sector(sector_name)
        if not sector:
            log.warning(f"未找到板块: {sector_name}")
            return []
        
        log.info(f"找到板块: {sector['name']} ({sector['code']})")
        
        # 获取板块成分股
        url = settings.eastmoney_clist_url
        params = {
            "pn": "1",
            "pz": str(top_n),
            "po": "1",
            "np": "1",
            "ut": settings.eastmoney_ut,
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": f"b:{sector['code']}+f:!50",
            "fields": "f12,f13,f14",
        }
        
        try:
            resp = self.session.get(url, params=params, headers=self.headers, timeout=10)
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
            log.error(f"获取板块成分股失败: {e}")
            return []


# 全局客户端实例
_client: Optional[EastMoneyClient] = None


def get_client() -> EastMoneyClient:
    """获取东方财富客户端实例（单例）"""
    global _client
    if _client is None:
        _client = EastMoneyClient()
    return _client


# 便捷函数，保持与原有接口兼容
def get_hot_stocks(top_n: int = 10) -> List[Dict]:
    """获取热门股票"""
    return get_client().get_hot_stocks(top_n)


def get_kline_data(code: str, market: int, days: int = 300) -> Optional[pd.DataFrame]:
    """获取K线数据"""
    return get_client().get_kline_data(code, market, days)


def get_sector_stocks(sector_name: str, top_n: int = 10) -> List[Dict]:
    """获取板块成分股"""
    return get_client().get_sector_stocks(sector_name, top_n)


def get_stock_name(code: str) -> Optional[str]:
    """获取股票名称"""
    return get_client().get_stock_name(code)
