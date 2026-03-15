from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.stock.miniqmt import init_minqmt, close_minqmt
from app.utils.logging import log
from app.config import get_settings

# 创建FastAPI应用
app = FastAPI(
    title="股票推荐系统",
    description="基于技术指标的A股股票推荐系统",
    version="1.2.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取配置
settings = get_settings()

@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

# 启动事件
@app.on_event("startup")
def startup_event():
    log.info("应用启动...")
    # 初始化 MiniQMT
    log.info("初始化 MiniQMT...")
    init_minqmt()

# 关闭事件
@app.on_event("shutdown")
def shutdown_event():
    log.info("应用关闭...")
    # 关闭 MiniQMT
    log.info("关闭 MiniQMT...")
    close_minqmt()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
