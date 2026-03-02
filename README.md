# AI-Deep-Stock 🔍📈

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

基于技术指标的A股股票推荐系统，每日定时发送推荐报告。

> ⚠️ **免责声明**：本项目仅供学习研究，不构成投资建议。股市有风险，投资需谨慎。

## 功能特性

- **技术面分析**：MA均线金叉、MACD金叉、RSI超卖反弹、量价配合
- **定时任务**：每日自动执行分析并发送邮件
- **API接口**：健康检查、手动触发任务
- **邮件通知**：HTML邮件报告

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```env
# 邮箱配置（QQ邮箱）
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SENDER=your_email@qq.com
PASSWORD=your_authorization_code  # QQ邮箱授权码
RECEIVER=receiver1@example.com, receiver2@example.com  # 多个邮箱用逗号分隔

# 定时任务配置
SCHEDULER_HOUR=9
SCHEDULER_MINUTE=30

# 股票分析配置
HOT_STOCK_COUNT=10
RECOMMEND_COUNT=3
```

### 3. 运行

**方式一：一键运行（推荐）**

```bash
# macOS/Linux
./run.sh

# Windows
run.bat
```

**方式二：启动服务**

```bash
uvicorn app.main:app --reload
```

服务启动后访问：
- 健康检查：`GET http://127.0.0.1:8000/health`
- 手动触发：`POST http://127.0.0.1:8000/trigger`

## 项目结构

```
├── app/
│   ├── stock/          # 股票分析模块
│   │   ├── data.py     # 数据获取
│   │   ├── indicators.py # 技术指标
│   │   ├── analyzer.py # 分析引擎
│   │   ├── email.py    # 邮件发送
│   │   └── task.py     # 定时任务
│   ├── utils/          # 工具类
│   └── main.py         # FastAPI入口
├── .env                # 环境变量
├── requirements.txt    # 依赖
├── run.sh              # macOS/Linux运行脚本
└── run.bat             # Windows运行脚本
```

## 评分逻辑

| 指标 | 权重 |
|------|------|
| MA均线系统 | 40分 |
| MACD指标 | 45分 |
| RSI指标 | 25分 |
| 量价配合 | 15分 |

## 许可证

MIT License
