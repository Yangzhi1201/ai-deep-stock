@echo off
chcp 65001 >nul
REM Windows 股票推荐任务运行脚本
REM 运行一次定时任务逻辑

echo ==========================================
echo 启动 AI-Deep-Stock 股票推荐分析任务
echo ==========================================
echo.

REM 获取脚本所在目录
cd /d "%~dp0"

REM 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
)

echo 开始执行分析...
echo.

REM 运行任务
python -c "import sys; sys.path.insert(0, '.'); from app.stock.task import stock_recommendation_task; stock_recommendation_task()"

REM 捕获退出码
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ==========================================

if %EXIT_CODE% == 0 (
    echo 任务执行成功！
) else (
    echo 任务执行失败，退出码: %EXIT_CODE%
)

echo ==========================================
echo.
pause
exit /b %EXIT_CODE%
