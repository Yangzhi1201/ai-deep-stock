import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_sector_recommend():
    """测试板块推荐接口"""
    payload = {"sector_name": "白酒"}
    response = client.post("/api/recommend/sector", json=payload)
    
    # 验证响应状态码
    assert response.status_code == 200
    
    # 验证响应数据结构
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "recommendations" in data["data"]
    assert len(data["data"]["recommendations"]) > 0
    assert data["data"]["sector"] == "白酒"
    
    # 验证单个推荐项的字段
    first_stock = data["data"]["recommendations"][0]
    assert "code" in first_stock
    assert "name" in first_stock
    assert "score" in first_stock

def test_specific_stock_analysis():
    """测试指定股票分析接口"""
    # 使用茅台作为测试对象
    payload = {"stock_codes": ["600519"]}
    response = client.post("/api/recommend/specific", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["recommendations"]) == 1
    assert data["data"]["recommendations"][0]["code"] == "600519"

# 注意：热门推荐接口可能会耗时较长或依赖外部状态，
# 在单元测试中通常会 Mock 掉外部依赖，这里仅作为集成测试示例
# def test_hot_recommend():
#     response = client.post("/api/recommend/hot")
#     assert response.status_code == 200
