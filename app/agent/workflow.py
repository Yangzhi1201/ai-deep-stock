"""
股票推荐 Agent 工作流
基于 LangGraph 实现的数据收集、分析、报告生成与发送的全流程自动化。
现在支持基于 LLM 的智能决策。
"""
from typing import TypedDict, List, Dict, Optional, Annotated, Any
import operator
from langgraph.graph import StateGraph, END
from app.utils.logging import log
from app.agent.llm import llm_client, TOOLS_DEFINITIONS

# --- 状态定义 ---

class AgentState(TypedDict):
    """Agent 工作流的状态字典"""
    messages: Annotated[List[Dict], operator.add]  # 聊天记录
    query: str       # 用户查询

# --- 节点定义 ---

def llm_node(state: AgentState) -> Dict:
    """
    [节点] LLM 决策
    """
    messages = state["messages"]
    
    # 如果消息列表为空，初始化系统提示
    if not messages:
        system_prompt = {
            "role": "system",
            "content": """你是一个专业的A股市场分析助手。你的目标是帮助用户筛选和分析股票。
            
你可以使用以下工具：
1. get_hot_stocks: 获取市场热门股票
2. get_sector_stocks: 获取板块成分股
3. analyze_stock: 分析单只股票的技术指标
4. recommend_stocks: 智能推荐买入评级的股票

工作流程：
- 当用户询问推荐股票时，优先使用 recommend_stocks 工具。
- 当用户询问特定板块时，使用 get_sector_stocks。
- 当用户询问具体股票时，使用 analyze_stock。
- 分析完成后，如果用户需要发送邮件报告，请总结分析结果并确认。
"""
        }
        # 首次调用，构造初始上下文并调用 LLM
        # 首次调用，构造初始上下文并调用 LLM
        initial_messages = [system_prompt, {"role": "user", "content": state["query"]}]
        response_message = llm_client.chat(initial_messages, tools=TOOLS_DEFINITIONS)
        
        # 返回 system, user, assistant 三条消息给 graph 初始化
        return {"messages": [system_prompt, {"role": "user", "content": state["query"]}, response_message]}

    # 后续调用：直接使用当前 messages 作为上下文
    current_messages = list(messages)
    
    # 调用 LLM
    response_message = llm_client.chat(current_messages, tools=TOOLS_DEFINITIONS)
    
    return {"messages": [response_message]}

def tool_node(state: AgentState) -> Dict:
    """
    [节点] 工具执行
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.tool_calls:
        tool_results = llm_client.process_tool_calls(last_message.tool_calls)
        return {"messages": tool_results}
        
    return {"messages": []}

# --- 路由逻辑 ---

def should_continue(state: AgentState) -> str:
    """
    决定下一步：继续工具调用还是结束
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.tool_calls:
        return "tools"
    return END

# --- 图构建 ---

def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("agent", llm_node)
    workflow.add_node("tools", tool_node)
    
    # 设置入口
    workflow.set_entry_point("agent")
    
    # 添加边
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

def run_agent(query: str):
    """
    运行 Agent 处理单个查询（兼容性函数）
    """
    app = create_agent_graph()
    result = app.invoke({"query": query, "messages": []})
    
    # 打印最终回复
    last_msg = result["messages"][-1]
    log.info(f"🤖 Agent 回复:\n{last_msg.content}")
    return result
