#!/bin/bash
# macOS 股票推荐任务运行脚本
# 运行一次定时任务逻辑

echo "=========================================="
echo "启动 AI-Deep-Stock 股票推荐分析任务"
echo "=========================================="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "激活虚拟环境..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 运行任务
echo "开始执行分析..."
python3 -c "
import sys
sys.path.insert(0, '.')
from app.stock.task import stock_recommendation_task
stock_recommendation_task()
"

# 捕获退出码
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ 任务执行成功！"
else
    echo ""
    echo "❌ 任务执行失败，退出码: $EXIT_CODE"
fi

echo "=========================================="
read -p "按回车键退出..."
exit $EXIT_CODE
