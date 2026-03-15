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
# LLM 配置 (OpenAI 兼容)
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 东方财富 API 配置 (通常使用默认值即可)
```

### 3. 运行助手

启动交互式 CLI：

```bash
python app/main.py
```

启动后，您可以直接与 AI 助手对话，例如：
- "推荐几只热门股票"
- "分析贵州茅台"
- "看看白酒板块的情况"

## ✨ 功能特性

- **🤖 智能对话**：通过自然语言与 AI 助手交互，无需记忆复杂指令。
- **📊 多维度分析**：
  - **🔥 热门股票**：自动获取市场热门股票并进行技术面分析。
  - **🏢 板块扫描**：按板块筛选并分析潜力股。
  - **📈 个股诊断**：提供详细的技术指标分析（MACD, KDJ, RSI 等）。
- **🧠 智能决策**：基于 LangGraph 的 Agent 工作流，自动调用工具获取数据并生成专业报告。

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

## 📂 项目结构

```
├── app/
│   ├── agent/          # Agent 智能体模块
│   │   ├── workflow.py     # LangGraph 工作流定义 (核心逻辑)
│   │   ├── llm.py          # LLM 交互逻辑
│   │   └── tools.py        # Agent 工具定义
│   ├── stock/          # 股票分析核心模块
│   │   ├── data.py         # 数据获取 (东方财富接口)
│   │   ├── indicators.py   # 技术指标计算
│   │   └── analyzer.py     # 分析引擎 & 评分系统
│   ├── utils/          # 工具类
│   ├── config.py       # 配置管理
│   └── main.py         # CLI 应用入口
├── run.py              # 项目启动脚本
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
