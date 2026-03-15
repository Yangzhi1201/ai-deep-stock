"""
LLM 工具定义模块
封装股票查询、分析等功能为 OpenAI 兼容的 Tools
"""
from typing import List, Dict, Any
from app.stock.data import get_hot_stocks, get_sector_stocks
from app.stock.analyzer import analyze_stock, parse_stock_code, run_hot_stocks_analysis

def tool_get_hot_stocks(top_n: int = 10) -> List[Dict]:
    """
    获取市场热门股票列表
    
    Args:
        top_n: 获取数量，默认 10
    """
    return get_hot_stocks(top_n)

def tool_get_sector_stocks(sector_name: str, top_n: int = 10) -> List[Dict]:
    """
    获取指定板块（概念/行业）的成分股
    
    Args:
        sector_name: 板块名称，如 "白酒", "AI", "低空经济"
        top_n: 获取数量，默认 10
    """
    return get_sector_stocks(sector_name, top_n)

def tool_analyze_stock(code: str) -> Dict:
    """
    分析单只股票的技术指标
    
    Args:
        code: 股票代码，支持 "600519" 或 "600519.SH" 格式
    """
    # parse_stock_code 返回 {"code": "...", "market": 1, "name": ""}
    stock_info = parse_stock_code(code)
    
    # 尝试补充名称，如果无法补充则使用 code
    name = stock_info.get("name") or stock_info["code"]
    
    # 调用 analyze_stock(code, market, name)
    result = analyze_stock(stock_info["code"], stock_info["market"], name)
    
    if not result:
        return {"error": f"无法获取股票 {code} 的数据或数据不足"}
    return result

def tool_recommend_stocks(recommend_n: int = 3) -> List[Dict]:
    """
    智能推荐股票（基于热门股筛选高评分标的）
    
    Args:
        recommend_n: 推荐数量，默认 3
    """
    # 调用 run_hot_stocks_analysis(top_n=20, recommend_n=recommend_n)
    # top_n 是初始热门池大小，recommend_n 是最终输出数量
    return run_hot_stocks_analysis(top_n=20, recommend_n=recommend_n)

# 工具定义列表 (OpenAI 格式)
TOOLS_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_hot_stocks",
            "description": "获取当前市场热门关注的股票列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "获取的股票数量",
                        "default": 10
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_sector_stocks",
            "description": "根据板块名称搜索并获取该板块的成分股",
            "parameters": {
                "type": "object",
                "properties": {
                    "sector_name": {
                        "type": "string",
                        "description": "板块名称，例如 '新能源', '半导体', '银行'"
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "获取的股票数量",
                        "default": 10
                    }
                },
                "required": ["sector_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_stock",
            "description": "分析指定股票的技术指标（MACD, RSI, KDJ等）并给出评分",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "股票代码，如 '600519' 或 '000001'"
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_stocks",
            "description": "智能推荐买入评级的热门股票",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommend_n": {
                        "type": "integer",
                        "description": "推荐的股票数量",
                        "default": 3
                    }
                }
            }
        }
    }
]

# 工具映射表
TOOLS_MAP = {
    "get_hot_stocks": tool_get_hot_stocks,
    "get_sector_stocks": tool_get_sector_stocks,
    "analyze_stock": tool_analyze_stock,
    "recommend_stocks": tool_recommend_stocks
}
