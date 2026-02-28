from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.stock.task import stock_recommendation_task
from app.utils.logging import log

# 创建FastAPI应用
app = FastAPI(
    title="股票推荐系统",
    description="基于技术指标的A股股票推荐系统，每日定时发送推荐报告",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建定时任务调度器
scheduler = BackgroundScheduler()

# 每天9:30执行股票推荐任务（A股开盘时间）
scheduler.add_job(
    stock_recommendation_task,
    trigger=CronTrigger(hour=9, minute=30),
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

# 健康检查接口
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "股票推荐系统运行正常"}

# 手动触发股票推荐任务接口
@app.post("/trigger")
def trigger_recommendation():
    log.info("手动触发股票推荐任务...")
    stock_recommendation_task()
    return {"status": "success", "message": "股票推荐任务已触发"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)