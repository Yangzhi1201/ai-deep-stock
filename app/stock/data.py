"""
股票数据获取模块
提供统一的数据获取接口，支持多种数据源
"""
from typing import List, Dict, Optional
import pandas as pd

from app.stock import eastmoney
from app.config import get_settings

settings = get_settings()


def get_hot_stocks(top_n: int = 10) -> List[Dict]:
    """
    获取热门股票
    根据配置选择数据源，默认使用东方财富
    """
    if settings.data_source_priority == "minqmt" and settings.minqmt_enabled:
        # TODO: 实现 MiniQMT 版本的热门股票获取
        # 目前 MiniQMT 没有直接提供热门股票接口，暂时使用东方财富
        pass
    
    # 使用东方财富接口
    return eastmoney.get_hot_stocks(top_n)


def get_kline_data(code: str, market: int, days: int = 300) -> Optional[pd.DataFrame]:
    """
    获取K线数据
    根据配置选择数据源
    """
    if settings.data_source_priority == "minqmt" and settings.minqmt_enabled:
        # TODO: 实现 MiniQMT 版本的K线数据获取
        pass
    
    # 使用东方财富接口
    return eastmoney.get_kline_data(code, market, days)


def get_sector_stocks(sector_name: str, top_n: int = 10) -> List[Dict]:
    """
    获取板块成分股
    根据配置选择数据源
    """
    if settings.data_source_priority == "minqmt" and settings.minqmt_enabled:
        # TODO: 实现 MiniQMT 版本的板块数据获取
        pass
    
    # 使用东方财富接口
    return eastmoney.get_sector_stocks(sector_name, top_n)


def get_stock_name(code: str) -> Optional[str]:
    """
    获取股票名称
    """
    return eastmoney.get_stock_name(code)


# 为了保持向后兼容，保留这些别名
__all__ = [
    'get_hot_stocks',
    'get_kline_data',
    'get_sector_stocks',
    'get_stock_name',
]
