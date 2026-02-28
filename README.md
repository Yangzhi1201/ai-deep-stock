# 股票推荐系统

基于技术指标的A股股票推荐系统，每日定时发送推荐报告。

## 功能特性

- **技术面分析**：基于MA均线金叉、MACD金叉、RSI超卖反弹、量价配合等指标
- **定时任务**：每日9:30自动执行股票推荐分析并发送邮件
- **API接口**：提供健康检查和手动触发任务的接口
- **邮件通知**：生成美观的HTML邮件报告并发送
- **配置管理**：使用环境变量管理敏感信息

## 技术栈

- **后端框架**：FastAPI 0.104.1
- **Web服务器**：Uvicorn 0.24.0.post1
- **数据处理**：pandas 2.1.4, numpy 1.26.3
- **HTTP请求**：requests 2.31.0
- **配置管理**：python-dotenv 1.0.0
- **定时任务**：APScheduler 3.10.4

## 项目结构

```
QoderWork/
├── app/
│   ├── stock/             # 股票相关功能
│   │   ├── data.py        # 股票数据获取
│   │   ├── indicators.py  # 技术指标计算
│   │   ├── analyzer.py    # 股票分析
│   │   ├── email.py       # 邮件生成和发送
│   │   └── task.py        # 定时任务
│   ├── utils/             # 工具类
│   │   ├── config.py      # 配置管理
│   │   └── logging.py     # 日志配置
│   └── main.py            # FastAPI应用主入口
├── .env                   # 环境变量
├── requirements.txt       # 依赖管理
└── run_stock.sh           # 运行脚本
```

## 安装步骤

1. **克隆项目**
   ```bash
   git clone <项目地址>
   cd QoderWork
   ```

2. **创建虚拟环境**（可选）
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # 或
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

## 配置说明

1. **编辑环境变量文件**：`.env`
   ```env
   # 邮箱配置
   SMTP_SERVER=smtp.qq.com
   SMTP_PORT=465
   SENDER=your_qq_email@qq.com
   PASSWORD=your_qq_email_authorization_code
   RECEIVER=receiver_email@example.com

   # 股票分析配置
   HOT_STOCK_COUNT=10
   RECOMMEND_COUNT=3
   ```

   **注意**：`PASSWORD` 不是QQ邮箱的登录密码，而是QQ邮箱的授权码。获取方法：QQ邮箱 → 设置 → 账户 → POP3/SMTP服务 → 开启 → 获取授权码。

## 使用方法

### 启动应用

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API接口

- **健康检查**：GET http://127.0.0.1:8000/health
  ```json
  {
    "status": "healthy",
    "message": "股票推荐系统运行正常"
  }
  ```

- **手动触发任务**：POST http://127.0.0.1:8000/trigger
  ```bash
  curl -X POST http://127.0.0.1:8000/trigger
  ```
  ```json
  {
    "status": "success",
    "message": "股票推荐任务已触发"
  }
  ```

### 定时任务

系统会在每天9:30（A股开盘时间）自动执行股票推荐分析，并将结果发送到配置的邮箱。

## 分析逻辑

1. **获取热门股票**：从东方财富人气榜获取前N只热门股票
2. **获取K线数据**：获取每只股票的历史K线数据
3. **计算技术指标**：计算MA、MACD、RSI等技术指标
4. **评分系统**：基于技术指标对股票进行评分（满分100）
   - MA均线系统：最高40分
   - MACD指标：最高45分
   - RSI指标：最高25分（超买扣分）
   - 量价配合：最高15分
5. **生成推荐**：选择评分最高的前3只股票
6. **发送邮件**：生成HTML邮件报告并发送

## 注意事项

1. **数据来源**：本系统使用东方财富API获取数据，可能会受到API限制
2. **风险提示**：本推荐基于技术指标量化分析，仅供参考，不构成投资建议。股市有风险，投资需谨慎。
3. **邮箱配置**：请确保正确配置QQ邮箱授权码，否则邮件发送会失败
4. **定时任务**：系统会自动跳过周末和非交易日的分析

## 运行脚本

项目提供了运行脚本 `run_stock.sh`，可以直接执行股票推荐分析：

```bash
chmod +x run_stock.sh
./run_stock.sh
```

## 许可证

本项目采用 MIT 许可证。
