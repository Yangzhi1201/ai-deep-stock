from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.agent.workflow import run_hot_stock_workflow, run_sector_stock_workflow, run_specific_stock_workflow

router = APIRouter(
    prefix="/api/recommend",
    tags=["Recommendation"],
    responses={404: {"description": "Not found"}},
)

class RecommendationResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class SectorRequest(BaseModel):
    sector_name: str

class SpecificStockRequest(BaseModel):
    stock_codes: List[str]

def _format_stock_result(res: Dict) -> Dict:
    """格式化单只股票的分析结果"""
    return {
        "code": res.get("代码"),
        "name": res.get("名称"),
        "score": res.get("综合评分"),
        "recommendation": res.get("recommendation"),
        "latest_price": res.get("最新价"),
        "change_pct": res.get("涨跌幅")
    }

@router.post("/hot", response_model=RecommendationResponse)
async def hot_recommend():
    """
    热门股票推荐
    
    触发 Agent 工作流：
    1. 获取当前市场热门股票
    2. 执行技术指标分析
    3. 生成并发送邮件报告
    """
    try:
        result = run_hot_stock_workflow()
        analysis_results = result.get("analysis_results", [])
        email_sent = result.get("email_sent", False)
        
        simple_results = [_format_stock_result(res) for res in analysis_results]
            
        return {
            "success": True,
            "message": f"分析完成，推荐 {len(simple_results)} 只股票。邮件发送状态: {'成功' if email_sent else '失败/未发送'}",
            "data": {
                "count": len(simple_results),
                "recommendations": simple_results,
                "email_sent": email_sent
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sector", response_model=RecommendationResponse)
async def sector_recommend(request: SectorRequest):
    """
    板块/概念股票推荐
    
    Args:
        sector_name: 板块名称（如"电力设备"、"AI"）
        
    触发 Agent 工作流：
    1. 搜索板块成分股
    2. 筛选涨幅靠前的股票
    3. 执行技术分析
    4. 生成并发送邮件报告
    """
    if not request.sector_name or not request.sector_name.strip():
        raise HTTPException(status_code=400, detail="板块名称不能为空")
        
    try:
        result = run_sector_stock_workflow(request.sector_name)
        analysis_results = result.get("analysis_results", [])
        email_sent = result.get("email_sent", False)
        
        simple_results = [_format_stock_result(res) for res in analysis_results]
            
        return {
            "success": True,
            "message": f"板块[{request.sector_name}]分析完成，推荐 {len(simple_results)} 只股票。邮件发送状态: {'成功' if email_sent else '失败/未发送'}",
            "data": {
                "count": len(simple_results),
                "recommendations": simple_results,
                "email_sent": email_sent,
                "sector": request.sector_name
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/specific", response_model=RecommendationResponse)
async def analyze_specific(request: SpecificStockRequest):
    """
    指定股票分析
    
    Args:
        stock_codes: 股票代码列表
        
    触发 Agent 工作流：
    1. 获取指定股票数据
    2. 执行深度技术分析
    3. 生成并发送邮件报告
    """
    if not request.stock_codes:
        raise HTTPException(status_code=400, detail="股票代码列表不能为空")
        
    try:
        result = run_specific_stock_workflow(request.stock_codes)
        analysis_results = result.get("analysis_results", [])
        email_sent = result.get("email_sent", False)
        
        simple_results = [_format_stock_result(res) for res in analysis_results]
            
        return {
            "success": True,
            "message": f"分析完成，共分析 {len(simple_results)} 只股票。邮件发送状态: {'成功' if email_sent else '失败/未发送'}",
            "data": {
                "count": len(simple_results),
                "recommendations": simple_results,
                "email_sent": email_sent,
                "stock_codes": request.stock_codes
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
