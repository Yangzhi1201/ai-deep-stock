"""
股票对比API接口
支持输入多只股票代码，进行综合对比分析并发送邮件报告
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from app.stock.analyzer import analyze_stocks_batch, parse_stock_code
from app.utils.logging import log

router = APIRouter(prefix="/api/stock-compare", tags=["股票对比"])


class StockCode(BaseModel):
    """单只股票代码信息"""
    code: str = Field(..., description="股票代码，如：600410")
    market: int = Field(..., description="市场类型：1=沪市, 0=深市")
    name: Optional[str] = Field(None, description="股票名称（可选）")


class StockCompareRequest(BaseModel):
    """股票对比请求体"""
    stocks: List[StockCode] = Field(..., description="要对比的股票列表", min_items=2, max_items=10)


class StockCompareResponse(BaseModel):
    """股票对比响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")


@router.post("/", response_model=StockCompareResponse)
async def compare_stocks_post(request: StockCompareRequest, background_tasks: BackgroundTasks):
    """
    对比多只股票并发送邮件报告
    
    请求成功后立即返回，邮件在后台发送
    
    示例请求:
    ```json
    {
        "stocks": [
            {"code": "600410", "market": 1},
            {"code": "002261", "market": 0},
            {"code": "300750", "market": 0}
        ]
    }
    ```
    """
    log.info(f"股票对比请求: 对比 {len(request.stocks)} 只股票")
    
    # 转换请求数据格式
    stocks = [{"code": s.code, "market": s.market, "name": s.name or ""} for s in request.stocks]
    
    # 后台执行分析和发送邮件
    background_tasks.add_task(_compare_and_send_task, stocks)
    
    return StockCompareResponse(
        success=True,
        message=f"已接收对比请求，共 {len(stocks)} 只股票，对比报告将发送至邮箱"
    )


@router.get("/", response_model=StockCompareResponse)
async def compare_stocks_get(
    codes: str = Query(..., description="要对比的股票代码，用逗号分隔。支持格式：600410,002261.SZ,300750.sh"),
    background_tasks: BackgroundTasks = None
):
    """
    GET方式对比多只股票并发送邮件报告
    
    请求成功后立即返回，邮件在后台发送
    
    示例:
    - /api/stock-compare/?codes=600410,002261,300750
    - /api/stock-compare/?codes=600410.SH,002261.SZ
    """
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    
    if len(code_list) < 2:
        raise HTTPException(status_code=400, detail="请至少提供2只股票进行对比")
    
    if len(code_list) > 10:
        raise HTTPException(status_code=400, detail="最多支持10只股票同时对比")
    
    log.info(f"股票对比请求: GET方式对比 {len(code_list)} 只股票")
    
    # 解析股票代码
    stocks = []
    for code_str in code_list:
        parsed = parse_stock_code(code_str)
        stocks.append(parsed)
    
    # 后台执行分析和发送邮件
    background_tasks.add_task(_compare_and_send_task, stocks)
    
    return StockCompareResponse(
        success=True,
        message=f"已接收对比请求，共 {len(stocks)} 只股票，对比报告将发送至邮箱"
    )


def _compare_and_send_task(stocks: List[Dict]):
    """
    后台任务：对比股票并发送邮件
    
    Args:
        stocks: 股票列表
    """
    try:
        # 执行批量分析，按评分排序
        results, summary = analyze_stocks_batch(stocks, sort_by="综合评分", sort_order="desc")
        
        if results:
            # 发送邮件
            from app.stock.email import build_email_html, send_email
            html = build_email_html(results)
            send_email(html)
            log.info(f"股票对比完成并发送邮件，共 {len(results)} 只股票")
        else:
            log.warning("没有成功分析任何股票，跳过邮件发送")
            
    except Exception as e:
        log.error(f"后台对比任务失败: {e}", exc_info=True)
