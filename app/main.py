from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.stock.task import stock_recommendation_task
from app.utils.logging import log
from app.config import get_settings
from app.api import system_router, recommendation_router

# 创建FastAPI应用
app = FastAPI(
    title="股票推荐系统",
    description="基于技术指标的A股股票推荐系统，支持每日股票推荐和股票对比功能",
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

# 注册API路由
app.include_router(system_router)
app.include_router(recommendation_router)

# 创建定时任务调度器
scheduler = BackgroundScheduler()

# 从配置读取定时任务时间（默认9:30）
settings = get_settings()

# 每天执行股票推荐任务（A股开盘时间）
scheduler.add_job(
    stock_recommendation_task,
    trigger=CronTrigger(hour=settings.scheduler_hour, minute=settings.scheduler_minute),
    id="stock_recommendation",
    name="每日股票推荐",
    replace_existing=True
)

# 启动定时任务调度器
@app.on_event("startup")
def startup_event():
    log.info("启动定时任务调度器...")
    scheduler.start()
    log.info("定时任务调度器已启动")

# 关闭定时任务调度器
@app.on_event("shutdown")
def shutdown_event():
    log.info("关闭定时任务调度器...")
    scheduler.shutdown()
    log.info("定时任务调度器已关闭")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
