"""
股票推荐 Agent 工作流
基于 LangGraph 实现的数据收集、分析、报告生成与发送的全流程自动化。
"""
from typing import TypedDict, List, Dict, Optional
from langgraph.graph import StateGraph, END
from app.stock.data import get_hot_stocks, get_sector_stocks
from app.stock.analyzer import analyze_stock, parse_stock_code
from app.stock.email import build_daily_recommendation_html, send_email
from app.utils.logging import log

# --- 状态定义 ---

class AgentState(TypedDict):
    """Agent 工作流的状态字典"""
    query_type: str  # 查询类型: "HOT"(热门), "SECTOR"(板块), "SPECIFIC"(指定)
    sector_name: Optional[str]  # 板块名称 (仅 SECTOR 模式)
    target_stocks: Optional[List[str]]  # 指定股票代码列表 (仅 SPECIFIC 模式)
    stocks: List[Dict]  # 收集到的股票列表
    analysis_results: List[Dict]  # 分析结果列表
    email_sent: bool  # 邮件发送状态

# --- 节点定义 ---

def data_collection_node(state: AgentState) -> Dict:
    """
    [节点] 数据收集
    根据 query_type 获取对应的股票列表。
    """
    query_type = state.get("query_type")
    log.info(f"▶ Agent 开始执行: 数据收集 (模式: {query_type})")
    
    stocks = []
    try:
        if query_type == "SPECIFIC" and state.get("target_stocks"):
            # 模式 1: 指定股票
            target_codes = state["target_stocks"]
            log.info(f"  处理指定股票: {target_codes}")
            for code_str in target_codes:
                # 解析代码 (支持 600410.SH 格式)
                stock_info = parse_stock_code(code_str)
                stocks.append(stock_info)
                
        elif query_type == "SECTOR" and state.get("sector_name"):
            # 模式 2: 板块选股
            sector = state["sector_name"]
            log.info(f"  搜索板块成分股: {sector}")
            stocks = get_sector_stocks(sector, top_n=10)
            
        else:
            # 模式 3: 热门股票 (默认)
            log.info("  获取市场热门股票 TOP10")
            stocks = get_hot_stocks(top_n=10)
            
    except Exception as e:
        log.error(f"  数据收集失败: {e}")
        stocks = []
        
    return {"stocks": stocks}


def analysis_node(state: AgentState) -> Dict:
    """
    [节点] 技术分析
    对收集到的股票进行各项技术指标计算和评分。
    """
    log.info("▶ Agent 开始执行: 技术分析")
    stocks = state["stocks"]
    results = []
    
    for stock in stocks:
        try:
            # 调用分析引擎
            res = analyze_stock(stock["code"], stock["market"], stock.get("name", stock["code"]))
            if res:
                results.append(res)
        except Exception as e:
            log.warning(f"  股票 {stock.get('code')} 分析异常: {e}")
            
    # 按综合评分降序排列
    results.sort(key=lambda x: x.get("综合评分", 0), reverse=True)
    
    # 结果筛选策略
    # 如果是指定股票，返回所有结果；否则只取前 5 名推荐
    if state.get("query_type") != "SPECIFIC":
        top_results = results[:5]
    else:
        top_results = results
    
    log.info(f"  分析完成，筛选出 {len(top_results)} 只优质股票")
    return {"analysis_results": top_results}


def email_processing_node(state: AgentState) -> Dict:
    """
    [节点] 邮件处理
    生成 HTML 报告并发送邮件。
    """
    log.info("▶ Agent 开始执行: 邮件处理")
    results = state["analysis_results"]
    
    if not results:
        log.warning("  无分析结果，跳过邮件发送")
        return {"email_sent": False}
    
    try:
        # 生成 HTML 报告
        html_content = build_daily_recommendation_html(results)
        
        # 发送邮件
        send_email(html_content)
        log.info("  邮件发送成功")
        return {"email_sent": True}
    except Exception as e:
        log.error(f"  邮件发送失败: {e}")
        return {"email_sent": False}

# --- 图构建 ---

workflow = StateGraph(AgentState)

# 注册节点
workflow.add_node("collect_data", data_collection_node)
workflow.add_node("analyze", analysis_node)
workflow.add_node("email_processing", email_processing_node)

# 定义流程
workflow.set_entry_point("collect_data")
workflow.add_edge("collect_data", "analyze")
workflow.add_edge("analyze", "email_processing")
workflow.add_edge("email_processing", END)

# 编译应用
app_workflow = workflow.compile()

# --- 快捷入口函数 ---

def run_hot_stock_workflow() -> Dict:
    """执行热门股票推荐流程"""
    return app_workflow.invoke({
        "query_type": "HOT",
        "sector_name": None,
        "target_stocks": [],
        "stocks": [],
        "analysis_results": [],
        "email_sent": False
    })

def run_sector_stock_workflow(sector_name: str) -> Dict:
    """执行板块股票推荐流程"""
    return app_workflow.invoke({
        "query_type": "SECTOR",
        "sector_name": sector_name,
        "target_stocks": [],
        "stocks": [],
        "analysis_results": [],
        "email_sent": False
    })

def run_specific_stock_workflow(stock_codes: List[str]) -> Dict:
    """执行指定股票分析流程"""
    return app_workflow.invoke({
        "query_type": "SPECIFIC",
        "sector_name": None,
        "target_stocks": stock_codes,
        "stocks": [],
        "analysis_results": [],
        "email_sent": False
    })
