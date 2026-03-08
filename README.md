# AI-Deep-Stock 🔍📈

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

基于 **LangGraph** 的智能 A 股股票推荐系统，实现了从数据获取、技术分析、报告生成到邮件发送的全流程自动化。

> ⚠️ **免责声明**：本项目仅供学习研究，不构成投资建议。股市有风险，投资需谨慎。

## ✨ 功能特性

- **🤖 智能 Agent 工作流**：基于 LangGraph 构建的自动化流水线，支持多模式数据采集与分析。
- **📊 多维度推荐**：
  - **🔥 热门股票**：自动抓取并分析市场热度最高的 TOP10 股票。
  - **🏢 板块/概念**：支持按板块（如“人工智能”、“白酒”）筛选涨幅靠前的成分股进行分析。
  - **🎯 指定股票**：深度分析用户关注的特定股票（支持 SH/SZ 市场代码）。
- **📈 技术面分析**：
  - **MA 均线系统**：金叉/死叉识别，多头排列判断。
  - **MACD 指标**：趋势强弱分析，背离检测。
  - **RSI 指标**：超买超卖状态识别。
  - **量价关系**：成交量与价格走势配合分析。
- **⏰ 自动化任务**：每日定时（默认 9:30）自动执行热门股及重点板块分析，并发送邮件报告。
- **📧 邮件通知**：生成包含详细评分、推荐理由和数据概览的 HTML 邮件报告。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并编辑配置：

```env
# 邮箱配置（推荐使用 QQ 邮箱 SMTP）
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SENDER=your_email@qq.com
PASSWORD=your_authorization_code  # QQ邮箱授权码
RECEIVER=receiver1@example.com,receiver2@example.com  # 多个接收者用逗号分隔

# 定时任务配置
SCHEDULER_HOUR=9
SCHEDULER_MINUTE=30
```

### 3. 运行服务

启动 FastAPI 服务：

```bash
# 开发模式（支持热重载）
uvicorn app.main:app --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

服务启动后访问：
- **API 文档 (Swagger UI)**: `http://127.0.0.1:8000/docs`
- **健康检查**: `http://127.0.0.1:8000/health`

## 🔌 API 接口说明

所有推荐接口均会触发 Agent 工作流，分析完成后自动发送邮件。

### 1. 热门股票推荐

获取当前市场人气最高的股票进行分析。

- **URL**: `/api/recommend/hot`
- **Method**: `POST`

**示例请求**：
```bash
curl -X POST "http://localhost:8000/api/recommend/hot"
```

### 2. 板块/概念推荐

指定板块名称，获取该板块涨幅靠前的成分股进行分析。

- **URL**: `/api/recommend/sector`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "sector_name": "白酒"
  }
  ```

**示例请求**：
```bash
curl -X POST "http://localhost:8000/api/recommend/sector" \
     -H "Content-Type: application/json" \
     -d '{"sector_name": "电力设备"}'
```

### 3. 指定股票分析

深度分析指定的股票代码。

- **URL**: `/api/recommend/specific`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "stock_codes": ["600519", "000858", "600036.SH"]
  }
  ```

**示例请求**：
```bash
curl -X POST "http://localhost:8000/api/recommend/specific" \
     -H "Content-Type: application/json" \
     -d '{"stock_codes": ["600519", "000858"]}'
```

## 🧪 测试

项目包含完整的 API 集成测试。

```bash
# 安装测试依赖
pip install pytest httpx

# 运行测试
PYTHONPATH=. pytest tests/test_api.py
```

## 📂 项目结构

```
├── app/
│   ├── agent/          # Agent 智能体模块
│   │   └── workflow.py     # LangGraph 工作流定义 (核心逻辑)
│   ├── stock/          # 股票分析核心模块
│   │   ├── data.py         # 数据获取 (东方财富接口)
│   │   ├── indicators.py   # 技术指标计算
│   │   ├── analyzer.py     # 分析引擎 & 评分系统
│   │   ├── email.py        # 邮件生成与发送
│   │   └── task.py         # 定时任务调度
│   ├── api/            # API 接口层
│   │   ├── recommendation.py # 推荐业务接口
│   │   └── system.py         # 系统管理接口
│   ├── utils/          # 工具类
│   ├── config.py       # 配置管理
│   └── main.py         # FastAPI 应用入口
├── tests/              # 测试用例
│   └── test_api.py     # API 集成测试
├── .env                # 环境变量配置
├── requirements.txt    # 项目依赖
└── README.md           # 项目文档
```

## 📝 评分逻辑

系统根据以下维度对股票进行综合打分（满分 100 分）：

| 指标 | 权重 | 说明 |
|------|------|------|
| **MA 均线** | 40% | 均线多头排列、金叉信号 |
| **MACD** | 30% | 趋势强弱、金叉/死叉 |
| **RSI** | 20% | 超买超卖状态 |
| **量价配合** | 10% | 成交量与价格趋势的验证 |

## 📄 许可证

[MIT License](LICENSE)
